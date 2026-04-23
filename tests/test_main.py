import os
import tempfile
import unittest
import unicodedata
from pathlib import Path
from unittest import mock
import tomllib

from watchcat_app.path_fixer import fix_path, run_bulk_fix
from watchcat_app.unicode_utils import visualize_nfd


class VisualizeNFDTests(unittest.TestCase):
    def test_visualize_nfd_converts_jamo_to_compatibility_chars(self):
        nfd_text = unicodedata.normalize("NFD", "가")

        visualized = visualize_nfd(nfd_text)

        self.assertEqual(visualized, "ㄱ‌ㅏ‌")


class FixPathTests(unittest.TestCase):
    def test_fix_path_returns_false_for_missing_path(self):
        messages = []

        result = fix_path("/path/that/does/not/exist", messages.append)

        self.assertFalse(result)
        self.assertEqual(messages, [])

    def test_fix_path_returns_false_when_name_is_already_nfc(self):
        messages = []
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "가.txt")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write("content")

            result = fix_path(path, messages.append)

        self.assertFalse(result)
        self.assertEqual(messages, [])

    def test_fix_path_renames_nfd_name_and_logs_result(self):
        messages = []
        with tempfile.TemporaryDirectory() as tmpdir:
            nfd_name = unicodedata.normalize("NFD", "가.txt")
            src_path = os.path.join(tmpdir, nfd_name)
            expected_path = os.path.join(tmpdir, "가.txt")

            with open(src_path, "w", encoding="utf-8") as fp:
                fp.write("payload")

            result = fix_path(src_path, messages.append)

            self.assertTrue(result)
            self.assertEqual(os.listdir(tmpdir), ["가.txt"])
            with open(expected_path, encoding="utf-8") as fp:
                self.assertEqual(fp.read(), "payload")

        self.assertEqual(len(messages), 1)
        self.assertIn("✅ 교정 완료:", messages[0])
        self.assertIn("-> 가.txt", messages[0])

    def test_fix_path_returns_false_for_kfix_tmp_file(self):
        messages = []

        with mock.patch("watchcat_app.path_fixer.os.path.exists", return_value=True):
            result = fix_path("/tmp/가.txt.kfix_tmp", messages.append)

        self.assertFalse(result)
        self.assertEqual(messages, [])

    def test_fix_path_skips_when_normalized_target_is_a_different_entry(self):
        messages = []
        nfd = unicodedata.normalize("NFD", "가")
        nfc = unicodedata.normalize("NFC", "가")
        src = f"/tmp/{nfd}.txt"

        with mock.patch("watchcat_app.path_fixer.os.path.exists", side_effect=[True, True]):
            with mock.patch("watchcat_app.path_fixer.os.path.samefile", return_value=False):
                with mock.patch("watchcat_app.path_fixer.os.rename") as rename:
                    result = fix_path(src, messages.append)

        self.assertFalse(result)
        rename.assert_not_called()
        self.assertEqual(messages, [f"⚠️ 이름 충돌로 건너뜀: {nfd}.txt -> {nfc}.txt"])

    def test_fix_path_rolls_back_when_final_rename_fails(self):
        messages = []
        nfd = unicodedata.normalize("NFD", "가")
        nfc = unicodedata.normalize("NFC", "가")
        src = f"/tmp/{nfd}.txt"
        new = f"/tmp/{nfc}.txt"
        temp = f"/tmp/{nfc}.txt.kfix_tmp"

        def fake_exists(path):
            if path == src:   return True   # 파일 존재 확인
            if path == new:   return False  # 충돌 없음
            if path == temp:  return True   # 롤백 시 임시 파일 존재
            return False

        with mock.patch("watchcat_app.path_fixer.os.path.exists", side_effect=fake_exists):
            with mock.patch("watchcat_app.path_fixer._build_temp_path", return_value=temp):
                with mock.patch(
                    "watchcat_app.path_fixer.os.rename",
                    side_effect=[None, OSError("busy"), None],
                ) as rename:
                    result = fix_path(src, messages.append)

        self.assertFalse(result)
        self.assertEqual(
            rename.call_args_list,
            [
                mock.call(src, temp),
                mock.call(temp, new),
                mock.call(temp, src),  # 롤백
            ],
        )
        self.assertEqual(messages, [f"❌ 에러 발생 ({nfd}.txt): busy"])

    def test_fix_path_logs_rollback_failure(self):
        messages = []
        nfd = unicodedata.normalize("NFD", "가")
        nfc = unicodedata.normalize("NFC", "가")
        src = f"/tmp/{nfd}.txt"
        new = f"/tmp/{nfc}.txt"
        temp = f"/tmp/{nfc}.txt.kfix_tmp"

        def fake_exists(path):
            if path == src:   return True
            if path == new:   return False
            if path == temp:  return True
            return False

        with mock.patch("watchcat_app.path_fixer.os.path.exists", side_effect=fake_exists):
            with mock.patch("watchcat_app.path_fixer._build_temp_path", return_value=temp):
                with mock.patch(
                    "watchcat_app.path_fixer.os.rename",
                    side_effect=[None, OSError("busy"), OSError("locked")],
                ):
                    result = fix_path(src, messages.append)

        self.assertFalse(result)
        self.assertEqual(len(messages), 1)
        self.assertIn("롤백 실패", messages[0])
        self.assertIn("busy", messages[0])
        self.assertIn("locked", messages[0])


class BuildTempPathTests(unittest.TestCase):
    def test_build_temp_path_avoids_existing_temp(self):
        from watchcat_app.path_fixer import _build_temp_path

        with tempfile.TemporaryDirectory() as tmpdir:
            first = os.path.join(tmpdir, "가.txt.kfix_tmp")
            open(first, "w").close()

            result = _build_temp_path(tmpdir, "가.txt")

            self.assertEqual(result, os.path.join(tmpdir, "가.txt.kfix_tmp1"))


class BulkFixTests(unittest.TestCase):
    def test_run_bulk_fix_counts_scanned_and_fixed(self):
        messages = []
        results = []

        with tempfile.TemporaryDirectory() as tmpdir:
            nfd_file_name = unicodedata.normalize("NFD", "가.txt")
            nfd_dir_name = unicodedata.normalize("NFD", "나")
            file_path = os.path.join(tmpdir, nfd_file_name)
            dir_path = os.path.join(tmpdir, nfd_dir_name)

            with open(file_path, "w", encoding="utf-8") as fp:
                fp.write("file")
            os.mkdir(dir_path)

            run_bulk_fix(tmpdir, messages.append, lambda scanned, fixed: results.append((scanned, fixed)))

            self.assertTrue(os.path.exists(os.path.join(tmpdir, "가.txt")))
            self.assertTrue(os.path.isdir(os.path.join(tmpdir, "나")))

        self.assertEqual(results, [(2, 2)])
        self.assertEqual(len(messages), 2)

    def test_run_bulk_fix_processes_children_before_parents(self):
        # 자식보다 부모를 먼저 rename하면 자식 경로가 깨져 1건만 교정됨
        messages = []

        with tempfile.TemporaryDirectory() as tmpdir:
            nfd_parent = unicodedata.normalize("NFD", "나")
            parent_dir = os.path.join(tmpdir, nfd_parent)
            os.makedirs(parent_dir)

            nfd_child = unicodedata.normalize("NFD", "가.txt")
            child_path = os.path.join(parent_dir, nfd_child)
            with open(child_path, "w", encoding="utf-8") as fp:
                fp.write("x")

            run_bulk_fix(tmpdir, messages.append, lambda s, f: None)

            self.assertTrue(os.path.isdir(os.path.join(tmpdir, "나")))
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, "나", "가.txt")))

        self.assertEqual(len(messages), 2)


class PackagingConfigTests(unittest.TestCase):
    def test_flet_exclude_blocks_dev_only_metadata_from_app_zip(self):
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as fp:
            pyproject = tomllib.load(fp)

        excludes = set(pyproject["tool"]["flet"]["app"]["exclude"])

        self.assertTrue(
            {
                ".github",
                ".omc",
                ".vscode",
                ".DS_Store",
                ".gitignore",
                "AGENTS.md",
                "CLAUDE.md",
                "README.md",
                "uv.lock",
            }.issubset(excludes)
        )


if __name__ == "__main__":
    unittest.main()
