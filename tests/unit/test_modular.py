import pandas as pd
import numpy as np
import pytest

import pandas_profiling


@pytest.fixture
def df():
    df = pd.read_csv(
        "https://data.nasa.gov/api/views/gh4g-9sfh/rows.csv?accessType=DOWNLOAD"
    )
    # Note: Pandas does not support dates before 1880, so we ignore these for this analysis
    df["year"] = pd.to_datetime(df["year"], errors="coerce")

    # Example: Constant variable
    df["source"] = "NASA"

    # Example: Boolean variable
    df["boolean"] = np.random.choice([True, False], df.shape[0])

    # Example: Mixed with base types
    df["mixed"] = np.random.choice([1, "A"], df.shape[0])

    # Example: Highly correlated variables
    df["reclat_city"] = df["reclat"] + np.random.normal(scale=5, size=(len(df)))

    # Example: Duplicate observations
    duplicates_to_add = pd.DataFrame(df.iloc[0:10])
    duplicates_to_add["name"] = duplicates_to_add["name"] + " copy"

    df = df.append(duplicates_to_add, ignore_index=True)
    return df


def test_modular_absent(df):
    profile = df.profile_report(
        title="Modular test",
        samples={"head": 0, "tail": 0},
        correlations={
            "pearson": {"calculate": False},
            "spearman": {"calculate": False},
            "kendall": {"calculate": False},
            "phi_k": {"calculate": False},
            "cramers": {"calculate": False},
            "recoded": {"calculate": False},
        },
        missing_diagrams={
            "matrix": False,
            "bar": False,
            "dendrogram": False,
            "heatmap": False,
        },
    )

    html = profile.to_html()
    assert "Correlations</h1>" not in html
    assert "Sample</h1>" not in html
    assert "Missing values</h1>" not in html


def test_modular_present(df):
    profile = df.profile_report(
        title="Modular test",
        samples={"head": 10, "tail": 10},
        correlations={
            "pearson": {"calculate": True},
            "spearman": {"calculate": True},
            "kendall": {"calculate": True},
            "phi_k": {"calculate": True},
            "recoded": {"calculate": True},
            "cramers": {"calculate": True},
        },
        missing_diagrams={
            "matrix": True,
            "bar": True,
            "dendrogram": True,
            "heatmap": True,
        },
    )

    html = profile.to_html()
    assert "Correlations</h1>" in html
    assert "Sample</h1>" in html
    assert "Missing values</h1>" in html
