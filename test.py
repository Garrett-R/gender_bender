# -*- coding: utf-8 -*-
import unittest

from messing_around import GenderFlipper


class TestFlipGender(unittest.TestCase):
    def setUp(self):
        self.flipper = GenderFlipper()

    def test_flip_back_and_forth(self):
        text = 'himself did not know herself.'

        result = self.flipper.flip_gender(text)
        self.assertEqual(result, 'herself did not know himself.')

    def test_preserves_case(self):
        text = 'himself did not know Herself.'

        result = self.flipper.flip_gender(text)
        self.assertEqual(result, 'herself did not know Himself.')

    def test_word_with_period(self):
        text = 'Mr. Jones is back!'

        result = self.flipper.flip_gender(text)
        self.assertEqual(result, 'Ms. Jones is back!')
