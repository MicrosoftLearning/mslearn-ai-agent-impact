"""Exercise the exact proposed check_links function without importing unrelated SDK code."""
import ast
import contextlib
import io
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'scripts/validate_repository.py'
tree=ast.parse(source.read_text())
functions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('check','check_links')], type_ignores=[])

class LinkReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.ns={'ROOT':self.root,'re':re,'unquote':unquote,'urlsplit':urlsplit}
        exec(compile(functions,str(source),'exec'),self.ns)
    def put(self,path,content=''):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content);return p
    def run_check(self):
        with contextlib.redirect_stdout(io.StringIO()):self.ns['check_links']()
    def test_good_relative_link(self):
        self.put('readme.md','[Setup](Instructions/Setup.md)');self.put('Instructions/Setup.md');self.run_check()
    def test_missing_lifecycle_link_detected(self):
        self.put('lifecycle/ex2/README.md','[Missing](missing.md)')
        with self.assertRaises(AssertionError):self.run_check()
    def test_missing_imported_readme_link_detected(self):
        self.put('Allfiles/L300-TW-Data/README.md','[Missing](missing.md)')
        with self.assertRaises(AssertionError):self.run_check()
    def test_above_root_is_rejected(self):
        self.put('readme.md','[Outside](../../outside.md)')
        with self.assertRaises(AssertionError):self.run_check()
    def test_percent_encoded_spaces(self):
        self.put('readme.md','[Data](data/a%20b.csv)');self.put('data/a b.csv');self.run_check()
    def test_fragments_and_external_not_fetched(self):
        self.put('readme.md','[X](https://example.invalid/none)\n[Y](#heading)\n[Z](//example.invalid/none)');self.run_check()
    def test_fenced_code_ignored(self):
        self.put('readme.md','```md\n[X](missing.md)\n```\n');self.run_check()
    def test_tilde_fence_ignored(self):
        self.put('readme.md','~~~md\n[X](missing.md)\n~~~\n');self.run_check()
    def test_reference_definition_checked(self):
        self.put('readme.md','[Label][ref]\n\n[ref]: absent.md\n')
        with self.assertRaises(AssertionError):self.run_check()
    def test_virtual_env_ignored(self):
        self.put('.venv/lib/readme.md','[X](missing.md)');self.run_check()
    def test_site_templates_ignored(self):
        self.put('index.md','[lab]({{ site.github.url }}{{ activity.url }})');self.run_check()
    def test_link_title_and_angle_target(self):
        self.put('readme.md','[X](<a b.md> "Title")');self.put('a b.md');self.run_check()
    def test_case_sensitive_target(self):
        self.put('readme.md','[X](Setup.md)');self.put('setup.md')
        with self.assertRaises(AssertionError):self.run_check()
    def test_symlink_outside_is_rejected(self):
        self.put('readme.md','[X](out.md)');(self.root/'out.md').symlink_to('/etc/hosts')
        with self.assertRaises(AssertionError):self.run_check()

if __name__=='__main__':unittest.main(verbosity=2)
