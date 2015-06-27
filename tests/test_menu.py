"""Tests for the Podcaster menu interface
"""
from podcaster.menu import build_data_rows, build_menu
from podcaster.table import TextTable

import unittest


class MenuTests(unittest.TestCase):
    def setUp(self):
        self._iden = lambda f: f
        self.table = TextTable()

    def test_build_rows(self):
        rows = build_data_rows(str, [1], ('header', self._iden, str))
        self.assertEqual(rows, [['CMD', 'header'], ['0', '1']])

        rows = build_data_rows(str, [], ('header', self._iden, str))
        self.assertEqual(rows, [['CMD', 'header']])

    def test_only_title(self):
        title = 'Foo'
        lines = build_menu(title).split('\n')
        self.assertRegexpMatches(lines[0], r'\+-*\+')
        self.assertRegexpMatches(lines[1], r'\| *%s *\|' % title)
        self.assertRegexpMatches(lines[2], r'\+-*\+')

    def test_only_actions(self):
        title = 'Foo'
        actions = (('a', 'b'), ('1', '2'), ('A', 'B'))
        lines = build_menu(title, action_rows=actions).split('\n')
        self.assertRegexpMatches(lines[3], r'\| *%s *\| *%s *\|' % actions[0])
        self.assertRegexpMatches(lines[4], r'\| *%s *\| *%s *\|' % actions[1])
        self.assertRegexpMatches(lines[5], r'\| *%s *\| *%s *\|' % actions[2])
        self.assertRegexpMatches(lines[6], r'\+-*\+-*\+')

    def test_no_data_rows(self):
        title = 'Foo'
        rows = (('a', 'b'),)
        lines = build_menu(title, data_rows=rows).split('\n')
        self.assertRegexpMatches(lines[3], r'\| *%s *\| *%s *\|' % rows[0])
        self.assertRegexpMatches(lines[4], r'\+-*\+-*\+')
        self.assertRegexpMatches(lines[5], r'\? *There\'s nothing here... *\?')
        self.assertRegexpMatches(lines[6], r'\+-*\+-*\+')

    def test_data_rows(self):
        title = 'Foo'
        rows = (('a', 'b', 'c'), ('1', '2', '3'))
        lines = build_menu(title, data_rows=rows).split('\n')
        self.assertRegexpMatches(lines[3], r'\| *%s *\| *%s *\| *%s *\|' % rows[0])
        self.assertRegexpMatches(lines[4], r'\+-*\+-*v-*\+')
        self.assertRegexpMatches(lines[5], r'\| *%s *\| *%s *%s *\|' % rows[1])
        self.assertRegexpMatches(lines[6], r'\+-*\+-*\^-*\+')

    def test_multiple_data_cols(self):
        title = 'Foo'
        rows = (('a', 'b', 'c', 'd'), ('1', '2', '3', '4'))
        lines = build_menu(title, data_rows=rows).split('\n')
        self.assertRegexpMatches(lines[3], r'\| *%s *\| *%s *\| *%s *\| *%s *\|' % rows[0])
        self.assertRegexpMatches(lines[4], r'\+-*\+-*v-*v-*\+')
        self.assertRegexpMatches(lines[5], r'\| *%s *\| *%s *%s *%s *\|' % rows[1])
        self.assertRegexpMatches(lines[6], r'\+-*\+-*\^-*\^-*\+')
