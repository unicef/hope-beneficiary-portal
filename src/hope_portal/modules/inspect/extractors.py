import abc
import secrets
from dataclasses import dataclass
from datetime import date
from typing import Any

import inflect
from django.utils.translation import gettext_lazy as _

p = inflect.engine()


@dataclass()
class QuestionData:
    question: str
    answer: str
    hint: str


class Extractor(abc.ABC):
    HINT = ""

    def __init__(self, label: str, value: Any, **kwargs: Any) -> None:
        self.label = label
        self.value = value

    @abc.abstractmethod
    def get_questions(self, n: int = 1) -> list[QuestionData]: ...

    def get_question(self) -> QuestionData:
        questions = self.get_questions(1)
        if not questions:
            raise Exception("No part selected")
        return questions[0]


def _valid_letter_indices(value: str) -> list[int]:
    return [i for i, c in enumerate(value) if c.strip()]


class LetterExtractor(Extractor):
    QUESTION = "What is the {ordinal} letter of '{label}'?"
    HINT = ""

    def __init__(self, label: str, value: str) -> None:
        super().__init__(label, value)
        self.selected_index = -1
        self.selected_letter = ""
        self._select_random_letter()

    def _select_random_letter(self) -> None:
        if self.value:
            indices = _valid_letter_indices(self.value)
            if indices:
                self.selected_index = secrets.choice(indices)
                self.selected_letter = self.value[self.selected_index]
                return
        self.selected_index = -1
        self.selected_letter = ""

    def _build_question(self, idx: int) -> QuestionData:
        return QuestionData(
            question=_(self.QUESTION).format(
                ordinal=p.ordinal(idx + 1),  # type: ignore[arg-type]
                label=self.label,
            ),
            answer=self.value[idx],
            hint=self.HINT,
        )

    def get_questions(self, n: int = 1) -> list[QuestionData]:
        if not self.value:
            return []
        indices = _valid_letter_indices(self.value)
        if not indices:
            return []
        count = max(1, min(n, len(indices)))
        picked = secrets.SystemRandom().sample(indices, count)
        return [self._build_question(idx) for idx in picked]

    def iter_all_questions(self) -> list[QuestionData]:
        if not self.value:
            return []
        return [self._build_question(idx) for idx in _valid_letter_indices(self.value)]

    def verify_answer(self, answer: str) -> bool:
        return answer.lower() == self.selected_letter.lower()


class PhoneNumberExtractor(LetterExtractor):
    QUESTION = "What is the {ordinal} digit of '{label}'?"
    HINT = _(
        "Count digits starting right after the leading '+' sign "
        "(the international/country calling code counts as the first digits)."
    )

    def __init__(self, label: str, value: str) -> None:
        super().__init__(label, value)
        if value.startswith("+"):
            self.value = value[1:]


class IbanExtractor(LetterExtractor):
    QUESTION = "What is the {ordinal} character of your '{label}'?"
    HINT = ""

    def __init__(self, label: str, value: str) -> None:
        super().__init__(label, "".join(value.split()))


class DocumentNumberExtractor(LetterExtractor):
    QUESTION = "What is the {ordinal} character of your '{label}'?"
    HINT = ""

    def __init__(self, label: str, value: str) -> None:
        super().__init__(label, "".join(value.split()))


class DateExtractor(Extractor):
    _PARTS: tuple[str, ...] = ("day", "month", "year")

    def __init__(self, label: str, value: date, key: str | None = None) -> None:
        super().__init__(label, value)
        self.selected_part = ""
        self.selected_value = ""
        self._select_random_part()

    def _select_random_part(self) -> None:
        if self.value:
            self.selected_part = secrets.choice(self._PARTS)
            self.selected_value = str(self._part_value(self.selected_part))

    def _part_value(self, part: str) -> int:
        if part == "day":
            return self.value.day
        if part == "month":
            return self.value.month
        return self.value.year

    def _build_question(self, part: str) -> QuestionData:
        part_name = {"day": _("day"), "month": _("month"), "year": _("year")}[part]
        q = _("What is the {part} (as number) of your '{label}'?").format(part=part_name, label=self.label)
        return QuestionData(question=q, answer=str(self._part_value(part)), hint=self.HINT)

    def get_questions(self, n: int = 1) -> list[QuestionData]:
        if not self.value:
            return []
        count = max(1, min(n, len(self._PARTS)))
        picked = secrets.SystemRandom().sample(list(self._PARTS), count)
        return [self._build_question(part) for part in picked]

    def iter_all_questions(self) -> list[QuestionData]:
        """Return one question per date part (day/month/year) — no random sampling."""
        if not self.value:
            return []
        return [self._build_question(part) for part in self._PARTS]

    def verify_answer(self, answer: str) -> bool:
        try:
            return str(answer) == self.selected_value
        except (ValueError, TypeError):
            return False
