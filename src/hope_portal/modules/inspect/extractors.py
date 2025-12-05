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
    def get_question(self) -> QuestionData: ...


def pick_random(value: str) -> int:
    for __ in range(len(value) * 2):
        idx = secrets.randbelow(len(value))
        if value[idx].strip():
            return idx
    return -1


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
            self.selected_index = pick_random(self.value)
            self.selected_letter = self.value[self.selected_index]
        else:
            self.selected_index = -1
            self.selected_letter = ""

    def get_question(self) -> QuestionData:
        if self.selected_index != -1:
            return QuestionData(
                question=_(self.QUESTION).format(
                    ordinal=p.ordinal(self.selected_index + 1),  # type: ignore[arg-type]
                    label=self.label,
                ),
                answer=self.selected_letter,
                hint=self.HINT,
            )
        raise Exception("No part selected")

    def verify_answer(self, answer: str) -> bool:
        return answer.lower() == self.selected_letter.lower()


class PhoneNumberExtractor(LetterExtractor):
    QUESTION = "What is the {ordinal} digit of '{label}'?"
    HINT = ""

    def __init__(self, label: str, value: str) -> None:
        super().__init__(label, value)
        if value.startswith("+"):
            self.value = value[1:]


class DateExtractor(Extractor):
    def __init__(self, label: str, value: date, key: str | None = None) -> None:
        super().__init__(label, value)
        self.selected_part = ""
        self.selected_value = ""
        self._select_random_part()

    def _select_random_part(self) -> None:
        if self.value:
            parts = ["day", "month", "year"]
            self.selected_part = secrets.choice(parts)  # noqa: S311
            if self.selected_part == "day":
                self.selected_value = str(self.value.day)
            elif self.selected_part == "month":
                self.selected_value = str(self.value.month)
            else:  # year
                self.selected_value = str(self.value.year)

    def get_question(self) -> QuestionData:
        if self.selected_part:
            part_name = {"day": _("day"), "month": _("month"), "year": _("year")}[self.selected_part]
            q = _("What is the {part} (as number) of your '{label}'?").format(part=part_name, label=self.label)
            return QuestionData(question=q, answer=self.selected_value, hint=self.HINT)
        raise Exception("No part selected")

    def verify_answer(self, answer: str) -> bool:
        try:
            return str(answer) == self.selected_value
        except (ValueError, TypeError):
            return False
