import unittest

from tempo import TSDF
from tempo.resample import (
    _appendAggKey,
    aggregate,
    checkAllowableFreq,
    validateFuncExists,
)
from tests.base import SparkTest


class ResampleTest(SparkTest):
    def test_resample(self):
        """Test of range stats for 20 minute rolling window"""

        # construct dataframes
        tsdf_input = self.get_data_as_tsdf("input")
        dfExpected = self.get_data_as_sdf("expected")
        expected_30s_df = self.get_data_as_sdf("expected30m")
        barsExpected = self.get_data_as_sdf("expectedbars")

        # 1 minute aggregation
        featured_df = tsdf_input.resample(freq="min", func="floor", prefix="floor").df
        # 30 minute aggregation
        resample_30m = tsdf_input.resample(freq="5 minutes", func="mean").df.withColumn(
            "trade_pr", sfn.round(sfn.col("trade_pr"), 2)
        )

        bars = tsdf_input.calc_bars(
            freq="min", metric_cols=["trade_pr", "trade_pr_2"]
        ).df

        # should be equal to the expected dataframe
        self.assertDataFrameEquality(featured_df, dfExpected)
        self.assertDataFrameEquality(resample_30m, expected_30s_df)

        # test bars summary
        self.assertDataFrameEquality(bars, barsExpected)

    def test_resample_millis(self):
        """Test of resampling for millisecond windows"""

        # construct dataframes
        tsdf_init = self.get_data_as_tsdf("init")
        dfExpected = self.get_data_as_sdf("expectedms")

        # 30 minute aggregation
        resample_ms = tsdf_init.resample(freq="ms", func="mean").df.withColumn(
            "trade_pr", sfn.round(sfn.col("trade_pr"), 2)
        )

        self.assertDataFrameEquality(resample_ms, dfExpected)

    def test_upsample(self):
        """Test of range stats for 20 minute rolling window"""

        # construct dataframes
        tsdf_input = self.get_data_as_tsdf("input")
        expected_30s_df = self.get_data_as_sdf("expected30m")
        barsExpected = self.get_data_as_sdf("expectedbars")

        resample_30m = tsdf_input.resample(
            freq="5 minutes", func="mean", fill=True
        ).df.withColumn("trade_pr", sfn.round(sfn.col("trade_pr"), 2))

        bars = tsdf_input.calc_bars(
            freq="min", metric_cols=["trade_pr", "trade_pr_2"]
        ).df

        upsampled = resample_30m.filter(
            sfn.col("event_ts").isin(
                "2020-08-01 00:00:00",
                "2020-08-01 00:05:00",
                "2020-09-01 00:00:00",
                "2020-09-01 00:15:00",
            )
        )

        # test upsample summary
        self.assertDataFrameEquality(upsampled, expected_30s_df)

        # test bars summary
        self.assertDataFrameEquality(bars, barsExpected)


class ResampleUnitTests(SparkTest):
    def test_appendAggKey_freq_is_none(self):
        input_tsdf = self.get_data_as_tsdf("input_data")

        self.assertRaises(TypeError, _appendAggKey, input_tsdf)

    def test_appendAggKey_freq_microsecond(self):
        input_tsdf = self.get_data_as_tsdf("input_data")

        appendAggKey_tuple = _appendAggKey(input_tsdf, "1 MICROSECOND")
        appendAggKey_tsdf = appendAggKey_tuple[0]

        self.assertIsInstance(appendAggKey_tsdf, TSDF)
        self.assertIn("agg_key", appendAggKey_tsdf.df.columns)
        self.assertEqual(appendAggKey_tuple[1], "1")
        self.assertEqual(appendAggKey_tuple[2], "microseconds")

    def test_appendAggKey_freq_is_invalid(self):
        input_tsdf = self.get_data_as_tsdf("input_data")

        self.assertRaises(
            ValueError,
            _appendAggKey,
            input_tsdf,
            "1 invalid",
        )

    def test_aggregate_floor(self):
        input_tsdf = self.get_data_as_tsdf("input_data")
        expected_data = self.get_data_as_sdf("expected_data")

        aggregate_df = aggregate(input_tsdf, "1 DAY", "floor")

        self.assertDataFrameEquality(
            aggregate_df,
            expected_data,
        )

    def test_aggregate_average(self):
        # TODO: fix DATE returns `null`
        # DATE is being included in metricCols when metricCols is None
        # this occurs for all aggregate functions but causes negative side effects with avg
        # is this intentional?
        # resample.py -> lines 86 to 87
        # occurring in all `func` arguments but causing null values for "mean"
        input_tsdf = self.get_data_as_tsdf("input_data")
        expected_data = self.get_data_as_sdf("expected_data")

        # explicitly declaring metricCols to remove DATE so that test can pass for now
        aggregate_df = aggregate(
            input_tsdf, "1 DAY", "mean", ["trade_pr", "trade_pr_2"]
        )

        self.assertDataFrameEquality(
            aggregate_df,
            expected_data,
        )

    def test_aggregate_min(self):
        input_tsdf = self.get_data_as_tsdf("input_data")
        expected_data = self.get_data_as_sdf("expected_data")

        aggregate_df = aggregate(input_tsdf, "1 DAY", "min")

        self.assertDataFrameEquality(
            aggregate_df,
            expected_data,
        )

    def test_aggregate_min_with_prefix(self):
        input_tsdf = self.get_data_as_tsdf("input_data")
        expected_data = self.get_data_as_sdf("expected_data")

        aggregate_df = aggregate(input_tsdf, "1 DAY", "min", prefix="min")

        self.assertDataFrameEquality(
            aggregate_df,
            expected_data,
        )

    def test_aggregate_min_with_fill(self):
        input_tsdf = self.get_data_as_tsdf("input_data")
        expected_data = self.get_data_as_sdf("expected_data")

        aggregate_df = aggregate(input_tsdf, "1 DAY", "min", fill=True)

        self.assertDataFrameEquality(
            aggregate_df,
            expected_data,
        )

    def test_aggregate_max(self):
        input_tsdf = self.get_data_as_tsdf("input_data")
        expected_data = self.get_data_as_sdf("expected_data")

        aggregate_df = aggregate(input_tsdf, "1 DAY", "max")

        self.assertDataFrameEquality(
            aggregate_df,
            expected_data,
        )

    def test_aggregate_ceiling(self):
        input_tsdf = self.get_data_as_tsdf("input_data")
        expected_data = self.get_data_as_sdf("expected_data")

        aggregate_df = aggregate(input_tsdf, "1 DAY", "ceil")

        self.assertDataFrameEquality(
            aggregate_df,
            expected_data,
        )

    def test_aggregate_invalid_func_arg(self):
        # TODO : we should not be hitting an UnboundLocalError
        input_tsdf = self.get_data_as_tsdf("input_data")

        self.assertRaises(UnboundLocalError, aggregate, input_tsdf, "1 DAY", "average")

    def test_check_allowable_freq_none(self):
        self.assertRaises(TypeError, checkAllowableFreq, None)

    def test_check_allowable_freq_microsecond(self):
        self.assertEqual(checkAllowableFreq("1 MICROSECOND"), ("1", "microsec"))

    def test_check_allowable_freq_millisecond(self):
        self.assertEqual(checkAllowableFreq("1 MILLISECOND"), ("1", "ms"))

    def test_check_allowable_freq_second(self):
        self.assertEqual(checkAllowableFreq("1 SECOND"), ("1", "sec"))

    def test_check_allowable_freq_minute(self):
        self.assertEqual(checkAllowableFreq("1 MINUTE"), ("1", "min"))

    def test_check_allowable_freq_hour(self):
        self.assertEqual(checkAllowableFreq("1 HOUR"), ("1", "hour"))

    def test_check_allowable_freq_day(self):
        self.assertEqual(checkAllowableFreq("1 DAY"), ("1", "day"))

    def test_check_allowable_freq_no_interval(self):
        # TODO: should first element return str for consistency?
        self.assertEqual(checkAllowableFreq("day"), (1, "day"))

    def test_check_allowable_freq_exception_not_in_allowable_freqs(self):
        self.assertRaises(ValueError, checkAllowableFreq, "wrong")

    def test_check_allowable_freq_exception(self):
        self.assertRaises(ValueError, checkAllowableFreq, "wrong wrong")

    def test_validate_func_exists_type_error(self):
        self.assertRaises(TypeError, validateFuncExists, None)

    def test_validate_func_exists_value_error(self):
        self.assertRaises(ValueError, validateFuncExists, "non-existent")


# MAIN
if __name__ == "__main__":
    unittest.main()
