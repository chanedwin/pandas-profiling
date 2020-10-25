from abc import ABC, abstractmethod
from functools import lru_cache

import attr

UNWRAPPED_SERIES_WARNING = """Attempting to pass a pandas series directly into a function that takes a wrapped series, 
                     this function will attempt to automatically wrap this in a pandas_profiling series wrapper,
                     but it is better practice to explicitly wrap it with a backend if calling the
                     function directly : ie. 
                     
                     from pandas_profiling.model.series_wrapper import SparkSeries, PandasSeries
                     wrapped_df = SparkSeries(spark_df)
                     
                     and pass that into the function directly """


@attr.s
class Sample(object):
    id = attr.ib()
    data = attr.ib()
    name = attr.ib()
    caption = attr.ib(default=None)


class GenericSeries(ABC):
    def __init__(self, series):
        self.series = series

    @abstractmethod
    def fillna(self, fill=None) -> "GenericSeries":
        raise NotImplementedError("Method not implemented for data type")


class PandasSeries(GenericSeries):
    """
    This class is the abstract layer over

    """

    def __init__(self, series):
        super().__init__(series)
        self.series = series

    def fillna(self, fill=None) -> "PandasSeries":
        if fill is not None:
            return PandasSeries(self.series.fillna(fill))
        else:
            return PandasSeries(self.series.fillna())


class SparkSeries(GenericSeries):
    """
    A lot of optimisations left to do (persisting, caching etc), but when functionality completed

    TO-DO Also SparkSeries does a lot more than PandasSeries now, likely abstraction issue
    TO-DO .na.drop() is called multiple times, can we optimise this?
    """

    def __init__(self, series):
        super().__init__(series)
        self.series = series
        # TO-DO - change profile_report to take persist_bool as a variable for spark-series
        self.persist_bool = True

    @property
    def type(self):
        return self.series.schema.fields[0].dataType

    @property
    def name(self):
        return self.series.columns[0]

    @property
    def empty(self) -> bool:
        return self.n_rows == 0

    @property
    def series_without_na(self):
        """
        Useful wrapper for getting the internal data series but with NAs dropped
        Returns: internal spark series without nans

        """
        return self.series.na.drop()

    def fillna(self, fill=None) -> "SparkSeries":
        if fill is not None:
            return SparkSeries(self.series.na.fill(fill))
        else:
            return SparkSeries(self.series.na.fillna())

    @property
    def n_rows(self) -> int:
        return self.series.count()

    @lru_cache()
    def value_counts(self, keep_na=True):

        from pyspark.sql.functions import array, map_keys, map_values
        from pyspark.sql.types import MapType

        # if series type is dict, handle that separately
        if isinstance(self.series.schema[0].dataType, MapType):
            if keep_na:
                new_df = self.series.groupby(
                    map_keys(self.series[self.name]).alias("key"),
                    map_values(self.series[self.name]).alias("value"),
                ).count()
                value_counts = (
                    new_df.withColumn(self.name, array(new_df["key"], new_df["value"]))
                    .select(self.name, "count")
                    .toPandas()
                )
            else:
                new_df = (
                    self.series.na.drop()
                    .groupby(
                        map_keys(self.series[self.name]).alias("key"),
                        map_values(self.series[self.name]).alias("value"),
                    )
                    .count()
                )
                value_counts = (
                    new_df.withColumn(self.name, array(new_df["key"], new_df["value"]))
                    .select(self.name, "count")
                    .toPandas()
                )
        else:
            if keep_na:
                value_counts = self.series.groupBy(self.name).count().toPandas()
            else:
                value_counts = (
                    self.series.na.drop().groupBy(self.name).count().toPandas()
                )

        value_counts = (
            value_counts.sort_values("count", ascending=False)
            .set_index(self.name, drop=True)
            .squeeze(axis="columns")
        )
        return value_counts

    @lru_cache()
    def count_na(self):
        return self.series.count() - self.series.na.drop().count()

    def __len__(self):
        return self.n_rows

    def memory_usage(self, deep):
        """
        Warning! this memory usage is only a sample
        TO-DO can we make this faster or not use a sample?
        """
        return (
            100
            * self.series.sample(fraction=0.01).toPandas().memory_usage(deep=deep).sum()
        )

    def get_spark_series(self):
        return self.series

    def persist(self):
        if self.persist_bool:
            return self.series.persist()

    def unpersist(self):
        if self.persist_bool:
            return self.series.unpersist()
