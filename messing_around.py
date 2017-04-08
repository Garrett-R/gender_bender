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

logging.basicConfig(level=logging.INFO)  # TODO Why does this not work??

def convert_ebook(input_path, out_path):
    book = epub.read_epub(input_path)
    flipper = GenderFlipper()

    for ii, item in enumerate(book.items):
        logging.info('Working on item {}/{}'.format(ii+1, len(book.items)))
        from ipdb import set_trace; set_trace(context=21)
        content = item.content.decode()
        content = re.sub('([Oo])liver', r'\1livia', content)
        content = flipper.flip_gender(content)
        item.content = content.encode()

    # Strangely, when I write it back out, it loses it center styling (at least for
    # the oliver twist ePub.  This happens even if I don't modify it at all.
    epub.write_epub(out_path, book)

class MissingLanguageModelError(Exception):
    pass


class GenderFlipper:
    def __init__(self, language_file='language_models/english'):
        # inflect_engine = inflect.engine()
        self.term_mapper = {}
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
                    self.term_mapper.update({term_0: term_1})
                    if not unidirectional:
                        self.term_mapper.update({term_1: term_0})

                    self.term_mapper.update(
                        {pluralize(term_0): pluralize(term_1)}
                    )
                    if not unidirectional:
                        self.term_mapper.update(
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
            terms = re.split('[^a-zA-Z]', remaining_text, 1)
            target_term = terms[0].lower()

            # print('Assessing: `{}...`'.format(terms[0]))
            # from ipdb import set_trace; set_trace(context=21)
            # logging.info('idx %s / %s', idx, len(text))
            if target_term in self.term_mapper:
                replacement = self.term_mapper[target_term]
                replacement = _copy_case(terms[0], replacement)
                logging.info('Replacing %s with %s', target_term, replacement)
                text = text[:idx] + replacement + text[idx+len(target_term):]

        # Strip the spaces we introduced at the beginning of function
        return text.strip()


def _copy_case(example_term, term):
    if example_term[0].isupper():
        term = term[0].upper() + term[1:]
    if all(char.isupper() for char in example_term):
        term = term.upper()
    return term


if __name__ == '__main__':
    convert_ebook('oliver_twist.epub', 'test1.epub')
