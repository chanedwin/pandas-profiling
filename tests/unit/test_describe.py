import datetime

import numpy as np
import pandas as pd
import pytest

from pandas_profiling import config
from pandas_profiling.model.describe import describe
from pandas_profiling.model.summary import describe_1d
from pandas_profiling.model.typeset import DateTime, Numeric

check_is_NaN = "pandas_profiling.check_is_NaN"


testdata = [
    # Unique values
    (pd.Series([1, 2]), True, 1, 1),
    # Unique values including nan
    (pd.Series([np.nan]), None, None, None),
    # Unique values all nan
    (pd.Series([1, 2, np.nan]), True, 1, 1),
    # Non unique values
    (pd.Series([1, 2, 2]), False, 2 / 3, 1 / 3),
    # Non unique nan
    (pd.Series([1, np.nan, np.nan]), True, 1, 1),
    # Non unique values including nan
    (pd.Series([1, 2, 2, np.nan]), False, 2 / 3, 1 / 3),
    # Non unique values including non unique nan
    (pd.Series([1, 2, 2, np.nan, np.nan]), False, 2 / 3, 1 / 3),
]


@pytest.mark.parametrize("data,is_unique,p_distinct,p_unique", testdata)
def test_describe_unique(data, is_unique, p_distinct, p_unique, summarizer, typeset):
    """Test the unique feature of 1D data"""

    desc_1d = describe_1d(data, summarizer, typeset)
    if is_unique is not None:
        assert desc_1d["p_unique"] == p_unique, "Describe 1D p_unique incorrect"
        assert desc_1d["p_distinct"] == p_distinct, "Describe 1D p_distinct incorrect"
        assert desc_1d["is_unique"] == is_unique, "Describe 1D should return unique"


@pytest.fixture
def recoding_data():
    data = {
        "x": [
            "chien",
            "chien",
            "chien",
            "chien",
            "chat",
            "chat",
            "chameaux",
            "chameaux",
        ],
        "y": ["dog", "dog", "dog", "dog", "cat", "cat", "camel", "camel"],
    }
    df = pd.DataFrame(data)

    return df


@pytest.fixture
def describe_data():
    data = {
        "id": [chr(97 + c) for c in range(1, 9)] + ["d"],
        "x": [50, 50, -10, 0, 0, 5, 15, -3, np.nan],
        "y": [
            0.000001,
            654.152,
            np.nan,
            15.984512,
            3122,
            -3.1415926535,
            111,
            15.9,
            13.5,
        ],
        "cat": [
            "a",
            "long text value",
            u"Élysée",
            "",
            None,
            "some <b> B.s </div> </div> HTML stuff",
            "c",
            "c",
            "c",
        ],
        "s1": np.ones(9),
        "s2": [u"some constant text $ % value {obj} " for _ in range(1, 10)],
        "somedate": [
            datetime.date(2011, 7, 4),
            datetime.datetime(2022, 1, 1, 13, 57),
            datetime.datetime(1990, 12, 9),
            np.nan,
            datetime.datetime(1990, 12, 9),
            datetime.datetime(1950, 12, 9),
            datetime.datetime(1898, 1, 2),
            datetime.datetime(1950, 12, 9),
            datetime.datetime(1950, 12, 9),
        ],
        "bool_tf": [True, True, False, True, False, True, True, False, True],
        "bool_tf_with_nan": [
            True,
            False,
            False,
            False,
            False,
            True,
            True,
            False,
            np.nan,
        ],
        "bool_01": [1, 1, 0, 1, 1, 0, 0, 0, 1],
        "bool_01_with_nan": [1, 0, 1, 0, 0, 1, 1, 0, np.nan],
        "list": [
            [1, 2],
            [1, 2],
            [1, 2],
            [1, 2],
            [1, 2],
            [1, 2],
            [1, 2],
            [1, 2],
            [1, 2],
        ],
        "mixed": [1, 2, "a", 4, 5, 6, 7, 8, 9],
        "dict": [
            {"a": "a"},
            {"b": "b"},
            {"c": "c"},
            {"d": "d"},
            {"e": "e"},
            {"f": "f"},
            {"g": "g"},
            {"h": "h"},
            {"i": "i"},
        ],
        "tuple": [
            (1, 2),
            (3, 4),
            (5, 6),
            (7, 8),
            (9, 10),
            (11, 12),
            (13, 14),
            (15, 16),
            (17, 18),
        ],
    }
    return data


@pytest.fixture
def expected_results():
    return {
        "id": {
            "25%": check_is_NaN,
            "5%": check_is_NaN,
            "50%": check_is_NaN,
            "75%": check_is_NaN,
            "95%": check_is_NaN,
            "count": 9,
            "cv": check_is_NaN,
            "n_distinct": 8,
            "histogram": check_is_NaN,
            "iqr": check_is_NaN,
            "is_unique": False,
            "kurtosis": check_is_NaN,
            "mad": check_is_NaN,
            "max": check_is_NaN,
            "mean": check_is_NaN,
            "min": check_is_NaN,
            "mini_histogram": check_is_NaN,
            "n_missing": 0,
            "p_missing": 0.0,
            "p_distinct": 0.88888888,
            "p_zeros": check_is_NaN,
            "range": check_is_NaN,
            "skewness": check_is_NaN,
            "std": check_is_NaN,
            "sum": check_is_NaN,
            "variance": check_is_NaN,
        },
        "x": {
            "25%": -0.75,
            "5%": -7.5499999999999989,
            "50%": 2.5,
            "75%": 23.75,
            "95%": 50.0,
            "count": 8,
            "n_infinite": 0,
            "p_infinite": 0,
            "cv": 1.771071190261633,
            "n_distinct": 6,
            "iqr": 24.5,
            "is_unique": False,
            "kurtosis": -0.50292858929003803,
            "mad": 9.0,
            "max": 50.0,
            "mean": 13.375,
            "min": -10.0,
            "n_missing": 1,
            "p_missing": 0.11111111111111116,
            "p_distinct": 6 / 8,
            "n": 9,
            "n_zeros": 2,
            "p_zeros": 0.2222222222222222,
            "range": 60.0,
            "skewness": 1.0851622393567653,
            "std": 23.688077169749342,
            "sum": 107.0,
            "variance": 561.125,
        },
        "y": {
            "25%": 10.125000249999999,
            "5%": -2.0420348747749997,
            "50%": 15.942256,
            "75%": 246.78800000000001,
            "95%": 2258.2531999999987,
            "count": 8,
            "n_infinite": 0,
            "p_infinite": 0,
            "cv": 2.2112992878833846,
            "n_distinct": 8,
            "iqr": 236.66299975000001,
            "is_unique": True,
            "kurtosis": 6.974137018717359,
            "mad": 17.51305182675,
            "max": 3122.0,
            "mean": 491.17436504331249,
            "min": -3.1415926535000001,
            "n_missing": 1,
            "p_missing": 0.11111111111111116,
            "p_distinct": 1,
            "n_zeros": 0,
            "p_zeros": 0.0,
            "range": 3125.1415926535001,
            "skewness": 2.6156591135729266,
            "std": 1086.1335236468506,
            "sum": 3929.3949203464999,
            "variance": 1179686.0311895239,
        },
        "cat": {
            "25%": check_is_NaN,
            "5%": check_is_NaN,
            "50%": check_is_NaN,
            "75%": check_is_NaN,
            "95%": check_is_NaN,
            "count": 8,
            "cv": check_is_NaN,
            "n_distinct": 6,
            "histogram": check_is_NaN,
            "iqr": check_is_NaN,
            "is_unique": False,
            "kurtosis": check_is_NaN,
            "mad": check_is_NaN,
            "max": check_is_NaN,
            "mean": check_is_NaN,
            "min": check_is_NaN,
            "mini_histogram": check_is_NaN,
            "n_missing": 1,
            "p_missing": 0.11111111111111116,
            "p_distinct": 6 / 8,
            "p_zeros": check_is_NaN,
            "range": check_is_NaN,
            "skewness": check_is_NaN,
            "std": check_is_NaN,
            "sum": check_is_NaN,
            "variance": check_is_NaN,
        },
        "s1": {
            "25%": 1.0,
            "5%": 1.0,
            "50%": 1.0,
            "75%": 1.0,
            "95%": 1.0,
            "count": 9,
            "cv": 0,
            "iqr": 0,
            "is_unique": False,
            "kurtosis": 0,
            "mad": 0.0,
            "max": 1.0,
            "mean": 1.0,
            "min": 1.0,
            "n_missing": 0,
            "p_missing": 0.0,
            "n_infinite": 0,
            "n_distinct": 1,
            "p_distinct": 0.1111111111111111,
            "p_zeros": 0,
            "range": 0,
            "skewness": 0,
            "std": 0,
            "sum": 9,
            "variance": 0.0,
            "mode": 1.0,
            "monotonic_increase": True,
            "monotonic_increase_strict": False,
        },
        "s2": {
            "25%": check_is_NaN,
            "5%": check_is_NaN,
            "50%": check_is_NaN,
            "75%": check_is_NaN,
            "95%": check_is_NaN,
            "count": 9,
            "cv": check_is_NaN,
            "n_distinct": 1,
            "histogram": check_is_NaN,
            "iqr": check_is_NaN,
            "is_unique": False,
            "kurtosis": check_is_NaN,
            "mad": check_is_NaN,
            "max": check_is_NaN,
            "mean": check_is_NaN,
            "min": check_is_NaN,
            "mini_histogram": check_is_NaN,
            "n_missing": 0,
            "p_missing": 0.0,
            "p_distinct": 0.1111111111111111,
            "p_zeros": check_is_NaN,
            "range": check_is_NaN,
            "skewness": check_is_NaN,
            "std": check_is_NaN,
            "sum": check_is_NaN,
            "variance": check_is_NaN,
        },
        "somedate": {
            "25%": check_is_NaN,
            "5%": check_is_NaN,
            "50%": check_is_NaN,
            "75%": check_is_NaN,
            "95%": check_is_NaN,
            "count": 8,
            "cv": check_is_NaN,
            "n_distinct": 5,
            "iqr": check_is_NaN,
            "is_unique": False,
            "kurtosis": check_is_NaN,
            "mad": check_is_NaN,
            "max": datetime.datetime(2022, 1, 1, 13, 57),
            "mean": check_is_NaN,
            "min": datetime.datetime(1898, 1, 2),
            "n_missing": 1,
            "p_missing": 0.11111111111111116,
            "p_distinct": 5 / 8,
            "p_zeros": check_is_NaN,
            "range": datetime.timedelta(45289, hours=13, minutes=57),
            "skewness": check_is_NaN,
            "std": check_is_NaN,
            "sum": check_is_NaN,
        },
        "bool_tf": {
            "25%": check_is_NaN,
            "5%": check_is_NaN,
            "50%": check_is_NaN,
            "75%": check_is_NaN,
            "95%": check_is_NaN,
            "count": 9,
            "cv": check_is_NaN,
            "n_distinct": 2,
            "histogram": check_is_NaN,
            "iqr": check_is_NaN,
            "is_unique": False,
            "kurtosis": check_is_NaN,
            "mad": check_is_NaN,
            "max": check_is_NaN,
            "min": check_is_NaN,
            "mini_histogram": check_is_NaN,
            "n_missing": 0,
            "p_missing": 0,
            "p_distinct": 2 / 9,
            "p_zeros": check_is_NaN,
            "range": check_is_NaN,
            "skewness": check_is_NaN,
            "std": check_is_NaN,
            "sum": check_is_NaN,
            "variance": check_is_NaN,
        },
        "bool_tf_with_nan": {
            "25%": check_is_NaN,
            "5%": check_is_NaN,
            "50%": check_is_NaN,
            "75%": check_is_NaN,
            "95%": check_is_NaN,
            "n": 9,
            "count": 8,
            "cv": check_is_NaN,
            "n_distinct": 2,
            "histogram": check_is_NaN,
            "iqr": check_is_NaN,
            "is_unique": False,
            "kurtosis": check_is_NaN,
            "mad": check_is_NaN,
            "max": check_is_NaN,
            "min": check_is_NaN,
            "mini_histogram": check_is_NaN,
            "n_missing": 1,
            "p_missing": 1 / 9,
            "p_distinct": 2 / 9,
            "p_zeros": check_is_NaN,
            "range": check_is_NaN,
            "skewness": check_is_NaN,
            "std": check_is_NaN,
            "sum": check_is_NaN,
            "variance": check_is_NaN,
        },
        "bool_01": {
            "5%": 0,
            "25%": 0,
            "50%": 1.0,
            "75%": 1,
            "95%": 1,
            "n": 9,
            "count": 9,
            "cv": 0.9486832980505138,
            "n_distinct": 2,
            "iqr": 1.0,
            "is_unique": False,
            "mad": 0,
            "max": 1,
            "min": 0,
            "n_missing": 0,
            "p_missing": 0,
            "p_distinct": 2 / 9,
            "p_zeros": 4 / 9,
            "sum": 5,
        },
        "bool_01_with_nan": {
            "5%": 0,
            "25%": 0,
            "50%": 0,
            "75%": 1,
            "95%": 1,
            "n": 9,
            "count": 8,
            "cv": 1.3801311186847085,
            "n_distinct": 2,
            "iqr": 1.0,
            "is_unique": False,
            "kurtosis": -2.24,
            "mad": 0.0,
            "max": 1,
            "min": 0,
            "n_missing": 1,
            "p_missing": 0.11111111111111116,
            "p_distinct": 2 / 8,
            "n_zeros": 5,
            "p_zeros": 5 / 9,
            "range": 1.0,
            "skewness": 0.6440611887195306,
            "std": 0.5175491695067657,
            "sum": 3.0,
            "variance": 0.26785714285714285,
        },
        "list": {
            "count": 9,
            "n_missing": 0,
            "p_missing": 0,
        },
        "mixed": {
            "count": 9,
            "n_missing": 0,
            "p_missing": 0,
        },
        "dict": {
            "count": 9,
            "n_missing": 0,
            "p_missing": 0,
        },
        "tuple": {
            "count": 9,
            "n_missing": 0,
            "p_missing": 0,
        },
    }


@pytest.mark.parametrize(
    "column",
    [
        "id",
        "x",
        "y",
        "cat",
        "s1",
        "s2",
        "somedate",
        "bool_tf",
        "bool_tf_with_nan",
        "bool_01",
        "bool_01_with_nan",
        "list",
        "mixed",
        "dict",
        "tuple",
    ],
)
def test_describe_df(column, describe_data, expected_results, summarizer, typeset):
    config["vars"]["num"]["low_categorical_threshold"].set(0)
    describe_data_frame = pd.DataFrame({column: describe_data[column]})
    if column == "somedate":
        describe_data_frame["somedate"] = pd.to_datetime(
            describe_data_frame["somedate"]
        )

    results = describe("title", describe_data_frame, summarizer, typeset)

    assert {
        "analysis",
        "table",
        "variables",
        "scatter",
        "correlations",
        "missing",
        "messages",
        "package",
        "sample",
        "duplicates",
    } == set(results.keys()), "Not in results"

    # Loop over variables
    for k, v in expected_results[column].items():
        if v == check_is_NaN:
            assert (
                k not in results["variables"][column]
            ) == True, "Value `{}` for key `{}` in columnumn `{}` is not NaN".format(
                results["variables"][column][k], k, column
            )
        elif isinstance(v, float):
            assert (
                pytest.approx(v) == results["variables"][column][k]
            ), "Value `{}` for key `{}` in columnumn `{}` is not NaN".format(
                results["variables"][column][k], k, column
            )
        else:
            assert (
                v == results["variables"][column][k]
            ), "Value `{}` for key `{}` in columnumn `{}` is not NaN".format(
                results["variables"][column][k], k, column
            )

    if results["variables"][column]["type"] in [Numeric, DateTime]:
        assert (
            "histogram" in results["variables"][column]
        ), f"Histogram missing for column {column}"


def test_describe_empty(summarizer, typeset):
    empty_frame = pd.DataFrame()
    with pytest.raises(ValueError):
        describe("", empty_frame, summarizer, typeset)


def test_describe_list(summarizer, typeset):
    with pytest.raises(AttributeError):
        with pytest.warns(UserWarning):
            describe("", [1, 2, 3], summarizer, typeset)
