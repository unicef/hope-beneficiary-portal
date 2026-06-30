import datetime

import pytest

from hope_portal.modules.inspect.extractors import (
    DateExtractor,
    IbanExtractor,
    LetterExtractor,
    PhoneNumberExtractor,
)


def test_letter_extractor_iter_all_questions_returns_one_per_non_space_character():
    extractor = LetterExtractor("Given name", "Arsen")
    questions = extractor.iter_all_questions()
    assert len(questions) == 5
    assert [q.answer for q in questions] == list("Arsen")


def test_letter_extractor_iter_all_questions_skips_space_characters():
    extractor = LetterExtractor("Given name", "A B")
    questions = extractor.iter_all_questions()
    assert len(questions) == 2
    assert [q.answer for q in questions] == ["A", "B"]


def test_letter_extractor_iter_all_questions_empty_value_returns_empty():
    extractor = LetterExtractor("Given name", "")
    assert extractor.iter_all_questions() == []


def test_phone_extractor_iter_all_questions_strips_leading_plus():
    extractor = PhoneNumberExtractor("Phone", "+48123")
    questions = extractor.iter_all_questions()
    answers = [q.answer for q in questions]
    assert "+" not in answers
    assert "4" in answers


def test_iban_extractor_iter_all_questions_strips_spaces():
    # "PL 61 1090" → spaces removed → "PL611090" (8 chars)
    extractor = IbanExtractor("IBAN", "PL 61 1090")
    questions = extractor.iter_all_questions()
    assert len(questions) == 8
    assert all(q.answer != " " for q in questions)


def test_date_extractor_iter_all_questions_returns_day_month_year():
    extractor = DateExtractor("Birth date", datetime.date(1990, 6, 15))
    questions = extractor.iter_all_questions()
    assert len(questions) == 3
    assert {q.answer for q in questions} == {"15", "6", "1990"}


def test_date_extractor_iter_all_questions_none_value_returns_empty():
    extractor = DateExtractor("Birth date", None)
    assert extractor.iter_all_questions() == []
