#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re

from ebooklib import epub
import gender_guesser.detector as gender

def convert_ebook(input_path):
    book = epub.read_epub(input_path)

    for item in book.items:
        # from ipdb import set_trace; set_trace(context=21)
        content = item.content.decode()
        content = re.sub('([Oo])liver', r'\1livia', content)  # TODO: Generalize handling of caps for all words.  Build one single global male <-> female map
        content = content.replace('himself', 'herself')
        item.content = content.encode()

    from ipdb import set_trace; set_trace(context=21)
    # Strangely, when I write it back out, it loses it center styling (at least for
    # the oliver twist ePub.  This happens even if I don't modify it at all.
    epub.write_epub('test.epub', book)

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
            line = fo.readline()
            term_0, term_1 = line.split(',')
            term_0 = term_0.strip()
            term_1 = term_1.strip()
            self.male_to_female.update({term_0: term_1})

        self.female_to_male = {female: male for male, female
                               in self.male_to_female.items()}

    def flip_gender(self, text):
        idx = -1
        while idx < len(text):
            idx += 1
            for term_0, term_1 in {**self.male_to_female,
                                   **self.female_to_male}.items():
                # from ipdb import set_trace; set_trace(context=21)

                match = re.match('({})[^a-zA-Z]'.format(term_0), text[idx:],
                                 re.IGNORECASE)
                if match:
                    current_term = match.group(1)
                    term_1 = _copy_case(current_term, term_1)
                    text = text[:idx] + term_1 + text[idx+len(term_0):]
                    break

        return text


def _copy_case(example_term, term):
    if example_term[0].isupper():
        term = term[0].upper() + term[1:]
    return term


if __name__ == '__main__':
    convert_ebook('oliver_twist.epub')
