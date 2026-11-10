"""Offline package checks. Passing is not evidence of cloud deployment or readiness."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runtime.core import CoreSnapshot


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print('PASS:', message)


def fixture_tests(directory: Path, pattern: str, expected_count: int,
                  expected_failures: set[str]) -> None:
    code = '''import io,json,unittest,sys
suite=unittest.defaultTestLoader.discover('tests',pattern=sys.argv[1])
stream=io.StringIO()
r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
print(json.dumps({'count':r.testsRun,'failures':[t.id().split('.')[-1] for t,_ in r.failures],
'errors':[t.id() for t,_ in r.errors],'skipped':len(r.skipped),'log':stream.getvalue()}))'''
    result = subprocess.run([sys.executable, '-c', code, pattern], cwd=directory,
                            capture_output=True, text=True, timeout=60, check=True)
    data = json.loads(result.stdout)
    check(data['count'] == expected_count and not data['errors'] and not data['skipped']
          and set(data['failures']) == expected_failures,
          f'{pattern}: {expected_count} tests; expected failures {sorted(expected_failures)}')


def check_links() -> None:
    # Include imported and lifecycle documentation, not only the top-level instructions.
    # Validate local file targets; external URLs and heading fragments are not fetched.
    root = ROOT.resolve()
    files = sorted(p for p in root.rglob('*.md')
                   if not any(part in {'.git', 'node_modules', '__pycache__'}
                              or part.startswith('.venv')
                              for part in p.relative_to(root).parts))
    broken = []
    for path in files:
        if not path.resolve().is_relative_to(root):
            broken.append(f'{path.relative_to(root)} -> document leaves package')
            continue
        # Keep line boundaries while ignoring fenced and inline example code.
        lines, fence = [], None
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            marker = re.match(r'^\s*(`{3,}|~{3,})', line)
            if marker:
                run = marker.group(1)
                if fence is None:
                    fence = run
                elif run[0] == fence[0] and len(run) >= len(fence):
                    fence = None
                continue
            if fence is None:
                lines.append(line)
        text = re.sub(r'(`+).*?\1', '', '\n'.join(lines))
        # Inline links/images and reference definitions cover the package's Markdown.
        targets = re.findall(r'\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)', text)
        targets += re.findall(r'^\s*\[[^]]+\]:\s*(<[^>]+>|\S+)', text, flags=re.M)
        for raw in targets:
            raw = raw.removeprefix('<').removesuffix('>')
            if '{{' in raw or '{%' in raw:
                continue
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(root) or not target.exists():
                broken.append(f'{path.relative_to(root)} -> {raw}')
    check(not broken, 'Local Markdown file targets resolve' if not broken else '\n'.join(broken))

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture-state', choices=['starter', 'repaired'], default='starter')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'tools/shared-assets.lock.json').read_text(encoding='utf-8'))
    overrides = json.loads((ROOT / 'tools/development-assets.lock.json').read_text(encoding='utf-8'))['files']
    indexed = {entry['path']:entry for entry in overrides}
    check(len(indexed) == len(overrides), 'Development asset overrides are unique')
    check(set(indexed).issubset({entry['path'] for entry in manifest['files']}), 'Overrides refer to imported assets')
    for entry in manifest['files']:
        path = ROOT / entry['path']
        if args.fixture_state == 'repaired' and path.name == 'qualification.py' and 'solutions' not in path.parts:
            continue
        override = indexed.get(entry['path'])
        if override:
            check(override['original_imported_sha256'] == entry['imported_sha256'] and bool(override['reason']),
                  f"Preserved import provenance: {entry['path']}")
        expected_hash = override['development_sha256'] if override else entry['imported_sha256']
        check(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash,
              f"Pinned asset: {entry['path']}")
    for path in ROOT.rglob('*.py'):
        if '.git' not in path.parts and not any(p.startswith('.venv') for p in path.parts):
            compile(path.read_bytes(), str(path), 'exec')
    check(True, 'Python sources compile')
    notebook = json.loads((ROOT / 'Allfiles/L300-TW-Data/notebooks/curate_caldova_tables.ipynb').read_text())
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), 'curation-notebook', 'exec')
    check(True, 'Notebook code parses (Spark execution NOT tested)')
    snapshot = CoreSnapshot(ROOT / 'Allfiles/L300-TW-Data/data/core')
    expected_counts = dict(launch_program=10, product=25, plant=5, capacity_plan=60, batch=212, supplier=6)
    check({k:len(v) for k,v in snapshot.tables.items()} == expected_counts, 'Six core tables contain 318 rows')
    decision = snapshot.assess()
    for key, expected in dict(target_units=270000, qualified_units=251100, gap_units=18900,
            binding_plant_id='PL003', delayed_batch_count=8,
            eligible_cmo_ids=['CMO001','CMO002','CMO006']).items():
        check(decision[key] == expected, f'Core baseline: {key}')
    check(snapshot.validate(decision)['passed'], 'Independent local core decision validation')
    check_links()
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                   cwd=ROOT, check=True, timeout=90)
    fixture = ROOT / 'Labfiles/04-caldova-agents/Python/qualification-tool'
    fixture_tests(fixture, 'test_baseline.py', 9, set())
    fixture_tests(fixture, 'test_evaluation.py', 8, set())
    expected_failures = {'test_expired_qualification_is_rejected', 'test_missing_qualification_expiry_is_rejected'}
    fixture_tests(fixture, 'test_regression.py', 2, expected_failures if args.fixture_state == 'starter' else set())
    print('OFFLINE CHECKS PASSED. Cloud deployment, hosted agents, Fabric, SharePoint, Teams,')
    print('Agent 365, delegated access and end-to-end acceptance are NOT verified by this command.')
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, AssertionError, subprocess.SubprocessError) as error:
        print('FAIL:', error, file=sys.stderr)
        raise SystemExit(1)
