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


def gender_bend(text, interactive_naming=False):
    global _flipper
    if _flipper is None:
        logging.debug('Initializing gender flipping object')
        _flipper = _GenderBender()

    return _flipper.flip_gender(text, interactive_naming)


def gender_bend_epub(input_path, output_path=None, interactive_naming=False):
    if output_path is None:
        base, ext = os.path.splitext(output_path)
        output_path = '{}_gender_bent{}'.format(base, ext)
    book = epub.read_epub(input_path)

    for ii, item in enumerate(book.items):
        logging.debug('Working on epub item {}/{}'.format(ii, len(book.items)-1))
        try:
            content = item.content.decode()
        except UnicodeDecodeError:
            logging.error('Decode Error on book item: %s', ii)
            continue
        content = gender_bend(content, interactive_naming)
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

        try:
            self._nlp = spacy.load('en_core_web_sm')
        except OSError:
            # At the moment, this seems to be the best solution with the requirement of
            # publishing this on PyPI (https://stackoverflow.com/a/55704556/2223706)
            logging.info('Downloading language model for the spaCy POS tagger '
                         '(don\'t worry, this will only happen once)')
            from spacy.cli import download
            download('en_core_web_sm')
            self._nlp = spacy.load('en_core_web_sm')

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

    def flip_gender(self, text, interactive_naming=False):
        # Pad spaces at the ends since our current algorithm relies on findining
        # non-letters to find word boundaries
        text = ' ' + text + ' '
        idx = 0
        while idx < len(text) - 1:
            idx += 1
            WORD_CHAR_REGEX = 'a-zA-Z\''
            if re.match('[{}]'.format(WORD_CHAR_REGEX), text[idx-1]):
                # This is the middle of a word
                continue
            if not re.match('[{}]'.format(WORD_CHAR_REGEX), text[idx]):
                # Not the beginning of a word
                continue

            remaining_text = text[idx:]
            # if re.search('\A[a-zA-Z]', test_text):
            #     # This is the middle of a word
            #     continue
            term = re.split('[^{}]'.format(WORD_CHAR_REGEX), remaining_text, 1)[0]
            # print(term)
            # from ipdb import set_trace; set_trace(context=21)
            # Prevent something like `queen's` from being considered a single
            # word
            term = str(self._nlp(term)[0])
            preceeding_text = text[:idx]
            # previous_term = re.split('[^{}]'.format(WORD_CHAR_REGEX),
            #                          preceeding_text.strip())[-1]
            following_phrase = re.split('[<>.]', text[idx+len(term):], 1)[0]
            # if term.endswith('\'s'):
            #     term = term.strip('\'s')

            # print('Assessing: `{}`'.format(term))
            # from ipdb import set_trace; set_trace(context=21)
            # logging.info('idx %s / %s', idx, len(text))
            if term.lower() in self._term_mapper:
                replacement = self._get_replacement(term, following_phrase)
                text = text[:idx] + replacement + text[idx+len(term):]
                continue

            #####  Flip names ######
            new_name = self.flip_name(text, idx, term, interactive_naming)
            if new_name is not None:
                new_name = _copy_case(term, new_name)
                logging.debug('Replacing name: %s with %s', term, new_name)
                text = text[:idx] + new_name + text[idx+len(term):]
                continue


                # if self._is_proper_noun(text, idx, term)

        # Strip the spaces we introduced at the beginning of function
        return text.strip()

    def flip_name(self, text, idx, term, interactive_naming=False):
        # print(self._not_names)
        if term[0].islower() or term.lower() in self._not_names:
            return None
        # We try a couple different ways to identify if this is a name, since
        # none work perfectly.  Note: false negatives (missing a true name) is
        # much worse than a false positive (thinking a non-name word is name)
        # TODO: Our name detection is still poor... spaCy doesn't work well,
        # should I just get a huge list of names for this purpose?
        doc = self._nlp(term)
        ent_type = doc[0].ent_type_  # TODO: is this working??
        if (ent_type == 'PERSON'
            or term.lower() in self._male_names
            or term.lower() in self._female_names
            or (not ent_type and self._is_proper_noun(text, idx, term))):

            lterm = term.lower()

            if lterm.lower() not in self._name_mapper:
                context = text[idx-40:idx+40]
                orig_gender = self._gender_detector.get_gender(titlecase(lterm))
                logging.debug('name: {} identified as: {}'.format(term, orig_gender))
                # for `mostly_female`/`mostly_male`, we'll just treat it as
                # `female`/`male`.
                orig_gender = orig_gender.lstrip('mostly_')
                if orig_gender == 'andy':
                    # androgynous name, so it can map to itself
                    suggested_name = lterm
                elif orig_gender == 'unknown':
                    suggested_name = None
                else:
                    suggested_name = self._generate_suggested_name(lterm,
                                                                   orig_gender)

                if not interactive_naming and suggested_name is None:
                    return term
                if interactive_naming:
                    input_ = _get_new_name_from_user(term, context, suggested_name)
                    # TODO: this logic belongs in the above function, not here
                    if input_ == 'n':
                        self._not_names.add(lterm)
                        return None
                    elif input_ == 's':
                        name = suggested_name
                    else:
                        name = input_
                else:
                    name = suggested_name
                self._name_mapper[lterm] = name.lower()

            return self._name_mapper[lterm]
        return None

    def _generate_suggested_name(self, orig_name, orig_gender):
        """Chooses a name from the opposite gender with the largest common
        prefix.

        :param str orig_gender: Either `female` or `male`
        :return: the suggested name
        """
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

    def _get_replacement(self, term, following_phrase):
        replacement = self._term_mapper[term.lower()]
        if replacement.lower() == 'him' and self._is_genitive_declension(following_phrase):
            replacement = 'his'
        if replacement.lower() == 'hers' and self._is_genitive_declension(following_phrase):
            replacement = 'her'
        replacement = _copy_case(term, replacement)
        logging.debug('Replacing %s with %s', term, replacement)
        return replacement

    @staticmethod
    def _is_proper_noun(text, idx, term):
        # TODO: need to improve this...
        is_start_of_sentence = not re.search('[a-zA-Z)(][ \n\t]*\Z', text[:idx])

        if is_start_of_sentence:
            # TODO: Poor assumption, but I'll improve this later
            return False

        return term[0].isupper() and len(term[0]) > 1

    def _is_genitive_declension(self, following_phrase):
        doc = self._nlp(following_phrase)
        for term in doc:
            if term.pos_ in {'NOUN', 'DET'}:
                # The "determiner" POS is because you can't have
                # `... by her the dog ...`, you could have though,
                # `... by her the quickest way possible ...`
                return True
            if term.pos_ in {'ADV', 'ADJ'}:
                # Adjectives may preced the object, as in `
                # ... by her very own mother ...`
                continue
            if term.pos_ in {'CCONJ', 'ADP'}:
                # Ex: `... created by her very quickly and ...`
                # (ADP is also a conjunction)
                return False


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
            'Context: {}\n'
            '(suggestion: {})\n'
            '(no translation=n, use suggested name=s) '
            ''.format(colored(old_name, 'red'), colored_context, colored_suggestion)
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
