# -*- coding: utf-8 -*-
"""updater.py 纯逻辑单元测试：version_tuple / is_newer。"""
import unittest

from updater import is_newer, version_tuple


class VersionTupleTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(version_tuple("v0.6.19"), (0, 6, 19))

    def test_no_v(self):
        self.assertEqual(version_tuple("0.6.19"), (0, 6, 19))

    def test_upper_v(self):
        self.assertEqual(version_tuple("V0.6.19"), (0, 6, 19))

    def test_empty(self):
        self.assertEqual(version_tuple(""), ())
        self.assertEqual(version_tuple(None), ())

    def test_junk(self):
        self.assertEqual(version_tuple("abc"), ())

    def test_extra_tail(self):
        # 数字尾巴取前 4 段；beta1 这类尾巴里的数字也会被抓进来（实现如此，锁死行为）
        self.assertEqual(version_tuple("v1.2.3.4.5"), (1, 2, 3, 4))
        self.assertEqual(version_tuple("v0.6.19-beta1"), (0, 6, 19, 1))
        self.assertEqual(version_tuple("v0.6.30.1"), (0, 6, 30, 1))

    def test_whitespace(self):
        self.assertEqual(version_tuple("  v0.6.19  "), (0, 6, 19))


class IsNewerTest(unittest.TestCase):
    def test_string_compare_trap(self):
        # 字符串比较会把 0.6.10 排在 0.6.9 前面，数字比较必须相反
        self.assertTrue(is_newer("v0.6.10", "v0.6.9"))
        self.assertFalse(is_newer("v0.6.9", "v0.6.10"))

    def test_equal(self):
        self.assertFalse(is_newer("v0.6.31", "v0.6.31"))
        self.assertFalse(is_newer("v0.6.31", "0.6.31"))

    def test_older(self):
        self.assertFalse(is_newer("v0.6.30", "v0.6.31"))
        self.assertFalse(is_newer("v0.5.9", "v0.6.0"))

    def test_missing_component_is_zero(self):
        # v0.7 > v0.6.99：缺的段按 0 补
        self.assertTrue(is_newer("v0.7", "v0.6.99"))
        self.assertFalse(is_newer("v0.6", "v0.6.1"))

    def test_empty_means_no(self):
        self.assertFalse(is_newer("", "v0.6.31"))
        self.assertFalse(is_newer("v0.6.31", ""))
        self.assertFalse(is_newer(None, "v0.6.31"))

    def test_different_length_equal(self):
        self.assertFalse(is_newer("v0.6.31", "v0.6.31.0"))
        self.assertFalse(is_newer("v0.6.31.0", "v0.6.31"))


if __name__ == "__main__":
    unittest.main()
