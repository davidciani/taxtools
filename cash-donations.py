#!/usr/bin/env python

from csv import DictReader

header = """V042
A TaxTool Donations 0.3
D 04/13/2019
^
"""

record_layout_1 = """TD
N280
C1
L1
${amount:0.2f}
X {payee} ({ein})
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


def main():
    print(header)
    with open("cash-charity-2018.csv") as f:
        rdr = DictReader(f)
        for record in rdr:
            if record["Notes"] is not "":
                print(
                    record_layout_2.format(
                        payee=record["Payee"],
                        ein=record["EIN"],
                        note=record["Notes"],
                        amount=-float(record["2018"]),
                    )
                )
            else:
                print(
                    record_layout_1.format(
                        payee=record["Payee"],
                        ein=record["EIN"],
                        amount=-float(record["2018"]),
                    )
                )


if __name__ == "__main__":
    main()
