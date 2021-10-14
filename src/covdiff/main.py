# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import json
import re
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional, Dict, List, Any

from FTB import CoverageHelper
from typing_extensions import TypedDict

from covdiff import writers

DIFF_KEYS = ("coveragePercent", "linesCovered", "linesMissed", "linesTotal")


class _CovReportBase(TypedDict):
    """Base CovReport class with required properties"""

    coveragePercent: int
    linesCovered: int
    linesMissed: int
    linesTotal: int
    name: str


class CovReport(_CovReportBase, total=False):
    """Coverage report class with recursive, optional properties"""

    children: _CovReportBase


def compare(
    report1: CovReport,
    report2: CovReport,
    exclude: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compare coverage reports and record differences in line covered vs missed.
    :param report1: First coverage report.
    :param report2: Second coverage report.
    :param exclude: List of exclusion directives.
    """

    def _walk(a: CovReport, b: CovReport, path: str) -> None:
        if a["name"] is not None:
            path = str(Path(path) / Path(a["name"]))

        results[path] = {"Filename": path}
        for key in DIFF_KEYS:
            cased = re.sub(r"(.)([A-Z][a-z]+)", r"\1 \2", key).title()
            # mypy cannot coerce string to typed dict key literal
            # https://github.com/python/mypy/issues/6262
            results[path][f"{cased} (a)"] = a[key]  # type: ignore
            results[path][f"{cased} (b)"] = b[key]  # type: ignore
            if key == "coveragePercent":
                results[path][f"{cased} (delta)"] = round(
                    a[key] - b[key], 2  # type: ignore
                )
            else:
                results[path][f"{cased} (delta)"] = a[key] - b[key]  # type: ignore

        # ToDo: Parse 'b' keys that don't exist in 'a'
        if "children" in a.keys() and "children" in b.keys():
            for key in sorted(a["children"].keys()):
                if key in b["children"].keys():
                    _walk(a["children"][key], b["children"][key], path)  # type: ignore

    # Apply filters to both reports
    if exclude is not None:
        CoverageHelper.apply_include_exclude_directives(report1, exclude)
        CoverageHelper.apply_include_exclude_directives(report2, exclude)

    results: Dict[str, Any] = {}
    _walk(report1, report2, "/")

    return results


def parse_args() -> Namespace:
    """Argument parser"""
    parser = ArgumentParser(description="Compare two coverage reports")
    parser.add_argument("reports", type=Path, nargs=2, help="Reports to compare")
    parser.add_argument("dest", type=Path, help="Path to store results")
    parser.add_argument(
        "-f", "--filter", type=Path, help="Path to filter list", metavar="FILE"
    )
    args = parser.parse_args()

    for report in args.reports:
        if not report.is_file():
            parser.error("Could not locate supplied coverage reports!")

    if args.filter and not args.filter.is_file():
        parser.error("Could not locate filter file!")

    return args


def main(args: Optional[Namespace] = None) -> int:
    """Compare coverage reports
    :param args:
    """

    if args is None:
        args = parse_args()

    reports = []
    for report in args.reports:
        with open(report, encoding="utf8") as file:
            data = json.load(file)
            reports.append(data)

    exclude = None
    if args.filter is not None:
        with open(args.filter, encoding="utf8") as file:
            exclude = file.read().splitlines()

    diff = compare(reports[0], reports[1], exclude=exclude)
    if args.dest.suffix.lower() == ".csv":
        writers.to_csv(diff, args.dest)
    elif args.dest.suffix.lower() == ".xlsx":
        writers.to_excel(diff, args.dest)

    return 0
