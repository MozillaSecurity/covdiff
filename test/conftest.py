# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import copy

import pytest


@pytest.fixture
def coverage_file_1():
    return {
        "coverage": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "coveragePercent": 100,
        "linesCovered": 10,
        "linesMissed": 0,
        "linesTotal": 10,
        "name": "xyz.cpp",
    }


@pytest.fixture
def coverage_file_2():
    return {
        "coverage": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "coveragePercent": 0,
        "linesCovered": 0,
        "linesMissed": 0,
        "linesTotal": 0,
        "name": "empty.cpp",
    }


@pytest.fixture
def coverage_directory(coverage_file_1, coverage_file_2):
    return {
        "coveragePercent": 100,
        "linesCovered": 10,
        "linesMissed": 0,
        "linesTotal": 10,
        "name": "abc",
        "children": {"xyz.cpp": coverage_file_1, "empty.cpp": coverage_file_2},
    }


@pytest.fixture
def coverage_data_1(coverage_directory):
    """Return a basic coverage data node"""
    return {
        "coveragePercent": 100,
        "linesCovered": 10,
        "linesMissed": 0,
        "linesTotal": 10,
        "name": "/",
        "children": {"abc": coverage_directory},
    }


@pytest.fixture
def coverage_data_2(coverage_data_1):
    """Slightly modified version of coverage_data_1"""
    data = copy.deepcopy(coverage_data_1)
    for key in ("coveragePercent", "linesCovered", "linesMissed"):
        data[key] = 0
        data["children"]["abc"][key] = 0
        data["children"]["abc"]["children"]["xyz.cpp"][key] = 0

    return data
