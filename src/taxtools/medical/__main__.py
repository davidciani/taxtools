#!/usr/bin/env python

import argparse
import dataclasses
import io
import logging
from csv import DictWriter
from itertools import chain
from pathlib import Path
from pprint import pprint
from typing import Dict

import pandas as pd

logging.basicConfig(
    format="%(asctime)s  %(levelname)-8s %(filename)s %(message)s",
    datefmt="%Y-%m-%dT%H-%M-%S",
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)


from . import MedicalData, MedicalItem


def asdict_shallow_str(obj: dataclasses.dataclass) -> Dict:
    return dict(
        (field.name, str(getattr(obj, field.name))) for field in dataclasses.fields(obj)
    )


def main(args):
    print(args.dir_path)

    # MedicalData.set_context(
    #     {
    #         "people": [
    #         ]
    #     }
    # )

    parsers = []
    for child in args.dir_path.iterdir():
        parsers.extend(MedicalData.get_parsers(child))
    pprint(parsers)

    items = list(chain.from_iterable(map(lambda x: x._items, parsers)))

    if args.year:
        items = [i for i in items if i.service_date.year == args.year]

    items_df = pd.DataFrame.from_records([asdict_shallow_str(i) for i in items])
    items_df["provider"] = items_df["provider"].apply(str)

    items_agg = (
        items_df.groupby(
            by=["name", "service_date", "category", "provider", "note", "source"]
        )
        .agg("sum")
        .reset_index()
        .to_dict("records")
    )

    with open(args.output, "w", newline="") as out:
        # out = io.StringIO()
        writer = DictWriter(
            out, MedicalItem.__dataclass_fields__.keys(), extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(items_agg)

        # print(out.getvalue())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract medical data.")
    parser.add_argument(
        "dir_path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="directory to search for medical data",
    )
    parser.add_argument("-o", "--output", help="output file", type=Path)
    parser.add_argument("-y", "--year", help="year", type=int)

    main(parser.parse_args())
