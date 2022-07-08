# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
from pathlib import Path
from typing import Dict, Any

import pandas as pd

COL_ORDER = [
    "Filename",
    "Coverage Percent (delta)",
    "Coverage Percent (a)",
    "Coverage Percent (b)",
    "Lines Covered (delta)",
    "Lines Covered (a)",
    "Lines Covered (b)",
    "Lines Missed (delta)",
    "Lines Missed (a)",
    "Lines Missed (b)",
    "Lines Total (delta)",
    "Lines Total (a)",
    "Lines Total (b)",
    "Common Lines",
    "Windows Only Percent",
]


def to_csv(data: Dict[str, Any], dest: Path) -> None:
    """Write data to CSV
    :param data: Data to be written.
    :param dest: Path to write file.
    """
    df = pd.DataFrame.from_dict(data, orient="index")
    df.to_csv(dest, encoding="utf-8", columns=COL_ORDER)


def to_excel(data: Dict[str, Any], dest: Path) -> None:
    """Write data to Excel
    :param data: Data to be written.
    :param dest: Path to write file.
    """
    df = pd.DataFrame.from_dict(data, orient="index")

    # pylint: disable=abstract-class-instantiated
    with pd.ExcelWriter(path=dest, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, columns=COL_ORDER)

        # pylint: disable=no-member
        wb = writer.book
        ws = writer.sheets["Sheet1"]

        # Colorize coverage percentage deltas that exceed 10%
        exceeded = wb.add_format({"bg_color": "#ff5050"})
        ws.conditional_format(
            "B2:B1048576",
            {"type": "cell", "criteria": ">=", "value": 10, "format": exceeded},
        )

        for row_num, value in enumerate(df.iterrows(), 1):
            file = Path(value[0])
            depth = len(file.parts)
            ws.set_row(row_num, None, None, {"level": depth, "hidden": depth > 2})
