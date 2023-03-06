from csv import DictReader
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Dict, List, TextIO
from . import MedicalData, MedicalItem, Provider

from thefuzz import process
import maya


class CaremarkData(MedicalData):
    _pattern = "caremark_claims\.CSV"

    def process_file(self, input_fp: TextIO) -> List[MedicalItem]:
        items: List[MedicalItem] = []

        for _ in range(3):
            next(input_fp)

        reader = DictReader(input_fp)

        for row in reader:
            if sum(x is not None for x in row.values()) == 1:
                break

            item = self.process_record(row)
            if item is not None:
                items.append(item)
        return items

    def process_record(self, row: Dict) -> MedicalItem:
        """
        Member Name
        Drug Name
        RX #
        Last Filled
        Pharmacy Name
        You Paid
        Your Plan(s) Paid
        Primary Plan Paid
        Secondary Plan Paid
        Manufacturer Discount
        Other Adjustments
        Amount Applied To Deductible
        Amount Funded by HRA
        Amount Funded by FSA
        Coupon Applied
        """

        patient_name = process.extractOne(row["Member Name"], self._ctx["people"])[0]
        svc_date = maya.parse(row["Last Filled"]).date

        try:
            amount = Decimal(row["You Paid"].strip('$'))
        except InvalidOperation:
            amount = Decimal("0")

        return MedicalItem(
            name=patient_name,
            service_date=svc_date,
            category="prescription",
            provider=Provider(organization=row["Pharmacy Name"], name=None),
            patient_amount=amount,
            note=f"{row['Drug Name']} RX#{row['RX #']}",
            source=f"{self.__class__.__name__}:{self._input_file.name}",
        )
