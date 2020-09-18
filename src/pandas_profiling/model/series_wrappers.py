import attr


@attr.s
class Sample(object):
    id = attr.ib()
    data = attr.ib()
    name = attr.ib()
    caption = attr.ib(default=None)


class GenericSeries(object):
    def __init__(self, series):
        self.series = series

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

    """

    def __init__(self, series):
        super().__init__(series)
        self.series = series

    @property
    def type(self):
        return self.series.schema.fields[0].dataType

    @property
    def name(self):
        return self.series.columns[0]

    @property
    def empty(self) -> bool:
        return self.n_rows == 0

    def fillna(self, fill=None) -> "GenericSeries":
        if fill is not None:
            return SparkSeries(self.series.na.fill(fill))
        else:
            return SparkSeries(self.series.na.fillna())

    @property
    def n_rows(self) -> int:
        return self.series.count()

    def value_counts(self):
        value_counts = self.series.na.drop().groupBy(self.name).count().toPandas()
        value_counts = value_counts.set_index(self.name, drop=True)
        return value_counts

    def count_na(self):
        return self.series.count() - self.series.na.drop().count()

    def __len__(self):
        return self.n_rows

    def memory_usage(self, deep):
        return self.series.sample(fraction=0.01).toPandas().memory_usage(deep=deep).sum()
