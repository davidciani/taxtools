#!/usr/bin/env python

import argparse
import logging
from csv import DictReader
from datetime import date, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

header = """V042
ATaxTool Donations 0.3
D{date:%Y-%m-%d}
^
"""

record_layout_1 = """TD
N280
C1
L1
${amount:0.2f}
X{payee} ({ein})
^
"""

record_layout_2 = """TD
N280
C1
L1
${amount:0.2f}
X {payee}/{note} ({ein})
^
"""


def main(args):

    input_file = Path(args.input).resolve(strict=True)
    logger.info(f"Input file: {input_file}")

    if args.output is None:
        output_file = input_file.with_stem(
            input_file.stem + f"_{datetime.now():%Y%m%d_%H%M%S}"
        ).with_suffix(".txf")
    else:
        output_file = Path(args.output).resolve()
    logger.info(f"Output file: {output_file}")

    with input_file.open("r") as f:
        records = list(DictReader(f))

    with output_file.open("x", newline="\r\n") as f:
        f.write(header.format(date=date.today()))
        for record in records:
            if float(record["amount"]) > 0:
                if record["notes"] != "":
                    f.write(
                        record_layout_2.format(
                            payee=record["payee"],
                            ein=record["ein"],
                            note=record["notes"],
                            amount=-float(record["amount"]),
                        )
                    )
                else:
                    f.write(
                        record_layout_1.format(
                            payee=record["payee"],
                            ein=record["ein"],
                            amount=-float(record["amount"]),
                        )
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input CSV file")
    parser.add_argument("-o", "--output", help="File to write TXF output to")

    main(parser.parse_args())
