"""Narrow Data Designer 0.10 / pandas Arrow missing-statistic compatibility."""
from contextlib import contextmanager
from importlib.metadata import version
import math


@contextmanager
def native_missing_token_statistics():
    """Retain undefined sample deviation while allowing the native profiler to finish.

    Arrow's one-row Series.std() returns pandas.NA. Designer 0.10's numeric
    validator cannot cast that scalar to float, whereas it accepts IEEE NaN.
    This changes only that missing scalar representation, never rows or finite
    statistics. Native Pydantic JSON serialization writes NaN as JSON null.
    The isolated runner restores the SDK function even when profiling fails.
    """
    if version('data-designer') != '0.10.0':
        raise RuntimeError('Revalidate the profiling compatibility boundary for this Designer version')
    import pandas as pd
    from data_designer.engine.analysis.utils import column_statistics_calculations as calculations

    original = calculations.calculate_output_token_stats
    receipt = {'sdk_version': '0.10.0', 'boundary': 'calculate_output_token_stats',
               'normalization': 'pandas.NA to native NaN; JSON null for undefined statistics',
               'normalized_fields': [], 'input_rows_modified': False, 'generation_replayed': False}

    def compatible(column_config, dataframe):
        statistics = original(column_config, dataframe)
        for name, value in statistics.items():
            if value is pd.NA:
                statistics[name] = math.nan
                receipt['normalized_fields'].append({'column': column_config.name, 'statistic': name})
        return statistics

    calculations.calculate_output_token_stats = compatible
    try:
        yield receipt
    finally:
        calculations.calculate_output_token_stats = original
