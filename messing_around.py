#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

# TODO: loaded from easy format?
male_to_female = {
    'himself': 'herself',
    'Mr.': 'Ms.',
}

female_to_male = {female: male for male, female in male_to_female.items()}

def flip_gender(text):
    idx = 0
    while idx < len(text):
        for term_0, term_1 in {**male_to_female, **female_to_male}.items():
            # from ipdb import set_trace; set_trace(context=21)

            match = re.match('({})[^a-zA-Z]'.format(term_0), text[idx:],
                             re.IGNORECASE)
            if match:
                current_term = match.group(1)
                term_1 = _copy_case(current_term, term_1)
                text = text[:idx] + term_1 + text[idx+len(term_0):]
                idx += 1
                break

        idx += 1

    return text


def _copy_case(example_term, term):
    if example_term[0].isupper():
        term = term[0].upper() + term[1:]
    return term


if __name__ == '__main__':
    convert_ebook('oliver_twist.epub')
