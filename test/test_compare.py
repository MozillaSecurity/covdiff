# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from covdiff.main import compare


def test_compare_simple(coverage_data_1, coverage_data_2):
    """Simple test of compare"""
    diff = compare(coverage_data_1, coverage_data_2)

    for name in ("/", "/abc", "/abc/xyz.cpp"):
        assert diff[name]["Coverage Percent (a)"] == coverage_data_1["coveragePercent"]
        assert diff[name]["Coverage Percent (b)"] == coverage_data_2["coveragePercent"]
        assert diff[name]["Coverage Percent (delta)"] == 100
        assert diff[name]["Lines Covered (a)"] == coverage_data_1["linesCovered"]
        assert diff[name]["Lines Covered (b)"] == coverage_data_2["linesCovered"]
        assert diff[name]["Lines Covered (delta)"] == 10
        assert diff[name]["Lines Missed (a)"] == coverage_data_1["linesMissed"]
        assert diff[name]["Lines Missed (b)"] == coverage_data_2["linesMissed"]
        assert diff[name]["Lines Missed (delta)"] == 0
        assert diff[name]["Lines Total (a)"] == coverage_data_1["linesTotal"]
        assert diff[name]["Lines Total (b)"] == coverage_data_2["linesTotal"]
        assert diff[name]["Lines Total (delta)"] == 0


def test_filter_positive_match(coverage_file_1, coverage_data_1):
    """Test that filter includes files matching positive pattern"""
    diff = compare(coverage_data_1, coverage_data_1)
    exclude = [f"+:**/{coverage_file_1['name']}"]
    diff_with_excluded = compare(coverage_data_1, coverage_data_1, exclude)
    assert diff == diff_with_excluded


def test_filter_negative_match(coverage_file_2, coverage_data_1):
    """Test that filter excludes files matching negative pattern"""
    exclude = [f"-:**/{coverage_file_2['name']}"]
    diff = compare(coverage_data_1, coverage_data_1, exclude)

    match_path = f"/{coverage_data_1['name']}/{coverage_file_2['name']}"
    assert match_path not in diff.keys()
