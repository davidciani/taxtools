from csv import DictReader
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Dict, List, TextIO
from . import MedicalData, MedicalItem, Provider

import maya
from thefuzz import fuzz, process


class BlueShieldMedicalData(MedicalData):
    _pattern = "bcbs_med_claims\.csv"

    def process_file(self, input_fp: TextIO) -> List[MedicalItem]:
        items: List[MedicalItem] = []

        for _ in range(4):
            next(input_fp)

        reader = DictReader(input_fp)

        for row in reader:
            if row["Group ID"] == "":
                continue

            item = self.process_record(row)
            if item is not None:
                items.append(item)
        return items

    def process_record(self, row: Dict) -> MedicalItem:
        """
        Patient
        Provider Name
        Doctor Name
        Specialty
        Dates of Service
        Patient Responsibility Non-Covered
        Patient Responsibility Deductible
        Patient Responsibility Copay/Coinsurance
        """
        patient_name = process.extractOne(row["Patient"], self._ctx["people"])[0]

        try:
            amount = (
                Decimal(row["Patient Responsibility Non-Covered"])
                + Decimal(row["Patient Responsibility Deductible"])
                + Decimal(row["Patient Responsibility Copay/Coinsurance"])
            )
        except InvalidOperation:
            amount = Decimal("0")

        svc_date = maya.parse(row["Dates of Service"]).date

        if row["Doctor Name"] == "Unavailable":
            doctor_name = None
        else:
            doctor_name = row["Doctor Name"]

        return MedicalItem(
            name=patient_name,
            service_date=svc_date,
            category="facility",
            provider=Provider(organization=row["Provider Name"], name=doctor_name),
            patient_amount=amount,
            note=row["Specialty"],
            source=f"{self.__class__.__name__}:{self._input_file.name}",
        )


class BlueShieldPharmacyData(MedicalData):
    _pattern = "bcbs_pharm_claims\.csv"

    def process_file(self, input_fp: TextIO) -> List[MedicalItem]:
        items: List[MedicalItem] = []

        for _ in range(4):
            next(input_fp)

        reader = DictReader(input_fp)

        for row in reader:

            item = self.process_record(row)
            if item is not None:
                items.append(item)
        return items

    def process_record(self, row: Dict) -> MedicalItem:
        """
        Patient Name
        Drug Name
        Fill Date
        Pharmacy Name
        Prescriber Name
        Deductible Amount
        HRA Reimbursed Amount
        Claim Number
        Patient Responsibility
        FSA Eligible
        Prescription Number (RX #)
        Dispensed Quantity
        Days Supply
        Dosage Form
        Drug Type
        """
        patient_name = process.extractOne(row["Patient Name"], self._ctx["people"])[0]
        svc_date = maya.parse(row["Fill Date"]).date

        try:
            amount = Decimal(row["Patient Responsibility"])
        except InvalidOperation:
            amount = Decimal("0")

        return MedicalItem(
            name=patient_name,
            service_date=svc_date,
            category="prescription",
            provider=Provider(organization=row["Pharmacy Name"], name=None),
            patient_amount=amount,
            note=f"{row['Drug Name']} RX#{row['Prescription Number (RX #)']}",
            source=f"{self.__class__.__name__}:{self._input_file.name}",
        )
