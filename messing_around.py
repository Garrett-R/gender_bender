#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import itertools
import logging
import os
import re

from ebooklib import epub
import gender_guesser.detector as gender
from pluralize import pluralize
import spacy
from titlecase import titlecase

logging.basicConfig(level=logging.INFO)  # TODO Why does this not work??

def convert_example_str():
    text = 'sat on the rocky ledge, and watched Ralph\'s green and white body enviously'
    flipper = GenderFlipper()
    flipped_text = flipper.flip_gender(text)
    print(flipped_text)

def convert_ebook(input_path, out_path):
    book = epub.read_epub(input_path)
    flipper = GenderFlipper()

    for ii, item in enumerate(book.items):
        logging.info('Working on item {}/{}'.format(ii+1, len(book.items)))
        content = item.content.decode()
        content = flipper.flip_gender(content)
        item.content = content.encode()

    # Strangely, when I write it back out, it loses it center styling (at least for
    # the oliver twist ePub.  This happens even if I don't modify it at all.
    epub.write_epub(out_path, book)


class MissingLanguageModelError(Exception):
    pass


class GenderFlipper:
    def __init__(self, language_file='language_models/english'):
        self._name_mapper = {}
        self._not_names = set()
        self._nlp = spacy.load('en')
        self._term_mapper = {}
        if not os.path.exists(language_file):
            raise MissingLanguageModelError(
                'Non-existent language model: "{}"'.format(language_file)
            )
        with open(language_file) as fo:
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
            if re.match('[a-zA-Z]', text[idx-1]):
                # This is the middle of a word
                continue
            if not re.match('[a-zA-Z]', text[idx]):  # TODO: better regex symbol than this a-zA-Z business?
                # Not the beginning of a word
                continue
            remaining_text = text[idx:]
            # if re.search('\A[a-zA-Z]', test_text):
            #     # This is the middle of a word
            #     continue
            term = re.split('[^a-zA-Z]', remaining_text, 1)[0]
            target_term = term.lower()

            # print('Assessing: `{}...`'.format(term))
            # from ipdb import set_trace; set_trace(context=21)
            # logging.info('idx %s / %s', idx, len(text))
            if target_term in self._term_mapper:
                replacement = self._term_mapper[target_term]
                replacement = _copy_case(term, replacement)
                logging.info('Replacing %s with %s', term, replacement)
                text = text[:idx] + replacement + text[idx+len(target_term):]
                continue

            #####  Flip names ######
            new_name = self.flip_name(text, idx, term)
            if new_name is not None:
                new_name = _copy_case(term, new_name)
                logging.info('Replacing name: %s with %s', term, new_name)
                text = text[:idx] + new_name + text[idx+len(target_term):]
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
                input_ = self._get_new_name_from_user(titlecase(term))
                if input_ == 'n':
                    self._not_names.add(term)
                    return None
                self._name_mapper[term] = input_

            return self._name_mapper[term]
        return None


    @staticmethod
    def _get_new_name_from_user(old_name):
        # TODO: give context and highlight name with color
        while True:
            input_ = input('Select new name for: {}\n'
                           '(not a first name=n) '.format(old_name))
            if (input_ != 'n' and len(input_) < 2) or input_.isspace():
                print('You must input a valid name')
                continue

            return input_


    def _is_proper_noun(self, text, idx, term):
        # TODO: need to improve this...
        is_start_of_sentence = not re.search('[a-zA-Z)(][ \n\t]*\Z', text[:idx])
        if is_start_of_sentence:
            # TODO: Poor assumption, but I'll improve this later
            return False

        return term[0].isupper()


def _copy_case(example_term, term):
    if example_term[0].isupper():
        term = term[0].upper() + term[1:]
    if all(char.isupper() for char in example_term):
        term = term.upper()
    return term


if __name__ == '__main__':
    # convert_example_str()
    convert_ebook('Lord_of_the_Flies.epub', 'Lady_of_the_Flies.epub')
