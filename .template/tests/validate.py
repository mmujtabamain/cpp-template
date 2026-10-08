#!/usr/bin/env python3
"""Cross-platform scaffold and real-vcpkg integration checks in disposable copies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
WINDOWS = os.name == 'nt'


# Capture subprocess output so failures include the command and its diagnostics.
def command(args, cwd, *, input='', env=None, success=True):
    result = subprocess.run([str(x) for x in args], cwd=cwd, input=input,
                            text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    if success and result.returncode:
        raise AssertionError(f"Command failed: {args}\n{result.stdout}")
    if not success and not result.returncode:
        raise AssertionError(f"Command unexpectedly succeeded: {args}\n{result.stdout}")
    return result


# Exercise disposable repository copies, never the developer's generated project.
def fresh(parent, name):
    project = parent / name
    project.mkdir()
    shutil.copytree(ROOT / '.template', project / '.template',
                    ignore=shutil.ignore_patterns('.scaffold-tmp', '__pycache__'))
    for file in ('scaffold.sh', 'scaffold.bat', 'README.md', '.gitignore'):
        shutil.copy2(ROOT / file, project / file)
    return project


# Call the shared implementation directly to test validation and confirmation behavior.
def scaffold(project, name='Vector Math', kind='library', *, force=False,
             answer='', success=True):
    args = ['cmake', f'-DPROJECT_DISPLAY_NAME={name}', f'-DPROJECT_TYPE={kind}']
    if force:
        args.append('-DSCAFFOLD_FORCE=ON')
    return command(args + ['-P', project / '.template/scripts/scaffold.cmake'],
                   project, input=answer, success=success)


# Also exercise the native entry points on the host platform.
def launcher(project, name, *args, input=''):
    if WINDOWS:
        return command(['cmd', '/c', str(project / (name + '.bat')), *args],
                       project, input=input)
    return command([project / (name + '.sh'), *args], project, input=input)


# Detect any file-content changes when a scaffold must cancel or reject input.
def snapshot(project):
    return {str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in project.rglob('*') if p.is_file()}


# Fast checks require CMake and Python but do not download dependencies.
class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cpp-template-')
        self.parent = Path(self.temp.name)
        self.project = fresh(self.parent, 'project with spaces')

    def tearDown(self):
        self.temp.cleanup()

    def test_names_and_types(self):
        names = [('SimpleProject', 'SimpleProject', 'simple_project', 'simple-project'),
                 ('Vector Math', 'VectorMath', 'vector_math', 'vector-math'),
                 ('vector-math', 'VectorMath', 'vector_math', 'vector-math')]
        for kind in ('exec', 'library'):
            for index, (display, target, namespace, manifest) in enumerate(names):
                with self.subTest(kind=kind, name=display):
                    p = fresh(self.parent, f'{kind}-{index}')
                    scaffold(p, display, kind)
                    self.assertIn(f'project({target} VERSION', (p / 'CMakeLists.txt').read_text())
                    self.assertEqual(json.loads((p / 'vcpkg.json').read_text())['name'], manifest)
                    self.assertEqual(json.loads((p / 'vcpkg.json').read_text())['dependencies'], ['fmt'])
                    self.assertIn(display, (p / 'README.md').read_text())
                    command(['cmake', '--list-presets'], p)
                    workflow = (p / '.github/workflows/validate.yml').read_text()
                    self.assertNotIn('.template/', workflow)
                    self.assertNotIn('@PROJECT_TYPE@', workflow)
                    self.assertIn(f"'{kind}' == 'library'", workflow)
                    self.assertFalse((p / '.cpp-template-scaffolded').exists())
                    self.assertFalse((p / '.template/.scaffold-tmp').exists())
                    if kind == 'library':
                        header = p / f'include/{namespace}/{namespace}.hpp'
                        self.assertIn(f'namespace {namespace}', header.read_text())
                        self.assertTrue((p / f'src/{namespace}.cpp').is_file())
                        config = (p / f'cmake/{target}Config.cmake.in').read_text()
                        self.assertIn('@PACKAGE_INIT@', config)
                        self.assertIn('find_dependency(fmt CONFIG REQUIRED)', config)
                        self.assertIn(f'{target}::{target}', (p / 'README.md').read_text())
                    else:
                        self.assertTrue((p / 'assets/.gitkeep').is_file())
                        self.assertIn(display, (p / 'src/main.cpp').read_text())

    def test_native_launcher(self):
        launcher(self.project, 'scaffold', 'Vector Math', 'library')
        self.assertTrue((self.project / 'include/vector_math/vector_math.hpp').exists())

    def test_interactive_launcher(self):
        launcher(self.project, 'scaffold', input='SimpleProject\nexec\n')
        self.assertIn('SimpleProject', (self.project / 'CMakeLists.txt').read_text())

    def test_declined_and_confirmed_replacement(self):
        scaffold(self.project)
        (self.project / 'src/valuable.cpp').write_text('user modifications')
        before = snapshot(self.project)
        for answer in ('', 'n\n'):
            result = scaffold(self.project, 'Replacement', 'exec', answer=answer)
            self.assertIn('cancelled', result.stdout)
            self.assertEqual(before, snapshot(self.project))
        for path in ('.git/keep', 'external/vcpkg/keep', '.github/keep', 'notes.txt'):
            p = self.project / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('preserve')
        (self.project / 'build').mkdir()
        (self.project / 'vcpkg_installed').mkdir()
        result = scaffold(self.project, 'Replacement', 'exec', answer='y\n')
        self.assertIn('permanently erase', result.stdout)
        for path in ('include', 'tests', 'examples', 'cmake', 'src/valuable.cpp', 'build', 'vcpkg_installed'):
            self.assertFalse((self.project / path).exists(), path)
        for path in ('.git/keep', 'external/vcpkg/keep', '.github/keep', 'notes.txt', '.template', 'scaffold.sh', 'scaffold.bat'):
            self.assertTrue((self.project / path).exists(), path)
        self.assertIn('Replacement', (self.project / 'src/main.cpp').read_text())

    def test_invalid_input_preserves_existing_data(self):
        scaffold(self.project)
        before = snapshot(self.project)
        for name in ('', '123', '../escape', 'bad;name', 'bad"name', 'class', 'Run'):
            scaffold(self.project, name, force=True, success=False)
            self.assertEqual(before, snapshot(self.project))
        scaffold(self.project, kind='invalid', force=True, success=False)
        self.assertEqual(before, snapshot(self.project))

    def test_partial_output_and_stale_stage_recovery(self):
        (self.project / 'src').mkdir()
        (self.project / 'src/partial.cpp').write_text('partial')
        stage = self.project / '.template/.scaffold-tmp'
        stage.mkdir()
        (stage / 'stale').write_text('stale')
        scaffold(self.project, force=True)
        self.assertFalse((self.project / 'src/partial.cpp').exists())
        self.assertTrue((self.project / 'tests/vector_math_test.cpp').exists())
        self.assertFalse(stage.exists())

    def test_render_error_preserves_existing_data(self):
        scaffold(self.project)
        (self.project / '.template/templates/common/vcpkg.json.in').write_text('{ broken json')
        original = (self.project / 'src/vector_math.cpp').read_bytes()
        scaffold(self.project, force=True, success=False)
        self.assertEqual(original, (self.project / 'src/vector_math.cpp').read_bytes())

    def test_missing_source_template_preserves_existing_data(self):
        scaffold(self.project)
        (self.project / '.template/templates/executable/src/main.cpp.in').unlink()
        original = (self.project / 'src/vector_math.cpp').read_bytes()
        result = scaffold(self.project, kind='exec', force=True, success=False)
        self.assertIn('missing src/main.cpp', result.stdout)
        self.assertEqual(original, (self.project / 'src/vector_math.cpp').read_bytes())

    def test_run_requires_setup(self):
        scaffold(self.project)
        result = command(['cmake', '-P', self.project / 'scripts/run.cmake'],
                         self.project, success=False)
        self.assertIn('Run setup.sh / setup.bat first', result.stdout)
        self.assertFalse((self.project / 'external').exists())

    def test_existing_bootstrap_failure_preserves_tree(self):
        scaffold(self.project)
        tree = self.project / 'external/vcpkg'
        tree.mkdir(parents=True)
        script = tree / ('bootstrap-vcpkg.bat' if WINDOWS else 'bootstrap-vcpkg.sh')
        script.write_text('@exit /b 1\n' if WINDOWS else '#!/bin/sh\nexit 1\n')
        result = command(['cmake', '-P', self.project / 'scripts/setup.cmake'],
                         self.project, success=False)
        self.assertIn('vcpkg bootstrap failed', result.stdout)
        self.assertTrue(script.is_file())

    def test_malformed_vcpkg_fails_without_removal(self):
        scaffold(self.project)
        tree = self.project / 'external/vcpkg'
        tree.mkdir(parents=True)
        (tree / 'keep').write_text('malformed tree')
        result = command(['cmake', '-P', self.project / 'scripts/setup.cmake'],
                         self.project, success=False)
        self.assertIn('Malformed vcpkg tree', result.stdout)
        self.assertEqual((tree / 'keep').read_text(), 'malformed tree')


def integration(parent):
    """Use real fmt; prove installed consumers work without the original sources."""
    p = fresh(parent, 'integration executable')
    scaffold(p, 'SimpleProject', 'exec')
    print('Integration: first setup (clone/bootstrap/install/configure)', flush=True)
    launcher(p, 'setup')
    vcpkg = p / 'external/vcpkg'
    assert not (vcpkg / '.git').exists()
    executable = vcpkg / ('vcpkg.exe' if WINDOWS else 'vcpkg')
    identity = (executable.stat().st_mtime_ns, executable.stat().st_size)
    marker = vcpkg / 'reuse-marker'
    marker.write_text('keep')
    (p / 'build/keep').write_text('build survives setup')
    print('Integration: repeated setup and executable run', flush=True)
    launcher(p, 'setup')
    assert identity == (executable.stat().st_mtime_ns, executable.stat().st_size)
    assert marker.read_text() == 'keep'
    assert (p / 'build/keep').exists()
    (p / 'assets/check.txt').write_text('copied asset')
    (p / 'src/util').mkdir()
    (p / 'src/util/extra.cpp').write_text('int extra() { return 42; }\n')
    (p / 'src/util/extra.hpp').write_text('int extra();\n')
    main = p / 'src/main.cpp'
    main.write_text('#include "util/extra.hpp"\n' + main.read_text().replace('fmt::print(', 'if (extra() != 42) return 1;\n    fmt::print('))
    result = launcher(p, 'run')
    assert 'Hello from SimpleProject!' in result.stdout
    assert (p / 'build/debug/assets/check.txt').read_text() == 'copied asset'
    launcher(p, 'setup', 'release')
    launcher(p, 'run', 'release')
    # Multi-config generators must run the real target and copy assets beside it.
    command(['cmake', '-S', p, '-B', p / 'build/multi', '-G', 'Ninja Multi-Config',
             f'-DCMAKE_TOOLCHAIN_FILE={vcpkg}/scripts/buildsystems/vcpkg.cmake',
             f'-DVCPKG_INSTALLED_DIR={p}/vcpkg_installed', '-DVCPKG_MANIFEST_INSTALL=OFF'], p)
    command(['cmake', '--build', p / 'build/multi', '--config', 'Debug', '--target', 'run'], p)
    assert (p / 'build/multi/Debug/assets/check.txt').exists()

    lib = fresh(parent, 'integration library')
    scaffold(lib)
    (lib / 'external').mkdir()
    shutil.move(vcpkg, lib / 'external/vcpkg')
    shutil.copytree(p / 'vcpkg_installed', lib / 'vcpkg_installed')
    # Existing sources with a missing binary must bootstrap without cloning.
    local_vcpkg = lib / 'external/vcpkg' / ('vcpkg.exe' if WINDOWS else 'vcpkg')
    local_vcpkg.unlink()
    launcher(lib, 'setup')
    assert local_vcpkg.exists()
    assert (lib / 'external/vcpkg/reuse-marker').read_text() == 'keep'
    launcher(lib, 'setup')
    for shared in (False, True):
        flavor = 'shared' if shared else 'static'
        print(f'Integration: {flavor} library, example, CTest, install and consumer', flush=True)
        command(['cmake', '--preset', 'debug', f'-DBUILD_SHARED_LIBS={"ON" if shared else "OFF"}'], lib)
        launcher(lib, 'run')
        command(['cmake', '--build', '--preset', 'debug'], lib)
        command(['ctest', '--preset', 'debug'], lib)
        prefix = parent / f'install-{flavor}'
        command(['cmake', '--install', lib / 'build/debug', '--prefix', prefix, '--config', 'Debug'], lib)
        assert (prefix / 'include/vector_math/export.hpp').is_file()
        assert list(prefix.rglob('VectorMathConfigVersion.cmake'))
        consumer = parent / f'consumer-{flavor}'
        consumer.mkdir()
        (consumer / 'main.cpp').write_text('#include <vector_math/vector_math.hpp>\nint main() { return vector_math::add(2, 3) == 5 ? 0 : 1; }\n')
        (consumer / 'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.24)
project(Consumer LANGUAGES CXX)
find_package(VectorMath 0.1 CONFIG REQUIRED)
add_executable(consumer main.cpp)
target_link_libraries(consumer PRIVATE VectorMath::VectorMath)
''')
        deps = [x for x in (lib / 'vcpkg_installed').iterdir() if (x / 'share/fmt').exists()]
        assert len(deps) == 1, deps
        # Hide original public/private sources: the installed package must suffice.
        for directory in ('src', 'include'):
            (lib / directory).rename(lib / (directory + '-hidden'))
        try:
            command(['cmake', '-S', consumer, '-B', consumer / 'build', '-G', 'Ninja',
                     '-DCMAKE_BUILD_TYPE=Debug', f'-DCMAKE_PREFIX_PATH={prefix};{deps[0]}'], consumer)
            command(['cmake', '--build', consumer / 'build'], consumer)
            env = os.environ.copy()
            env['PATH'] = os.pathsep.join([str(prefix / 'bin'), str(deps[0] / 'debug/bin'),
                                          str(deps[0] / 'bin'), env.get('PATH', '')])
            command([consumer / 'build' / ('consumer.exe' if WINDOWS else 'consumer')], consumer, env=env)
        finally:
            for directory in ('src', 'include'):
                (lib / (directory + '-hidden')).rename(lib / directory)

    print('Integration: add_subdirectory consumer defaults', flush=True)
    outer = parent / 'subdirectory-consumer'
    outer.mkdir()
    (outer / 'CMakeLists.txt').write_text(f'''cmake_minimum_required(VERSION 3.24)
project(Outer LANGUAGES CXX)
add_subdirectory("{lib.as_posix()}" library)
if(VECTOR_MATH_BUILD_EXAMPLES OR VECTOR_MATH_BUILD_TESTS)
    message(FATAL_ERROR "Consumer unexpectedly enabled examples/tests")
endif()
if(TARGET VectorMath_example OR TARGET VectorMath_test)
    message(FATAL_ERROR "Consumer contains development targets")
endif()
''')
    command(['cmake', '-S', outer, '-B', outer / 'build', '-G', 'Ninja',
             f'-DCMAKE_PREFIX_PATH={deps[0]}'], outer)
    command(['cmake', '--build', outer / 'build'], outer)
    # Removing template machinery must leave the generated project fully usable.
    shutil.rmtree(lib / '.template')
    (lib / 'scaffold.sh').unlink()
    (lib / 'scaffold.bat').unlink()
    launcher(lib, 'run')
    print('Integration checks passed', flush=True)


# Run fast checks first; opt into network-dependent builds and consumer checks explicitly.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integration', action='store_true')
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ScaffoldTests)
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        raise SystemExit(1)
    if args.integration:
        with tempfile.TemporaryDirectory(prefix='cpp-template-integration-') as temp:
            integration(Path(temp))
