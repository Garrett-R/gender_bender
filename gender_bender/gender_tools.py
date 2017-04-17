#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import itertools
import logging
import os
import re

from ebooklib import epub
import gender_guesser.detector as gender_detector
import spacy
from termcolor import colored
from titlecase import titlecase

from gender_bender.pluralize import pluralize


logging.basicConfig(level=logging.INFO)  # TODO Why does this not work??  Move into __init__.py

# lazy-loaded singleton that's responsible for all the work
_flipper = None


def gender_bend(text):
    global _flipper
    if _flipper is None:
        logging.info('Initializing gender flipping object')
        _flipper = _GenderBender()

    return _flipper.flip_gender(text)


def gender_bend_epub(input_path, output_path=None):
    if output_path is None:
        base, ext = os.path.splitext(output_path)
        output_path = '{}_gender_bent{}'.format(base, ext)
    book = epub.read_epub(input_path)

    for ii, item in enumerate(book.items):
        logging.info('Working on epub item {}/{}'.format(ii, len(book.items)-1))
        try:
            content = item.content.decode()
        except UnicodeDecodeError:
            logging.error('Decode Error on book item: %s', ii)
            continue
        content = gender_bend(content)
        item.content = content.encode()

    # Strangely, when I write it back out, it loses it center styling (at least for
    # the oliver twist ePub.  This happens even if I don't modify it at all.
    epub.write_epub(output_path, book)


class MissingLanguageModelError(Exception):
    pass


# TODO: break into NameFlipper and WordFlipper?
class _GenderBender:
    def __init__(self, language_model='english'):
        self._gender_detector = gender_detector.Detector()
        self._name_mapper = {}
        self._not_names = set()
        self._nlp = spacy.load('en')
        self._term_mapper = {}
        model_dir = os.path.join('gender_bender', 'language_models')
        female_file = os.path.join(model_dir, language_model, 'female_names')
        if not os.path.exists(female_file):
            raise MissingLanguageModelError(
                'Non-existent female name file: "{}"'.format(female_file)
            )
        male_file = os.path.join(model_dir, language_model, 'male_names')
        if not os.path.exists(male_file):
            raise MissingLanguageModelError(
                'Non-existent male name file: "{}"'.format(male_file)
            )
        with open(female_file) as fo:
            self._female_names = [name.strip() for name in fo.readlines()]
        with open(male_file) as fo:
            self._male_names = [name.strip() for name in fo.readlines()]

        word_file = os.path.join(model_dir, language_model, 'words')
        if not os.path.exists(word_file):
            raise MissingLanguageModelError(
                'Non-existent word file: "{}"'.format(word_file)
            )
        with open(word_file) as fo:
            for line in fo:
                # logging.debug('language file line: %s', line)
                if re.match(' *#', line) or re.match(' *\n\Z', line):
                    continue

                unidirectional = '=>' in line

                try:
                    terms_0_str, terms_1_str = line.split('=')
                    terms_1_str = terms_1_str.lstrip('>')
                except ValueError:
                    logging.warning('Invalid line: %s', line)
                    continue
                terms_0 = [tt.strip().lower() for tt in terms_0_str.split(',')]
                terms_1 = [tt.strip().lower() for tt in terms_1_str.split(',')]

                for term_0, term_1 in itertools.product(terms_0, terms_1):
                    self._term_mapper.update({term_0: term_1})
                    if not unidirectional:
                        self._term_mapper.update({term_1: term_0})

                    # avoid `him = her` becoming `them = their`
                    if pluralize(term_0) in {'them', 'their'}:
                        continue

                    self._term_mapper.update(
                        {pluralize(term_0): pluralize(term_1)}
                    )
                    if not unidirectional:
                        self._term_mapper.update(
                            {pluralize(term_1): pluralize(term_0)}
                        )

    def flip_gender(self, text):
        # Pad spaces at the ends since our current algorithm relies on findining
        # non-letters to find word boundaries
        text = ' ' + text + ' '
        idx = 0
        while idx < len(text) - 1:
            idx += 1
            if re.match('[a-zA-Z\']', text[idx-1]):
                # This is the middle of a word
                continue
            if not re.match('[a-zA-Z\']', text[idx]):  # TODO: better regex symbol than this a-zA-Z business?
                # Not the beginning of a word
                continue

            remaining_text = text[idx:]
            # if re.search('\A[a-zA-Z]', test_text):
            #     # This is the middle of a word
            #     continue
            term = re.split('[^a-zA-Z\']', remaining_text, 1)[0]
            # print(term)
            # from ipdb import set_trace; set_trace(context=21)
            # Prevent something like `queen's` from being considered a single
            # word
            term = str(self._nlp(term)[0])
            # if term.endswith('\'s'):
            #     term = term.strip('\'s')

            # print('Assessing: `{}`'.format(term))
            # from ipdb import set_trace; set_trace(context=21)
            # logging.info('idx %s / %s', idx, len(text))
            if term.lower() in self._term_mapper:
                replacement = self._term_mapper[term.lower()]
                replacement = _copy_case(term, replacement)
                logging.debug('Replacing %s with %s', term, replacement)
                text = text[:idx] + replacement + text[idx+len(term):]
                continue

            #####  Flip names ######
            new_name = self.flip_name(text, idx, term)
            if new_name is not None:
                new_name = _copy_case(term, new_name)
                logging.debug('Replacing name: %s with %s', term, new_name)
                text = text[:idx] + new_name + text[idx+len(term):]
                continue


            # if self._is_proper_noun(text, idx, term)

        # Strip the spaces we introduced at the beginning of function
        return text.strip()

    def flip_name(self, text, idx, term):
        if term[0].islower() or term in self._not_names:
            return None

        doc = self._nlp(term)
        ent_type = doc[0].ent_type_
        if (ent_type == 'PERSON' or (ent_type is None and
                                     self._is_proper_noun(text, idx, term))):

            if term not in self._name_mapper:
                context = text[idx-40:idx+40]
                orig_gender = self._gender_detector.get_gender(titlecase(term))
                print('name: {} identified as: {}'.format(term, orig_gender))
                # for `mostly_female`/`mostly_male`, we'll just treat it as
                # `female`/`male`.
                orig_gender = orig_gender.lstrip('mostly_')
                if orig_gender == 'andy':
                    # androgynous name, so it can map to itself
                    suggested_name = term
                elif orig_gender == 'unknown':
                    suggested_name = None
                else:
                    suggested_name = self._generate_suggested_name(term, orig_gender)
                input_ = _get_new_name_from_user(term, context, suggested_name)
                # TODO: this logic belongs in the above function, not here
                if input_ == 'n':
                    self._not_names.add(term)
                    return None
                elif input_ == 's':
                    name = suggested_name
                else:
                    name = input_
                self._name_mapper[term] = name

            return self._name_mapper[term]
        return None

    def _generate_suggested_name(self, orig_name, orig_gender):
        """Chooses a name from the opposite gender with the largest common
        prefix.

        :param str orig_gender: Either `female` or `male`
        :return: the suggested name
        """
        orig_name = orig_name.lower()
        if orig_gender == 'female':
            names = self._male_names
        else:
            names = self._female_names
        suggested_name = None
        for num_chars in range(1, len(orig_name)):
            for name in names:
                if name.startswith(orig_name[:num_chars]):
                    suggested_name = titlecase(name)
                    break
            else:
                # Ok, there's no better match, so we take the last match
                break

        return suggested_name


    @staticmethod
    def _is_proper_noun(text, idx, term):
        # TODO: need to improve this...
        is_start_of_sentence = not re.search('[a-zA-Z)(][ \n\t]*\Z', text[:idx])
        if is_start_of_sentence:
            # TODO: Poor assumption, but I'll improve this later
            return False

        return term[0].isupper()


def _get_new_name_from_user(old_name, context, suggested_name):
    # TODO: suggest multiple options for the name
    colored_context = context.replace(old_name, colored(old_name, 'red'))
    if suggested_name is None:
        colored_suggestion = 'N/A'
    else:
        colored_suggestion = colored(suggested_name, 'green')

    while True:
        input_ = input(
            '-------------------------------------\n'
            'Select new name for: {}   \n'
            '(suggestion: {})\n'
            '(not a first name=n, use suggested name=s) '
            ''.format(colored_context, colored_suggestion)
        )
        if (input_ not in {'n', 's'} and len(input_) < 2) or input_.isspace():
            print('You must input a valid name')
            continue

        return input_


def _copy_case(example_term, term):
    if example_term[0].isupper():
        term = term[0].upper() + term[1:]
    if all(char.isupper() for char in example_term):
        term = term.upper()
    return term
