"""Offline release scenarios; no network access is needed by these tests."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

import check_updates as watch


class CompatibilityUpdateTests(unittest.TestCase):
    @staticmethod
    def sources(cpp=23, cmake='v4.4.2'):
        def fetch(url):
            if url == watch.CPP_STANDARD_URL:
                return f'<p>The current ISO C++ standard is <b>C++{cpp}</b>.</p><p>In-progress C++29</p>'
            return json.dumps({'tag_name': cmake, 'draft': False, 'prerelease': False})
        return fetch

    def test_current_releases_have_no_warnings(self):
        findings = watch.check_updates({11, 14, 17, 20, 23}, '4.4.2', self.sources())
        self.assertEqual([level for level, _, _ in findings], ['notice', 'notice'])

    def test_published_cpp26_missing_from_map_warns(self):
        findings = watch.check_updates({11, 14, 17, 20, 23}, '4.4.2', self.sources(cpp=26))
        self.assertEqual(findings[0][0], 'warning')
        self.assertIn('C++26 is published but missing', findings[0][2])
        self.assertIn('minCmake', findings[0][2])

    def test_mapped_new_standard_needs_no_code_change(self):
        findings = watch.check_updates({23, 26}, '4.4.2', self.sources(cpp=26))
        self.assertEqual(findings[0][0], 'notice')

    def test_cpp_draft_does_not_count_as_a_published_standard(self):
        self.assertEqual(watch.published_cpp(self.sources()(watch.CPP_STANDARD_URL)), 23)

    def test_cmake5_warns_without_requiring_a_map_change(self):
        findings = watch.check_updates({23}, '4.4.2', self.sources(cmake='v5.0.0'))
        self.assertEqual(findings[1][0], 'warning')
        self.assertIn('CMake 5.0.0', findings[1][2])
        self.assertIn('does not automatically require a map change', findings[1][2])

    def test_new_patch_release_also_warns(self):
        findings = watch.check_updates({23}, '4.4.2', self.sources(cmake='v4.4.3'))
        self.assertEqual(findings[1][0], 'warning')

    def test_prerelease_response_is_inconclusive(self):
        def fetch(url):
            if url == watch.CPP_STANDARD_URL:
                return self.sources()(url)
            return json.dumps({'tag_name': 'v5.0.0-rc1', 'prerelease': True})
        findings = watch.check_updates({23}, '4.4.2', fetch)
        self.assertIn('inconclusive', findings[1][2])

    def test_unavailable_source_does_not_hide_other_release(self):
        def fetch(url):
            if url == watch.CPP_STANDARD_URL:
                raise URLError('offline')
            return self.sources(cmake='v5.0.0')(url)
        findings = watch.check_updates({23}, '4.4.2', fetch)
        self.assertIn('inconclusive', findings[0][2])
        self.assertIn('CMake 5.0.0', findings[1][2])

    def test_changed_upstream_format_does_not_claim_freshness(self):
        findings = watch.check_updates({23}, '4.4.2', lambda url: '<html>unknown format</html>')
        self.assertTrue(all(level == 'warning' and 'inconclusive' in message for level, _, message in findings))

    def test_reads_both_the_committed_and_reviewed_map_layout(self):
        self.assertEqual(watch.mapped_standards({'cppStandards': [{'standard': 23}]}), {23})
        self.assertEqual(watch.mapped_standards({'compatibilityMap': [{'cppStandard': 23}]}), {23})

    def test_warning_is_escaped_and_written_to_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            summary = Path(directory) / 'summary.md'
            output = io.StringIO()
            with patch.dict(os.environ, {'GITHUB_STEP_SUMMARY': str(summary)}), redirect_stdout(output):
                watch.emit([('warning', '.scaffold/compatibility.json', 'example%\nsecond line')])
            self.assertIn('example%25%0Asecond line', output.getvalue())
            self.assertIn('Compatibility release review', summary.read_text())
            self.assertIn('**Warning**', summary.read_text())


if __name__ == '__main__':
    unittest.main()
