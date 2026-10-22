#!/usr/bin/env python3
"""Strict caption location must not turn OCR errors into native clicks."""
import unittest

from verify_offline_export import exact_ocr_caption


def words(*tokens, line='1', block='1'):
    return [{'page_num': '1', 'block_num': block, 'par_num': '1', 'line_num': line,
             'text': token, 'left': 100 + index * 50, 'top': 200, 'width': 40, 'height': 20}
            for index, token in enumerate(tokens)]


class ExactCaptionTests(unittest.TestCase):
    def test_complete_caption_locates_the_union_of_its_visible_words(self):
        self.assertEqual(exact_ocr_caption(words('LEAVE', 'MATCH'), 'LEAVE MATCH'),
                         {'left': 100, 'top': 200, 'width': 90, 'height': 20, 'text': 'LEAVE MATCH'})

    def test_misread_partial_reordered_and_extra_text_cannot_match(self):
        for tokens in [('LEAYE', 'MATCH'), ('LEAVE',), ('MATCH', 'LEAVE'), ('BACK', 'LEAVE', 'MATCH')]:
            with self.subTest(tokens=tokens):
                self.assertIsNone(exact_ocr_caption(words(*tokens), 'LEAVE MATCH'))

    def test_words_on_different_lines_cannot_form_a_caption(self):
        self.assertIsNone(exact_ocr_caption(words('LEAVE') + words('MATCH', line='2'), 'LEAVE MATCH'))

    def test_duplicate_complete_captions_are_ambiguous(self):
        self.assertIsNone(exact_ocr_caption(words('LEAVE', 'MATCH') + words('LEAVE', 'MATCH', block='2'), 'LEAVE MATCH'))

    def test_missing_line_identity_cannot_authorize_a_click(self):
        rows = words('LEAVE', 'MATCH')
        for row in rows:
            row.pop('line_num')
        self.assertIsNone(exact_ocr_caption(rows, 'LEAVE MATCH'))


if __name__ == '__main__':
    unittest.main()
