# -*- coding: utf-8 -*-
import unittest

from gender_bender.gender_tools import _copy_case, gender_bend

class TestFlipGender(unittest.TestCase):

    def test_flip_back_and_forth(self):
        text = 'himself did not know herself.'

        result = gender_bend(text)
        self.assertEqual(result, 'herself did not know himself.')

    def test_preserves_case(self):
        text = 'himself did not know Herself.'

        result = gender_bend(text)
        self.assertEqual(result, 'herself did not know Himself.')

    def test_word_with_period(self):
        text = 'Mr. Jones is back!'

        result = gender_bend(text)
        self.assertEqual(result, 'Ms. Jones is back!')

    def test_plural(self):
        text = 'Attention Ladies and Gentlemen'

        result = gender_bend(text)
        self.assertEqual(result, 'Attention Gentlemen and Ladies')

    def test_unidirectional_flip(self):
        # actor is ambiguous (without context, which is how this algorithm
        # operates) so it is not flipped.
        text = 'The actor talked to the actress'

        result = gender_bend(text)
        self.assertEqual(result, 'The actor talked to the actor')

    def test_multi_word_replacement(self):
        text = 'she was one of many freshmen in the class'

        result = gender_bend(text)
        self.assertEqual(result, 'he was one of many first year students in '
                                 'the class')

    def test_flip_word_with_apostrophe(self):
        text = 'the Queen\'s got a picture of this island'

        result = gender_bend(text)
        self.assertEqual(result, 'the King\'s got a picture of this island')

    def test_no_change(self):
        text = 'A column of spray wetted them.'

        result = gender_bend(text)
        self.assertEqual(result, text)

    def test_basic(self):
        text = 'If Ivanka weren\'t my daughter, perhaps I\'d be dating her.'

        result = gender_bend(text)
        self.assertEqual(result, 'If Ivan weren\'t my son, perhaps I\'d be '
                                 'dating him.')

    def test_simon(self):
        text = 'Simon, walking in front of Ralph, felt a flicker of incredulity'

        result = gender_bend(text)
        self.assertEqual(result, 'Simone, walking in front of Rachael, felt a '
                                 'flicker of incredulity')

    def test_third_person_singular_declensions_0(self):
        text = 'her last drop was for her'

        result = gender_bend(text)
        self.assertEqual(result, 'his last drop was for him')

    def test_third_person_singular_declensions_1(self):
        text = 'By her own hand was her sword crafted for her'

        result = gender_bend(text)
        self.assertEqual(result, 'By his own hand was his sword crafted for him')

    def test_third_person_singular_declensions_2(self):
        text = 'It was created by her very quickly'

        result = gender_bend(text)
        self.assertEqual(result, 'It was created by him very quickly')

    def test_third_person_singular_declensions_3(self):
        text = 'It was created by her very own child'

        result = gender_bend(text)
        self.assertEqual(result, 'It was created by his very own child')

    def test_hers(self):
        text = 'the sword is his'

        result = gender_bend(text)
        self.assertEqual(result, 'the sword is hers')

    def test_his(self):
        text = 'the boy glanced over his shoulder'

        result = gender_bend(text)
        self.assertEqual(result, 'the girl glanced over her shoulder')


class TestCopyCase(unittest.TestCase):
    def test_lower_case(self):
        example = 'bonjour'
        result = _copy_case(example, 'hello')

        self.assertEqual(result, 'hello')

    def test_mixed_case(self):
        example = 'Bonjour'
        result = _copy_case(example, 'hello')

        self.assertEqual(result, 'Hello')

    def test_all_caps(self):
        example = 'BONJOUR'
        result = _copy_case(example, 'hello')

        self.assertEqual(result, 'HELLO')
