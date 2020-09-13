import pandas as pd
from typing import List


class GenericDataFrame(object):
    """
    This class is the abstract layer over the backend data types, and describes the functions and attributes
    that need to be implemented to be a valid backend

    """

    def __init__(self):
        # self.df holds the underlying data object
        self.df = None

    def get_columns(self) -> List[str]:
        """
        method to get all the columns in dataframe as a list

        Returns: a list of column names

        """
        raise NotImplemented("Implementation not found")

    def get_count(self) -> int:
        """
        method to get the number of rows in a dataframe as an int

        Returns: number of rows in column

        """
        raise NotImplemented("Implementation not found")

    def is_empty(self) -> bool:
        """
        return True if dataframe is empty, else return false. A dataframe of NaN should not
        evaluate to empty

        Returns: True if dataframe is empty else false

        """
        raise NotImplemented("Implementation not found")

    def get_duplicates(self, subset):
        """
        returns only the duplicated rows in the dataframe. Used for the get_duplicates method

        Args:
            subset: subset of rows to consider

        Returns:

        """
        raise NotImplemented("Implementation not found")

    def dropna(self, subset):
        raise NotImplemented("Implementation not found")

    def groupby_get_n_largest(self, columns, n, remove_duplicates=True):
        return NotImplemented("Implementation not found")

    def get_memory_usage(self, config):
        raise NotImplemented("Implementation not found")

    def __len__(self):
        raise NotImplemented("Implementation not found")

    def __getitem__(self, key):
        raise NotImplemented("Implementation not found")

    def corr(self, method):
        raise NotImplemented("Implementation not found")

    def get_internal_df(self):
        raise NotImplemented("Implementation not found")

    def head(self, n):
        raise NotImplemented("Implementation not found")

    def tail(self, n):
        raise NotImplemented("Implementation not found")


class PandasDataFrame(GenericDataFrame):
    """
    This class is the abstract layer over

    """

    def __init__(self, df):
        super().__init__()
        self.df = df

    @staticmethod
    def validate_same_type(obj):
        """
        Check if pandas dataframe using isinstance. More pythonic way of checking as opposed to spark type check.
        Possible because its cheap to import pandas dataframe type.

        Args:
            obj: check if object is a spark dataframe

        Returns: True if the __module__ and __name__ of object matches spark dataframe, else false

        """
        return isinstance(obj, pd.DataFrame)

    def get_columns(self):
        return self.df.columns

    def get_count(self):
        return len(self.df)

    def is_empty(self):
        return self.df.empty

    def get_duplicates(self, subset, keep="first"):
        return self.df.duplicated(subset=subset, keep=keep)

    def dropna(self, subset):
        return self.df.dropna(subset=subset)

    def groupby_get_n_largest(self, columns, n, remove_duplicates=True):
        if remove_duplicates:
            return (self.df[self.get_duplicates(subset=columns, keep=False)]
                    .groupby(columns)
                    .size()
                    .reset_index(name="count")
                    .nlargest(n, "count"))
        else:
            return (self.df.groupby(columns)
                    .size()
                    .reset_index(name="count")
                    .nlargest(n, "count"))

    def __len__(self):
        return self.get_count()

    def get_memory_usage(self, config):
        return self.df.memory_usage(deep=config["memory_deep"].get(bool)).sum()

    def __getitem__(self, key):
        return self.df[key]

    def corr(self, method):
        return self.df.corr(method=method)

    def get_internal_df(self):
        """
        This function should be deprecated once all functionalities are properly wrapped!!

        Returns:

        """
        return self.df

    def head(self, n):
        return self.df.head(n=n)

    def tail(self, n):
        return self.df.tail(n=n)


class SparkDataFrame(GenericDataFrame):
    """
    This class is the abstract layer over

    """

    def __init__(self, df):
        super().__init__()
        self.df = df

    @staticmethod
    def is_same_type(obj):
        """
        Check if spark dataframe without importing actual spark dataframe class and doing isinstance (too expensive
        to import pyspark class - create more library dependencies for pp)

        Args:
            obj: check if object is a spark dataframe

        Returns: True if the __module__ and __name__ of object matches spark dataframe, else false

        """
        return type(obj).__module__ == "pyspark.sql.dataframe" and type(obj).__name__ == "DataFrame"


def get_implemented_datatypes():
    return (PandasDataFrame, SparkDataFrame)
