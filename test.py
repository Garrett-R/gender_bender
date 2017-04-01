# -*- coding: utf-8 -*-
import unittest

from messing_around import GenderFlipper


class TestFlipGender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flipper = GenderFlipper()

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

    def test_plural(self):
        text = 'Attention Ladies and Gentlemen'

        result = self.flipper.flip_gender(text)
        self.assertEqual(result, 'Attention Gentlemen and Ladies')

    def test_unidirectional_flip(self):
        # actor is ambiguous (without context, which is how this algorithm
        # operates) so it is not flipped.
        text = 'The actor talked to the actress'

        result = self.flipper.flip_gender(text)
        self.assertEqual(result, 'The actor talked to the actor')

    def test_multi_word_replacement(self):
        text = 'she was one of many freshmen in the class'

        result = self.flipper.flip_gender(text)
        self.assertEqual(result, 'she was one of many first year students in '
                                 'the class')


