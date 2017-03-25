# -*- coding: utf-8 -*-
import unittest

from messing_around import GenderFlipper


class TestFlipGender(unittest.TestCase):

    def test_flip_back_and_forth(self):
        flipper = GenderFlipper()
        text = 'himself did not know herself.'

        result = flipper.flip_gender(text)
        self.assertEqual(result, 'herself did not know himself.')

    def test_preserves_case(self):
        flipper = GenderFlipper()
        text = 'himself did not know Herself.'

        result = flipper.flip_gender(text)
        self.assertEqual(result, 'herself did not know Himself.')
