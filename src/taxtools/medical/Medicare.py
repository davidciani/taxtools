from datetime import date
from decimal import Decimal, InvalidOperation
from itertools import zip_longest
import logging
from typing import Dict, List
from . import MedicalData, MedicalItem, Provider
import re

from thefuzz import process
from pprint import pformat, pprint
import maya

logger = logging.getLogger(__name__)


class MedicareData(MedicalData):
    _pattern = "medicare_claims\.txt"

    def process_file(self, input_fp) -> List[MedicalItem]:
        items: List[MedicalItem] = []

        input_str = input_fp.read()

        input_str = re.sub("\n{2,}", "\n", input_str)

        SECTION_BREAK = "-" * 32 + "\n"

        sections_raw = re.split(
            r"("
            + SECTION_BREAK
            + r")|(Line number:.*\n)|((?<=Claim Lines for )(?<=Part D\n)Claim Number: .*\n)",
            input_str,
        )

        sections = []
        for section in sections_raw:
            if section == SECTION_BREAK:
                continue
            elif section is None or section.strip() == "":
                continue
            else:
                lines = [
                    [y.strip("$") for y in re.split(":\s+", x)]
                    for x in section.split("\n")
                    if x != ""
                ]
                section_dict = {line[0]: line[1] for line in lines if len(line) == 2}

                if len(section_dict) > 0:
                    sections.append(section_dict)

        edited_sections = []
        current_claim_num = ""
        for section, next_section in zip_longest(sections, sections[1:], fillvalue={}):
            if section.get("skip", False):
                continue

            # Get the current claim number or add it
            if "Claim Number" in section.keys():
                current_claim_num = section["Claim Number"]

            # Skip the psudo claim lines
            if ("Claim Lines for Claim Number" in section.keys()) & (
                ("Claim Number" in next_section.keys())
                | ("Line number" in next_section.keys())
            ):
                continue

            if "Line number" in section.keys():
                section["section_type"] = "line"

                if "Claim Number" not in section.keys():
                    section["Claim Number"] = current_claim_num

                section.update(next_section)
                next_section["skip"] = True

            elif "Claim Type" in section.keys():
                if "Claim Number" not in section.keys():
                    section["Claim Number"] = current_claim_num

                section["section_type"] = "claim"

            edited_sections.append(section)

        cleaned_claims = [
            {
                **x,
                "lines": [
                    y
                    for y in edited_sections
                    if (y.get("section_type") == "line")
                    & (y.get("Claim Number") == x.get("Claim Number"))
                ],
            }
            for x in edited_sections
            if x.get("section_type") == "claim"
        ]

        # pprint(cleaned_claims)

        pii = [x for x in edited_sections if "Name" in x.keys()][0]
        patient_name = process.extractOne(pii["Name"], self._ctx["people"])[0]

        for claim in cleaned_claims:
            match claim:
                case {"Claim Type": "Part D"}:
                    svc_date = maya.parse(claim["Claim Service Date"]).date

                    items.append(
                        MedicalItem(
                            name=patient_name,
                            service_date=svc_date,
                            category="prescription",
                            provider=Provider(
                                organization=claim["Pharmacy Name"], name=None
                            ),
                            patient_amount=None,
                            note=f"{claim['Drug Name']}",
                            source=f"{self.__class__.__name__}:{self._input_file.name}",
                        )
                    )
                case {"Claim Type": "PartB"} | {"Claim Type": "Outpatient"}:

                    for line in claim["lines"]:
                        if line["Date of Service From"] != "":
                            svc_date = maya.parse(line["Date of Service From"]).date
                        else:
                            svc_date = maya.parse(claim["Service Start Date"]).date

                        try:
                            patient_amount = (
                                Decimal(claim["You May be Billed"])
                                * Decimal(line["Allowed Amount"])
                                / Decimal(claim["Medicare Approved"])
                            )
                        except InvalidOperation:
                            patient_amount = Decimal(0)

                        items.append(
                            MedicalItem(
                                name=patient_name,
                                service_date=svc_date,
                                category="facility",
                                provider=Provider(
                                    organization=re.sub(r"\s+", " ", claim["Provider"]),
                                    name=None,
                                ),
                                patient_amount=patient_amount,
                                # note=f"{line.get('Procedure Code/Description','No Description')}; {line.get('Place of Service/Description','No Place of Service')}",
                                note=f"{line.get('Place of Service/Description','No Place of Service')}",
                                source=f"{self.__class__.__name__}:{self._input_file.name}",
                            )
                        )

        return items

    def process_record(self, row: Dict) -> MedicalItem:
        pass
