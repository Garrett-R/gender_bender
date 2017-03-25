#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import logging
import os
import re

from ebooklib import epub
import gender_guesser.detector as gender

logging.basicConfig(level=logging.INFO)

def convert_ebook(input_path, out_path):
    book = epub.read_epub(input_path)
    flipper = GenderFlipper()

    for ii, item in enumerate(book.items):
        logging.info('Working on item {}/{}'.format(ii+1, len(book.items)))
        # from ipdb import set_trace; set_trace(context=21)
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
    def __init__(self, language_file='language_models/english.txt'):
        self.male_to_female = {}
        if not os.path.exists(language_file):
            raise MissingLanguageModelError(
                'Non-existent language model: "{}"'.format(language_file)
            )
        with open(language_file) as fo:
            for line in fo:
                if re.match(' *#', line):
                    continue

                try:
                    term_0, term_1 = line.split(',')
                except ValueError:
                    logging.warning('Invalid line: %s', line)
                    continue
                term_0 = term_0.strip()
                term_1 = term_1.strip()
                self.male_to_female.update({term_0: term_1})

        self.female_to_male = {female: male for male, female
                               in self.male_to_female.items()}

    def flip_gender(self, text):
        # Note that idx is incremented immediately, so we actually miss the very
        # first word, of each epub segment, but that's unlikely to be a real
        # word anywway
        idx = 0
        while idx < len(text):
            idx += 1
            # from ipdb import set_trace; set_trace(context=21)
            # logging.info('idx %s / %s', idx, len(text))
            for term_0, term_1 in {**self.male_to_female,
                                   **self.female_to_male}.items():
                # from ipdb import set_trace; set_trace(context=21)
                regex = '[^a-zA-Z]({})[^a-zA-Z]'.format(re.escape(term_0))
                match = re.match(regex, text[idx-1:], re.IGNORECASE)
                if match:
                    # from ipdb import set_trace; set_trace(context=21)
                    current_term = match.group(1)
                    term_1 = _copy_case(current_term, term_1)
                    logging.info('Replacing %s with %s', current_term, term_1)
                    text = text[:idx] + term_1 + text[idx+len(term_0):]
                    break

        return text


def _copy_case(example_term, term):
    if example_term[0].isupper():
        term = term[0].upper() + term[1:]
    return term


if __name__ == '__main__':
    convert_ebook('oliver_twist.epub', 'test1.epub')
