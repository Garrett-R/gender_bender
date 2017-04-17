# -*- coding: utf-8 -*-
import unittest

from mock import patch

from gender_bender.gender_tools import _copy_case, gender_bend

def mock_get_new_name_from_user(_0, _1, suggested_name):
    # Note: the downside of just returning the suggested_name is that if we
    # update the name list and the suggested name changes, we may have to update
    # some tests.
    return suggested_name


@patch('gender_bender.gender_tools._get_new_name_from_user',
       mock_get_new_name_from_user)
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

    def test_his(self):
        text = 'the boy glanced over his shoulder'

        result = gender_bend(text)
        self.assertEqual(result, 'the girl glanced over her shoulder')

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
