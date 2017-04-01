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

logging.basicConfig(level=logging.INFO)

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
                if re.match(' *#', line):
                    continue

                unidirectional = '=>' in line

                try:
                    terms_0_str, terms_1_str = line.split('=')
                    terms_1_str = terms_1_str.lstrip('>')
                except ValueError:
                    logging.warning('Invalid line: %s', line)
                    continue
                terms_0 = [tt.strip() for tt in terms_0_str.split(',')]
                terms_1 = [tt.strip() for tt in terms_1_str.split(',')]

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
        while idx < len(text):
            idx += 1
            test_text = text[idx-1:]
            if re.search('\A[a-zA-Z]', test_text):
                # This is the middle of a word
                continue
            # print('Assessing: `{}...`'.format(text[idx:idx+10]))
            # from ipdb import set_trace; set_trace(context=21)
            # logging.info('idx %s / %s', idx, len(text))
            for term_0, term_1 in self.term_mapper.items():
                # from ipdb import set_trace; set_trace(context=21)
                regex = '[^a-zA-Z]({})[^a-zA-Z]'.format(re.escape(term_0))
                match = re.match(regex, test_text, re.IGNORECASE)
                if match:
                    current_term = match.group(1)
                    term_1 = _copy_case(current_term, term_1)
                    logging.info('Replacing %s with %s', current_term, term_1)
                    text = text[:idx] + term_1 + text[idx+len(term_0):]
                    break

        # Strip the spaces we introduced at the beginning of function
        return text.strip()


def _copy_case(example_term, term):
    if example_term[0].isupper():
        term = term[0].upper() + term[1:]
    return term


if __name__ == '__main__':
    convert_ebook('oliver_twist.epub', 'test1.epub')
