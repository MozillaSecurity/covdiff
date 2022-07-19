# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# pylint: disable=too-few-public-methods
import json
import shutil
from argparse import Namespace, ArgumentParser
from logging import getLogger
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Dict, Any

import six
import zstandard
from FTB.CoverageHelper import merge_coverage_data
from google.cloud import storage as gcp_storage
from google.oauth2.service_account import Credentials

LOG = getLogger(__name__)

PLATFORM_CHOICES = (
    "all",
    "macosx",
    "linux",
    "windows",
)


def json_hook(obj: Dict[str, Any]) -> Dict[Any, Any]:
    """Convert empty strings to None"""
    for k, v in six.iteritems(obj):
        if v == "":
            obj[k] = None
    return obj


class BucketException(Exception):
    """Exception for failing to retrieve a bucket"""


class MozCovFetcher:
    """Class for retrieving coverage reports from coverage.moz.tools"""

    def __init__(self, key: Path):
        creds = Credentials.from_service_account_file(str(key))
        self.client = gcp_storage.Client(project=creds.project_id, credentials=creds)

    def download(self, dest: Path, rev: str, platform: str, suite: str = "all") -> None:
        """
        Download a coverage report.
        :param dest: The location to store the coverage report.
        :param rev: The coverage report revision.
        :param platform: The platform the coverage report was performed on.
        :param suite: The test suite used.
        """
        bucket = self.client.get_bucket("relman-code-coverage-prod")
        gcp_path = f"mozilla-central/{rev}/{platform}:{suite}.json.zstd"
        blob = bucket.blob(gcp_path)

        if not blob.exists():
            raise BucketException(f"No report found on GCP at {gcp_path}")

        with open(dest, "wb", encoding="UTF-8") as output:
            with NamedTemporaryFile(suffix=".json.zstd") as report_path:
                blob.download_to_filename(report_path.name)
                LOG.info(f"Downloaded report archive {gcp_path}")
                report_path.seek(0)

                dctx = zstandard.ZstdDecompressor()
                reader = dctx.stream_reader(report_path)
                while True:
                    chunk = reader.read(16384)
                    if not chunk:
                        break
                    output.write(chunk)


def parse_args() -> Namespace:
    """Argument parser"""
    parser = ArgumentParser(description="Fetch coverage report")
    parser.add_argument("key", type=Path, help="Path to service account credentials")
    parser.add_argument("revision", type=Path, help="Coverage report revision")
    parser.add_argument("dest", type=Path, help="Path to store output")
    parser.add_argument("--suite", default=["all"], nargs="+", help="Test suite")
    parser.add_argument(
        "--platform",
        default="all",
        choices=PLATFORM_CHOICES,
        help="Test platform",
    )

    args = parser.parse_args()

    if args.key and not args.key.is_file():
        parser.error("Could not locate service account credentials!")

    return args


def main(args: Optional[Namespace] = None) -> int:
    """Compare coverage reports
    :param args:
    """

    if args is None:
        args = parse_args()

    fetcher = MozCovFetcher(args.key)

    for idx, suite in enumerate(args.suite):
        with NamedTemporaryFile(suffix=".json.zstd") as file:
            temp_path = Path(file.name)
            fetcher.download(
                temp_path,
                args.revision,
                args.platform,
                suite,
            )
            if idx == 0:
                LOG.info(f"Storing {suite} as base")
                shutil.copy(str(temp_path), str(args.dest))
            else:
                r1 = json.loads(args.dest.read_text("UTF-8"), object_hook=json_hook)
                r2 = json.loads(temp_path.read_text("UTF-8"), object_hook=json_hook)
                LOG.info(f"Merging {suite} coverage report into base")
                try:
                    merge_coverage_data(r1, r2)
                except AssertionError:
                    LOG.info(f"Cannot merge {suite} due to name mismatch!")
                args.dest.write_text(json.dumps(r1))

    return 0
