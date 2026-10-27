"""Tests for the Smart Lock DFA. Run with:  python -m unittest discover tests"""
import itertools
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from main import ALPHABET, build_dfa, ends_with_code, run_dfa, run_naive   # noqa: E402


def delta_by_definition(code, state, key):
    """delta(i, x) = length of the longest prefix of the code that is a suffix of (first i digits) + x,
    written independently of build_dfa."""
    typed = (code if state == len(code) else code[:state]) + key
    return max(j for j in range(len(code) + 1) if typed.endswith(code[:j]))


class TestConstruction(unittest.TestCase):
    def test_table_for_1213_by_hand(self):
        t = build_dfa("1213")
        by_hand = [{"1": 1, "2": 0, "3": 0}, {"1": 1, "2": 2, "3": 0}, {"1": 3, "2": 0, "3": 0},
                   {"1": 1, "2": 2, "3": 4}, {"1": 1, "2": 0, "3": 0}]
        for state, row in enumerate(by_hand):
            self.assertEqual({k: t[state][k] for k in row}, row)
            self.assertEqual(t[state]["9"], 0)                      # a key not in the code always resets

    def test_every_move_follows_the_definition(self):
        for code in ["1213", "1111", "1122", "1234", "4545", "121", "5", "98765"]:
            t = build_dfa(code)
            self.assertEqual(len(t), len(code) + 1)
            for state in range(len(code) + 1):
                for key in ALPHABET:
                    self.assertEqual(t[state][key], delta_by_definition(code, state, key))


class TestSimulation(unittest.TestCase):
    def test_examples(self):
        t = build_dfa("1213")
        self.assertEqual(run_dfa(t, "1213", "121213"), ([0, 1, 2, 3, 2, 3, 4], True))
        self.assertFalse(run_naive("1213", "121213")[1])
        self.assertEqual(run_dfa(t, "1213", "1212"), ([0, 1, 2, 3, 2], False))
        self.assertEqual(run_dfa(t, "1213", ""), ([0], False))

    def test_opens_exactly_when_the_code_is_typed(self):
        for code in ["1213", "1111", "1122"]:
            t = build_dfa(code)
            for n in range(8):
                for keys in itertools.product("1239", repeat=n):
                    s = "".join(keys)
                    self.assertEqual(run_dfa(t, code, s)[1], ends_with_code(code, s))

    def test_naive_lock_fails_only_on_self_overlapping_codes(self):
        def misses(code):
            return sum(ends_with_code(code, s) and not run_naive(code, s)[1]
                       for s in ("".join(k) for k in itertools.product("1234", repeat=7)))
        self.assertEqual(misses("1234"), 0)
        self.assertGreater(misses("1213"), 0)

    def test_long_input(self):
        t = build_dfa("1213")
        path, opened = run_dfa(t, "1213", "12" * 500_000 + "13")
        self.assertTrue(opened)
        self.assertEqual(len(path), 1_000_003)


class TestCommandLine(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, os.path.join(ROOT, "main.py"), *args], capture_output=True, text=True)

    def test_bad_input_is_rejected(self):
        for args, message in ((["--keys", "12x3"], "keys must contain only numeric digits"),
                              (["--code", "12a4"], "code must contain only numeric digits")):
            out = self.run_cli(*args)
            self.assertEqual(out.returncode, 1)
            self.assertIn(message, out.stdout)

    def test_step_table(self):
        out = self.run_cli("--code", "1213", "--keys", "121213").stdout
        self.assertIn("naive lock forgets '12'", out)
        self.assertIn("DFA opens", out)


if __name__ == "__main__":
    unittest.main()
