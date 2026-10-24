#!/usr/bin/env python3
"""Advisory release checks; discovery never edits or approves compatibility entries."""

import argparse
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

CMAKE_RELEASE_URL = 'https://api.github.com/repos/Kitware/CMake/releases/latest'
CPP_STANDARD_URL = 'https://isocpp.org/std/the-standard'


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def published_cpp(page):
    parser = PageText()
    parser.feed(page)
    text = ' '.join(' '.join(parser.parts).split())
    matches = set(re.findall(r'current ISO C\+\+ standard is C\+\+\s*(\d{2})\b', text, re.I))
    if len(matches) != 1:
        raise ValueError('Could not identify the published C++ standard; the upstream page may have changed.')
    return int(matches.pop())


def cmake_version(value):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', value)
    if not match:
        raise ValueError(f'Expected a stable CMake major.minor.patch version, got {value!r}.')
    return tuple(map(int, match.groups()))


def latest_cmake(payload):
    release = json.loads(payload)
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Latest CMake response is not a stable release.')
    return cmake_version(release['tag_name'])


def mapped_standards(manifest):
    # Also read the committed layout while the map rename is under review.
    if 'compatibilityMap' in manifest:
        rows, key = manifest['compatibilityMap'], 'cppStandard'
    else:
        rows, key = manifest['cppStandards'], 'standard'
    standards = {int(row[key]) for row in rows}
    if not standards:
        raise ValueError('The compatibility map is empty.')
    return standards


def fetch(url):
    headers = {'User-Agent': 'cpp-template-compatibility-watch'}
    if url == CMAKE_RELEASE_URL:
        headers['Accept'] = 'application/vnd.github+json'
        token = os.environ.get('GH_TOKEN')
        if token:
            headers['Authorization'] = f'Bearer {token}'
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        return response.read().decode('utf-8')


def check_updates(standards, reviewed_cmake, fetch_page=fetch):
    """Return findings separately so an unavailable source cannot hide the other."""
    findings = []
    try:
        standard = published_cpp(fetch_page(CPP_STANDARD_URL))
        if standard not in standards:
            findings.append(('warning', '.scaffold/compatibility.json',
                             f'C++{standard} is published but missing from the compatibility map. '
                             f'Review compiler support and determine minCmake. Source: {CPP_STANDARD_URL}'))
        else:
            findings.append(('notice', '.scaffold/compatibility.json',
                             f'The published C++{standard} standard is present in the compatibility map.'))
    except (OSError, ValueError, KeyError, TypeError) as error:
        findings.append(('warning', '.scaffold/compatibility.json',
                         f'C++ freshness check is inconclusive: {error} Source: {CPP_STANDARD_URL}'))

    try:
        version = latest_cmake(fetch_page(CMAKE_RELEASE_URL))
        latest = '.'.join(map(str, version))
        if version > cmake_version(reviewed_cmake):
            findings.append(('warning', '.github/workflows/compatibility-updates.yml',
                             f'CMake {latest} is newer than the reviewed baseline {reviewed_cmake}. '
                             'Run the compatibility tests and review generated projects before updating '
                             'the baseline. A new CMake release does not automatically require a map change.'))
        else:
            findings.append(('notice', '.github/workflows/compatibility-updates.yml',
                             f'Latest stable CMake {latest} does not exceed the reviewed baseline {reviewed_cmake}.'))
    except (OSError, ValueError, KeyError, TypeError) as error:
        findings.append(('warning', '.github/workflows/compatibility-updates.yml',
                         f'CMake freshness check is inconclusive: {error} Source: {CMAKE_RELEASE_URL}'))
    return findings


def emit(findings):
    for level, file, message in findings:
        escaped = message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print(f'::{level} file={file},title=Compatibility review::{escaped}')
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as output:
            output.write('## Compatibility release review\n\n')
            for level, _, message in findings:
                output.write(f'- **{level.title()}**: {message}\n')
            output.write('\nThis is advisory. Releases do not establish compiler or template compatibility.\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('.scaffold/compatibility.json'))
    parser.add_argument('--reviewed-cmake', required=True, help='Last CMake release reviewed with the compatibility tests')
    args = parser.parse_args()
    try:
        cmake_version(args.reviewed_cmake)
        standards = mapped_standards(json.loads(args.manifest.read_text()))
    except (OSError, ValueError, KeyError, TypeError) as error:
        emit([('warning', str(args.manifest), f'Compatibility freshness check is inconclusive: {error}')])
        return
    emit(check_updates(standards, args.reviewed_cmake))


if __name__ == '__main__':
    main()
