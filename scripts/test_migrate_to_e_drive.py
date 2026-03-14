"""
Tests for migrate_to_e_drive.py — validates logic with a temp directory structure.
Run: python "C:/Users/User/Documents/Obsidian Vault/scripts/test_migrate_to_e_drive.py"
"""
import os
import sys
import shutil
import tempfile
import unittest
import logging
from datetime import datetime
from pathlib import Path

# --- Import module under test by patching its constants ---
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import migrate_to_e_drive as mig


class TestMigration(unittest.TestCase):

    def setUp(self):
        """Create temp source and dest dirs with synthetic files."""
        self.src_dir = Path(tempfile.mkdtemp(prefix="mig_src_"))
        self.dst_dir = Path(tempfile.mkdtemp(prefix="mig_dst_"))
        self.log_path = self.dst_dir / "test-migration.log"
        self.log = logging.getLogger("test_migrate")
        self.log.setLevel(logging.DEBUG)
        if not self.log.handlers:
            self.log.addHandler(logging.StreamHandler(sys.stdout))

        # Patch module constants for test
        mig.SOURCE_ROOT = self.src_dir
        mig.DEST_ROOT = self.dst_dir
        mig.LOG_PATH = self.log_path

    def tearDown(self):
        """Remove temp dirs."""
        shutil.rmtree(str(self.src_dir), ignore_errors=True)
        shutil.rmtree(str(self.dst_dir), ignore_errors=True)

    def _create_file(self, rel_path: str, content: str, mtime_dt: datetime) -> Path:
        """Create a file under src_dir with given content and modification time."""
        fpath = self.src_dir / rel_path
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
        ts = mtime_dt.timestamp()
        os.utime(str(fpath), (ts, ts))
        return fpath

    # ---------------------------------------------------------------
    # Test: should_skip_dir
    # ---------------------------------------------------------------
    def test_skip_git(self):
        """Directories in SKIP_DIRS should be skipped."""
        self.assertTrue(mig.should_skip_dir(".git"), msg=".git should be skipped")
        self.assertTrue(mig.should_skip_dir("__pycache__"), msg="__pycache__ should be skipped")
        self.assertTrue(mig.should_skip_dir("venv"), msg="venv should be skipped")
        self.assertTrue(mig.should_skip_dir("node_modules"), msg="node_modules should be skipped")

    def test_no_skip_normal(self):
        """Normal dirs should NOT be skipped."""
        self.assertFalse(mig.should_skip_dir("scripts"), msg="scripts should not be skipped")
        self.assertFalse(mig.should_skip_dir("PROJECTS"), msg="PROJECTS should not be skipped")
        self.assertFalse(mig.should_skip_dir("data"), msg="data should not be skipped")

    # ---------------------------------------------------------------
    # Test: collect_files — cutoff filter
    # ---------------------------------------------------------------
    def test_collect_after_cutoff(self):
        """Files modified after cutoff should be collected."""
        self._create_file("new.csv", "new data", datetime(2026, 2, 1))
        self._create_file("old.csv", "old data", datetime(2025, 12, 1))
        self._create_file("edge.csv", "edge data", datetime(2026, 1, 19, 0, 0, 0))

        # Set cutoff to Jan 19
        mig.CUTOFF_TS = datetime(2026, 1, 19, 0, 0, 0).timestamp()
        result = mig.collect_files(self.src_dir, self.log)
        names = sorted([f.name for f in result])
        self.assertIn("new.csv", names, msg="new.csv should be collected (after cutoff)")
        self.assertIn("edge.csv", names, msg="edge.csv should be collected (exactly at cutoff)")
        self.assertNotIn("old.csv", names, msg="old.csv should NOT be collected (before cutoff)")

    def test_collect_skips_git(self):
        """Files inside .git/ should not be collected."""
        self._create_file(".git/HEAD", "ref: refs/heads/main", datetime(2026, 2, 1))
        self._create_file("real.txt", "real file", datetime(2026, 2, 1))

        mig.CUTOFF_TS = datetime(2026, 1, 19).timestamp()
        result = mig.collect_files(self.src_dir, self.log)
        names = [f.name for f in result]
        self.assertNotIn("HEAD", names, msg=".git/HEAD should be skipped")
        self.assertIn("real.txt", names, msg="real.txt should be collected")

    def test_collect_skips_venv(self):
        """Files inside venv/ should not be collected."""
        self._create_file("venv/lib/site.py", "site", datetime(2026, 2, 1))
        self._create_file("app.py", "app", datetime(2026, 2, 1))

        mig.CUTOFF_TS = datetime(2026, 1, 19).timestamp()
        result = mig.collect_files(self.src_dir, self.log)
        names = [f.name for f in result]
        self.assertNotIn("site.py", names, msg="venv/lib/site.py should be skipped")
        self.assertIn("app.py", names, msg="app.py should be collected")

    # ---------------------------------------------------------------
    # Test: copy_file — actual copy + verification
    # ---------------------------------------------------------------
    def test_copy_file_success(self):
        """copy_file should create dst with matching size and return True."""
        src = self._create_file("data/test.csv", "hello,world\n1,2\n3,4", datetime(2026, 2, 1))
        rel = src.relative_to(self.src_dir)
        dst = self.dst_dir / rel

        result = mig.copy_file(src, dst, self.log)
        self.assertTrue(result, msg="copy_file should return True on success")
        self.assertTrue(dst.exists(), msg="destination file should exist")
        self.assertEqual(src.stat().st_size, dst.stat().st_size, msg="file sizes should match")
        self.assertEqual(
            src.read_text(encoding="utf-8"),
            dst.read_text(encoding="utf-8"),
            msg="file contents should match exactly"
        )

    def test_copy_preserves_structure(self):
        """Nested dir structure should be mirrored in destination."""
        self._create_file("PROJECTS/bot/scripts/run.py", "print('hi')", datetime(2026, 2, 1))
        src = self.src_dir / "PROJECTS" / "bot" / "scripts" / "run.py"
        rel = src.relative_to(self.src_dir)
        dst = self.dst_dir / rel

        mig.copy_file(src, dst, self.log)
        self.assertTrue(dst.exists(), msg="nested file should be copied")
        self.assertEqual(
            dst.parent.name, "scripts",
            msg="parent dir should be 'scripts'"
        )

    def test_copy_file_bad_src(self):
        """copy_file should return False and log error for nonexistent src."""
        fake_src = self.src_dir / "nonexistent.txt"
        fake_dst = self.dst_dir / "nonexistent.txt"
        result = mig.copy_file(fake_src, fake_dst, self.log)
        self.assertFalse(result, msg="copy_file should return False for missing src")

    # ---------------------------------------------------------------
    # Test: collect_files — empty dir
    # ---------------------------------------------------------------
    def test_collect_empty_dir(self):
        """Empty source should return empty list."""
        mig.CUTOFF_TS = datetime(2026, 1, 19).timestamp()
        result = mig.collect_files(self.src_dir, self.log)
        self.assertEqual(len(result), 0, msg="empty dir should yield 0 files")

    # ---------------------------------------------------------------
    # Test: collect — nested structure with mixed dates
    # ---------------------------------------------------------------
    def test_collect_nested_mixed(self):
        """Mixed old/new files across nested dirs should filter correctly."""
        self._create_file("a/b/new1.csv", "d1", datetime(2026, 3, 1))
        self._create_file("a/b/old1.csv", "d2", datetime(2025, 6, 1))
        self._create_file("c/new2.py", "d3", datetime(2026, 1, 20))
        self._create_file("c/old2.py", "d4", datetime(2025, 1, 1))
        self._create_file("root_new.md", "d5", datetime(2026, 2, 15))

        mig.CUTOFF_TS = datetime(2026, 1, 19).timestamp()
        result = mig.collect_files(self.src_dir, self.log)
        names = sorted([f.name for f in result])
        self.assertEqual(names, ["new1.csv", "new2.py", "root_new.md"],
                         msg="should collect only the 3 files after cutoff")

    # ---------------------------------------------------------------
    # Test: copy preserves timestamps
    # ---------------------------------------------------------------
    def test_copy_preserves_mtime(self):
        """shutil.copy2 should preserve modification time."""
        target_dt = datetime(2026, 2, 10, 14, 30, 0)
        src = self._create_file("ts_test.txt", "timestamp check", target_dt)
        dst = self.dst_dir / "ts_test.txt"

        mig.copy_file(src, dst, self.log)
        src_mtime = src.stat().st_mtime
        dst_mtime = dst.stat().st_mtime
        self.assertAlmostEqual(src_mtime, dst_mtime, delta=2.0,
                               msg="mtime should be preserved within 2s tolerance")


if __name__ == "__main__":
    unittest.main(verbosity=2)
