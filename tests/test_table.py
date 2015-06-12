"""Tests for the table-formatting interface
"""
from podcaster.table import TextTable, FormatError

import unittest
from textwrap import dedent


class TextTableTests(unittest.TestCase):
    def setUp(self):
        self.table = TextTable()

    def test_single(self):
        self.table.add_row(('a',))
        self.assertEqual(str(self.table), ' a ')
    
    def test_buffer(self):
        self.table = TextTable(3)
        self.table.add_row(('a',))
        self.assertEqual(str(self.table), '   a   ')

    def test_simple_jagged(self):
        self.table.add_row(('a', 'b'), seps=('|', '|', '|'))
        self.table.add_row(('a',), seps=('|', '|'))
        expected = dedent('''\
            | a | b |
            | a     |''')
        self.assertEqual(str(self.table), expected)

    def test_jagged(self):
        self.table.add_row(('a', 'b'), seps=('|', '|', '|'))
        self.table.add_row(('aaaaaa',), seps=('|', '|'))
        expected = dedent('''\
            | a | b  |
            | aaaaaa |''')
        self.assertEqual(str(self.table), expected)

    def test_three_jagged(self):
        self.table.add_row(('a', 'b', 'c'), seps=('|', '|', '|', '|'))
        self.table.add_row(('a', 'b'), seps=('|', '|', '|'))
        self.table.add_row(('a',), seps=('|', '|'))
        expected = dedent('''\
            | a | b | c |
            | a | b     |
            | a         |''')
        self.assertEqual(str(self.table), expected)

    def test_complex_jagged(self):
        self.table.add_row(('a', 'b', 'c'), seps=('|', '|', '|', '|'))
        self.table.add_row(('a', 'bbbbbb'), seps=('|', '|', '|'))
        self.table.add_row(('aaaaaaaaaaa',), seps=('|', '|'))
        self.table.add_row(('a', 'bb'), seps=('|', '|', '|'))
        self.table.add_row(('a',), seps=('|', '|'))
        expected = dedent('''\
            | a | b | c   |
            | a | bbbbbb  |
            | aaaaaaaaaaa |
            | a | bb      |
            | a           |''')
        self.assertEqual(str(self.table), expected)

    def test_align(self):
        self.table.add_row(('aaaaaaaaa',), seps=('|', '|'))
        self.table.add_row(('aa',), seps=('|', '|'), align='l')
        self.table.add_row(('a',), seps=('|', '|'), align='c')
        self.table.add_row(('aa',), seps=('|', '|'), align='r')
        self.table.add_row(('aaaaaaaaa',), seps=('|', '|'))
        expected = dedent('''\
            | aaaaaaaaa |
            | aa        |
            |     a     |
            |        aa |
            | aaaaaaaaa |''')
        self.assertEqual(str(self.table), expected)

    def test_fill_char(self):
        self.table.add_row(('aaa',), seps=('|', '|'), fill_char='=')
        self.table.add_row(('aaaaaa',), seps=('|', '|'), fill_char='-')
        self.table.add_row(('aaa',), seps=('|', '|'), fill_char='~')
        expected = dedent('''\
            |=aaa====|
            |-aaaaaa-|
            |~aaa~~~~|''')
        self.assertEqual(str(self.table), expected)

    def test_fill_char_err(self):
        with self.assertRaises(FormatError):
            self.table.add_row(('a',), seps=('|', '|'), fill_char='  ')
        with self.assertRaises(FormatError):
            self.table.add_row(('a',), seps=('|', '|'), fill_char='')
        with self.assertRaises(FormatError):
            self.table.add_break_row(seps=('|', '|'), fill_char='  ')

    def test_seps_err(self):
        with self.assertRaises(FormatError):
            self.table.add_row(('a',), seps=('||', '||'))
        with self.assertRaises(FormatError):
            self.table.add_row(('a',), seps=('|',))
        with self.assertRaises(FormatError):
            self.table.add_row(('a',), seps=('|', '|', '|'))
        with self.assertRaises(FormatError):
            self.table.set_seps('||', '|', '|')
        with self.assertRaises(FormatError):
            self.table.set_seps('|')
