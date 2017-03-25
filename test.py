# -*- coding: utf-8 -*-
import unittest

from messing_around import flip_gender


class TestFlipGender(unittest.TestCase):

    def test_flip_back_and_forth(self):
        text = 'himself did not know herself.'

        result = flip_gender(text)
        self.assertEqual(result, 'herself did not know himself.')

    def test_preserves_case(self):
        text = 'himself did not know Herself.'

        result = flip_gender(text)
        self.assertEqual(result, 'herself did not know Himself.')


