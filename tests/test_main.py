import os
import tempfile
import unittest
import unicodedata
from unittest import mock

import main


class VisualizeNFDTests(unittest.TestCase):
    def test_visualize_nfd_converts_jamo_to_compatibility_chars(self):
        nfd_text = unicodedata.normalize("NFD", "가")

        visualized = main.visualize_nfd(nfd_text)

        self.assertEqual(visualized, "ㄱ\u200cㅏ\u200c")


class FixPathTests(unittest.TestCase):
    def test_fix_path_returns_false_for_missing_path(self):
        messages = []

        result = main.fix_path("/path/that/does/not/exist", messages.append)

        self.assertFalse(result)
        self.assertEqual(messages, [])

    def test_fix_path_returns_false_when_name_is_already_nfc(self):
        messages = []
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "가.txt")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write("content")

            result = main.fix_path(path, messages.append)

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

            result = main.fix_path(src_path, messages.append)

            self.assertTrue(result)
            self.assertEqual(os.listdir(tmpdir), ["가.txt"])
            with open(expected_path, encoding="utf-8") as fp:
                self.assertEqual(fp.read(), "payload")

        self.assertEqual(len(messages), 1)
        self.assertIn("✅ 교정 완료:", messages[0])
        self.assertIn("-> 가.txt", messages[0])

    def test_fix_path_skips_when_normalized_target_is_a_different_entry(self):
        messages = []

        with mock.patch("watchcat_app.path_fixer.os.path.exists", side_effect=[True, True]):
            with mock.patch("watchcat_app.path_fixer.os.path.samefile", return_value=False):
                with mock.patch("watchcat_app.path_fixer.os.rename") as rename:
                    result = main.fix_path("/tmp/가.txt", messages.append)

        self.assertFalse(result)
        rename.assert_not_called()
        self.assertEqual(messages, ["⚠️ 이름 충돌로 건너뜀: 가.txt -> 가.txt"])

    def test_fix_path_rolls_back_when_final_rename_fails(self):
        messages = []

        with mock.patch(
            "watchcat_app.path_fixer.os.path.exists",
            side_effect=[True, False, False, True],
        ):
            with mock.patch(
                "watchcat_app.path_fixer.os.rename",
                side_effect=[None, OSError("busy"), None],
            ) as rename:
                result = main.fix_path("/tmp/가.txt", messages.append)

        self.assertFalse(result)
        self.assertEqual(
            rename.call_args_list,
            [
                mock.call("/tmp/가.txt", "/tmp/가.txt.kfix_tmp"),
                mock.call("/tmp/가.txt.kfix_tmp", "/tmp/가.txt"),
                mock.call("/tmp/가.txt.kfix_tmp", "/tmp/가.txt"),
            ],
        )
        self.assertEqual(messages, ["❌ 에러 발생 (가.txt): busy"])


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

            main.run_bulk_fix(tmpdir, messages.append, lambda scanned, fixed: results.append((scanned, fixed)))

            self.assertTrue(os.path.exists(os.path.join(tmpdir, "가.txt")))
            self.assertTrue(os.path.isdir(os.path.join(tmpdir, "나")))

        self.assertEqual(results, [(2, 2)])
        self.assertEqual(len(messages), 2)


if __name__ == "__main__":
    unittest.main()
