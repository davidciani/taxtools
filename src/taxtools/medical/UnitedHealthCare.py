from csv import DictReader
from datetime import date
from decimal import Decimal
import re
from typing import Dict, List, TextIO
from . import MedicalData, MedicalItem

from thefuzz import fuzz, process
import maya


class UHCData(MedicalData):
    _pattern = "uhc_claims\.csv"

    # def process_file(self, input_fp: TextIO) -> List[MedicalItem]:
    #     items: List[MedicalItem] = []

    #     for _ in range(3):
    #         next(input_fp)

    #     reader = DictReader(input_fp)

    #     for row in reader:
    #         if sum(x is not None for x in row.values()) == 1:
    #             break

    #         item = self.process_record(row)
    #         if item is not None:
    #             items.append(item)
    #     return items

    # Claim Number
    # Date Visited
    # Visited Provider
    # Coverage Type
    # Claim Status
    # Date Processed
    # Total Billed
    # Medicare Approved Amount
    # Medicare Paid
    # Plan Cost-Share
    # Plan Paid
    # Marked as Paid

    def process_record(self, row: Dict) -> MedicalItem:
        patient_name = process.extractOne(self._person_name, self._ctx["people"])[0]
        svc_date = maya.parse(row["Date Visited"]).date

        return MedicalItem(
            name=patient_name,
            service_date=svc_date,
            category="facility",
            provider=re.sub(r"\s+", " ", row["Visited Provider"]),
            patient_amount=Decimal(re.sub("[^\d\.]", "", row["Plan Cost-Share"])),
            note="",
            source=f"{self.__class__.__name__}:{self._input_file.name}",
        )
