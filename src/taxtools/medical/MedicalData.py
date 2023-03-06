from csv import DictReader
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import logging
from pathlib import Path
import re
from typing import Dict, List, TextIO
from typing_extensions import Self

logger = logging.getLogger(__name__)


@dataclass
class Provider:
    organization: str
    name: str

    def __str__(self):
        if self.name is not None:
            return f"{self.name} at {self.organization}"
        else:
            return self.organization


@dataclass
class MedicalItem:
    name: str
    service_date: date
    category: str
    provider: Provider
    patient_amount: Decimal
    note: str
    source: str


class MedicalData:
    def __init__(self, input_file: Path) -> None:
        self._input_file = input_file

        mo = re.match(r"medical-(\w+)-(.+)", input_file.stem)
        self._person_name = mo.group(1)
        self._file_type = mo.group(2)

        with self._input_file.open("r") as f:
            self._items = self.process_file(f)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} ({self._input_file.name})>"

    def __iter__(self):
        return iter(self._items)

    def process_file(self, input_fp: TextIO) -> List[MedicalItem]:
        items: List[MedicalItem] = []

        reader = DictReader(input_fp)

        for row in reader:
            item = self.process_record(row)
            if item is not None:
                items.append(item)
        return items

    def process_record(self) -> MedicalItem:
        raise NotImplementedError

    @classmethod
    def get_parsers(cls, input_file) -> List[Self]:
        parsers: List[Self] = []

        subcls_patterns = [(subcls, subcls._pattern) for subcls in cls.__subclasses__()]

        for subcls, pattern in subcls_patterns:
            if re.search(pattern, input_file.name):
                parsers.append(subcls(input_file))

        return parsers

    @classmethod
    def set_context(cls, context: Dict):
        cls._ctx = context

    @classmethod
    def get_context(cls) -> Dict:
        return cls._ctx
