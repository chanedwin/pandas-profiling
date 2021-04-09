"""Compute statistical description of datasets."""

import multiprocessing
import multiprocessing.pool
import warnings
from collections import Counter
from functools import singledispatch
from typing import Callable, Mapping, Tuple

import numpy as np
import pandas as pd

from pandas_profiling.config import config as config
from pandas_profiling.model.dataframe_wrappers import (
    UNWRAPPED_DATAFRAME_WARNING,
    GenericDataFrame,
    PandasDataFrame,
    SparkDataFrame,
    get_appropriate_wrapper,
)
from pandas_profiling.model.messages import (
    check_correlation_messages,
    check_table_messages,
    check_variable_messages,
)
from pandas_profiling.model.summarizer import BaseSummarizer
from pandas_profiling.model.typeset import (
    SparkBoolean,
    SparkCategorical,
    SparkNumeric,
    SparkUnsupported,
    Unsupported,
)
from pandas_profiling.visualisation.missing import (
    missing_bar,
    missing_dendrogram,
    missing_heatmap,
    missing_matrix,
)
from pandas_profiling.visualisation.plot import scatter_pairwise, spark_scatter_pairwise


@singledispatch
def describe_1d(series, summarizer: BaseSummarizer, typeset) -> dict:
    """Describe a series (infer the variable type, then calculate type-specific values).

    Args:
        series: The Series to describe.

    Returns:
        A Series containing calculated series description values.
    """
    raise NotImplementedError("Method is not implemented for dtype")


@describe_1d.register(pd.Series)
def _describe_1d_pandas(series: pd.Series, summarizer: BaseSummarizer, typeset) -> dict:
    """Describe a series (infer the variable type, then calculate type-specific values).

    Args:
        series: The Series to describe.

    Returns:
        A Series containing calculated series description values.
    """

    # Make sure pd.NA is not in the series, final .series call is to unwrap the series to get back our pd.Series
    series = series.fillna(np.nan)

    # get `infer_dtypes` (bool) from config
    infer_dtypes = config["infer_dtypes"].get(bool)
    if infer_dtypes:
        # Infer variable types
        vtype = typeset.infer_type(series)
        series = typeset.cast_to_inferred(series)
    else:
        # Detect variable types from pandas dataframe (df.dtypes). [new dtypes, changed using `astype` function are now considered]
        vtype = typeset.detect_type(series)

    # engine must be pandas here due to singledispatch logic
    return summarizer.summarize(series, engine="pandas", dtype=vtype)


def sort_column_names(dct: Mapping, sort: str):
    sort = sort.lower()
    if sort.startswith("asc"):
        dct = dict(sorted(dct.items(), key=lambda x: x[0].casefold()))
    elif sort.startswith("desc"):
        dct = dict(reversed(sorted(dct.items(), key=lambda x: x[0].casefold())))
    elif sort != "none":
        raise ValueError('"sort" should be "ascending", "descending" or "None".')
    return dct


@singledispatch
def get_series_descriptions(df: GenericDataFrame, summarizer, typeset, pbar):
    raise NotImplementedError(
        f"get_table_stats is not implemented for datatype {type(df)}"
    )


@get_series_descriptions.register(PandasDataFrame)
def _get_series_descriptions_pandas(df: PandasDataFrame, summarizer, typeset, pbar):
    def multiprocess_1d(args) -> Tuple[str, dict]:
        """Wrapper to process series in parallel.

        Args:
            column: The name of the column.
            series: The series values.

        Returns:
            A tuple with column and the series description.
        """
        column, series = args
        return column, describe_1d(series, summarizer, typeset)

    # check for unwrapped dataframes and warn
    if not isinstance(df, GenericDataFrame):
        warnings.warn(UNWRAPPED_DATAFRAME_WARNING)
        df_wrapper = get_appropriate_wrapper(df)
        df = df_wrapper(df)

    pool_size = config["pool_size"].get(int)

    sort = config["sort"].get(str)

    # Multiprocessing of Describe 1D for each column
    if pool_size <= 0:
        pool_size = 1

    args = [(name, series) for name, series in df.iteritems()]

    series_description = {}

    if pool_size == 1:
        for arg in args:
            pbar.set_postfix_str(f"Describe variable:{arg[0]}")
            column, description = multiprocess_1d(arg)
            series_description[column] = description
            pbar.update()
    else:
        # TODO: use `Pool` for Linux-based systems
        with multiprocessing.pool.ThreadPool(pool_size) as executor:
            for i, (column, description) in enumerate(
                executor.imap_unordered(multiprocess_1d, args)
            ):
                pbar.set_postfix_str(f"Describe variable:{column}")
                series_description[column] = description
                pbar.update()

        # Restore the original order
        series_description = {k: series_description[k] for k in df.columns}

    # Mapping from column name to variable type
    series_description = sort_column_names(series_description, sort)

    return series_description


@get_series_descriptions.register(SparkDataFrame)
def _get_series_descriptions_spark(df: PandasDataFrame, summarizer, typeset, pbar):
    # check for unwrapped dataframes and warn
    if not isinstance(df, GenericDataFrame):
        warnings.warn(UNWRAPPED_DATAFRAME_WARNING)
        df_wrapper = get_appropriate_wrapper(df)
        df = df_wrapper(df)

    sort = config["sort"].get(str)

    schema_column_pairs = [
        {"name": i[0], "type": str(i[1].dataType)} for i in zip(df.columns, df.schema)
    ]

    numeric_cols = {
        pair["name"]
        for pair in filter(
            lambda pair: pair["type"] in SparkNumeric, schema_column_pairs
        )
    }
    categorical_cols = {
        pair["name"]
        for pair in filter(
            lambda pair: pair["type"] in SparkCategorical, schema_column_pairs
        )
    }
    boolean_cols = {
        pair["name"]
        for pair in filter(
            lambda pair: pair["type"] in SparkBoolean, schema_column_pairs
        )
    }
    supported_cols = numeric_cols.union(categorical_cols).union(boolean_cols)
    unsupported_cols = set(df.columns)
    unsupported_cols.difference_update(supported_cols)

    pbar.set_postfix_str(f"Describe variable type: Numeric")
    series_description = summarizer.summarize(
        SparkDataFrame(df.get_spark_df().select(list(numeric_cols))),
        engine=df.engine,
        dtype=SparkNumeric,
    )
    pbar.update(n=len(numeric_cols))

    pbar.set_postfix_str(f"Describe variable type: Categorical")
    series_description.update(
        summarizer.summarize(
            SparkDataFrame(df.get_spark_df().select(list(categorical_cols))),
            engine=df.engine,
            dtype=SparkCategorical,
        )
    )
    pbar.update(n=len(categorical_cols))

    pbar.set_postfix_str(f"Describe variable type: Boolean")
    series_description.update(
        summarizer.summarize(
            SparkDataFrame(df.get_spark_df().select(list(boolean_cols))),
            engine=df.engine,
            dtype=SparkBoolean,
        )
    )
    pbar.update(n=len(boolean_cols))

    pbar.set_postfix_str(f"Describe variable type: Others")
    series_description.update(
        summarizer.summarize(
            SparkDataFrame(df.get_spark_df().select(list(unsupported_cols))),
            engine=df.engine,
            dtype=SparkUnsupported,
        )
    )
    pbar.update(n=len(unsupported_cols))

    # Restore the original order
    series_description = sort_column_names(series_description, sort)

    return series_description


@singledispatch
def get_table_stats(df: GenericDataFrame, variable_stats: dict) -> dict:
    """General statistics for the DataFrame.

    Args:
      df: The DataFrame to describe.
      variable_stats: Previously calculated statistic on the DataFrame.

    Returns:
        A dictionary that contains the table statistics.
    """
    raise NotImplementedError(
        f"get_table_stats is not implemented for datatype {type(df)}"
    )


@get_table_stats.register(PandasDataFrame)
def _get_table_stats_pandas(df: PandasDataFrame, variable_stats: dict) -> dict:
    n = len(df)

    memory_size = df.get_memory_usage(deep=config["memory_deep"].get(bool)).sum()
    record_size = float(memory_size) / n if n > 0 else 0

    table_stats = {
        "n": n,
        "n_var": len(df.columns),
        "memory_size": memory_size,
        "record_size": record_size,
        "n_cells_missing": 0,
        "n_vars_with_missing": 0,
        "n_vars_all_missing": 0,
    }

    for series_summary in variable_stats.values():
        if "n_missing" in series_summary and series_summary["n_missing"] > 0:
            table_stats["n_vars_with_missing"] += 1
            table_stats["n_cells_missing"] += series_summary["n_missing"]
            if series_summary["n_missing"] == n:
                table_stats["n_vars_all_missing"] += 1

    table_stats["p_cells_missing"] = (
        table_stats["n_cells_missing"] / (table_stats["n"] * table_stats["n_var"])
        if table_stats["n"] > 0
        else 0
    )

    # Variable type counts
    table_stats.update(
        {"types": dict(Counter([v["type"] for v in variable_stats.values()]))}
    )

    return table_stats


@get_table_stats.register(SparkDataFrame)
def _get_table_stats_spark(df: SparkDataFrame, variable_stats: dict) -> dict:
    n = len(df)

    memory_size = df.get_memory_usage(deep=config["memory_deep"].get(bool)).sum()
    record_size = float(memory_size) / n if n > 0 else 0

    table_stats = {
        "n": n,
        "n_var": len(df.columns),
        "memory_size": memory_size,
        "record_size": record_size,
        "n_cells_missing": 0,
        "n_vars_with_missing": 0,
        "n_vars_all_missing": 0,
    }

    for series_summary in variable_stats.values():
        if "n_missing" in series_summary and series_summary["n_missing"] > 0:
            table_stats["n_vars_with_missing"] += 1
            table_stats["n_cells_missing"] += series_summary["n_missing"]
            if series_summary["n_missing"] == n:
                table_stats["n_vars_all_missing"] += 1

    table_stats["p_cells_missing"] = table_stats["n_cells_missing"] / (
        table_stats["n"] * table_stats["n_var"]
    )

    supported_columns = [
        k for k, v in variable_stats.items() if v["type"] != SparkUnsupported
    ]
    table_stats["n_duplicates"] = (
        df.get_duplicate_rows_count(subset=supported_columns)
        if len(supported_columns) > 0
        else 0
    )
    table_stats["p_duplicates"] = (
        (table_stats["n_duplicates"] / len(df))
        if (len(supported_columns) > 0 and len(df) > 0)
        else 0
    )

    # Variable type counts
    table_stats.update(
        {"types": dict(Counter([v["type"] for v in variable_stats.values()]))}
    )

    return table_stats


@singledispatch
def get_missing_diagrams(df: GenericDataFrame, table_stats: dict) -> dict:
    """Gets the rendered diagrams for missing values.

    Args:
        table_stats: The overall statistics for the DataFrame.
        df: The DataFrame on which to calculate the missing values.

    Returns:
        A dictionary containing the base64 encoded plots for each diagram that is active in the config (matrix, bar, heatmap, dendrogram).
    """
    raise NotImplementedError(
        f"get_missing_diagrams is not implemented for datatype {type(df)}"
    )


@get_missing_diagrams.register(PandasDataFrame)
def _get_missing_diagrams_pandas(df: PandasDataFrame, table_stats: dict) -> dict:

    if len(df) == 0:
        return {}

    def warn_missing(missing_name, error):
        warnings.warn(
            f"""There was an attempt to generate the {missing_name} missing values diagrams, but this failed.
    To hide this warning, disable the calculation
    (using `df.profile_report(missing_diagrams={{"{missing_name}": False}}`)
    If this is problematic for your use case, please report this as an issue:
    https://github.com/pandas-profiling/pandas-profiling/issues
    (include the error message: '{error}')"""
        )

    def missing_diagram(name) -> Callable:
        return {
            "bar": missing_bar,
            "matrix": missing_matrix,
            "heatmap": missing_heatmap,
            "dendrogram": missing_dendrogram,
        }[name]

    missing_map = {
        "bar": {
            "min_missing": 0,
            "name": "Count",
            "caption": "A simple visualization of nullity by column.",
        },
        "matrix": {
            "min_missing": 0,
            "name": "Matrix",
            "caption": "Nullity matrix is a data-dense display which lets you quickly visually pick out patterns in data completion.",
        },
        "heatmap": {
            "min_missing": 2,
            "name": "Heatmap",
            "caption": "The correlation heatmap measures nullity correlation: how strongly the presence or absence of one variable affects the presence of another.",
        },
        "dendrogram": {
            "min_missing": 1,
            "name": "Dendrogram",
            "caption": "The dendrogram allows you to more fully correlate variable completion, revealing trends deeper than the pairwise ones visible in the correlation heatmap.",
        },
    }

    missing_map = {
        name: settings
        for name, settings in missing_map.items()
        if config["missing_diagrams"][name].get(bool)
        and table_stats["n_vars_with_missing"] >= settings["min_missing"]
    }
    missing = {}

    if len(missing_map) > 0:
        for name, settings in missing_map.items():
            try:
                if name != "heatmap" or (
                    table_stats["n_vars_with_missing"]
                    - table_stats["n_vars_all_missing"]
                    >= settings["min_missing"]
                ):
                    missing[name] = {
                        "name": settings["name"],
                        "caption": settings["caption"],
                        "matrix": missing_diagram(name)(df),
                    }
            except ValueError as e:
                warn_missing(name, e)

    return missing


@get_missing_diagrams.register(SparkDataFrame)
def _get_missing_diagrams_spark(df: SparkDataFrame, table_stats: dict) -> dict:
    """
    awaiting missingno submission

    Args:
        df:
        table_stats:

    Returns:

    """

    def warn_missing(missing_name, error):
        warnings.warn(
            f"""There was an attempt to generate the {missing_name} missing values diagrams, but this failed.
    To hide this warning, disable the calculation
    (using `df.profile_report(missing_diagrams={{"{missing_name}": False}}`)
    If this is problematic for your use case, please report this as an issue:
    https://github.com/pandas-profiling/pandas-profiling/issues
    (include the error message: '{error}')"""
        )

    def missing_diagram(name) -> Callable:
        return {
            "bar": missing_bar,
        }[name]

    missing_map = {
        "bar": {
            "min_missing": 0,
            "name": "Count",
            "caption": "A simple visualization of nullity by column.",
        },
    }

    missing_map = {
        name: settings
        for name, settings in missing_map.items()
        if config["missing_diagrams"][name].get(bool)
        and table_stats["n_vars_with_missing"] >= settings["min_missing"]
    }
    missing = {}

    if len(missing_map) > 0:
        for name, settings in missing_map.items():
            try:
                if name != "heatmap" or (
                    table_stats["n_vars_with_missing"]
                    - table_stats["n_vars_all_missing"]
                    >= settings["min_missing"]
                ):
                    missing[name] = {
                        "name": settings["name"],
                        "caption": settings["caption"],
                        "matrix": missing_diagram(name)(df),
                    }
            except ValueError as e:
                warn_missing(name, e)

    return missing


@singledispatch
def get_scatter_matrix(df, continuous_variables):
    raise NotImplementedError(
        f"get_table_stats is not implemented for datatype {type(df)}"
    )


@get_scatter_matrix.register(PandasDataFrame)
def _get_scatter_matrix_pandas(df, continuous_variables):
    scatter_matrix = {}
    if config["interactions"]["continuous"].get(bool):
        targets = config["interactions"]["targets"].get(list)
        if len(targets) == 0:
            targets = continuous_variables

        scatter_matrix = {x: {y: "" for y in continuous_variables} for x in targets}

        for x in targets:
            for y in continuous_variables:
                if x in continuous_variables:
                    subset_df = df.dropna(subset=[x, y])
                    scatter_matrix[x][y] = scatter_pairwise(
                        subset_df[x], subset_df[y], x, y
                    )

    return scatter_matrix


@get_scatter_matrix.register(SparkDataFrame)
def _get_scatter_matrix_spark(df, continuous_variables):
    scatter_matrix = {}
    if config["interactions"]["continuous"].get(bool):
        targets = config["interactions"]["targets"].get(list)
        if len(targets) == 0:
            targets = continuous_variables

        scatter_matrix = {x: {y: "" for y in continuous_variables} for x in targets}

        df.persist()

        for x in targets:
            for y in continuous_variables:
                if x in continuous_variables:
                    scatter_matrix[x][y] = spark_scatter_pairwise(df, x, y)
    return scatter_matrix


def get_messages(table_stats, series_description, correlations):
    messages = check_table_messages(table_stats)
    for col, description in series_description.items():
        messages += check_variable_messages(col, description)
    messages += check_correlation_messages(correlations)
    messages.sort(key=lambda message: str(message.message_type))
    return messages
