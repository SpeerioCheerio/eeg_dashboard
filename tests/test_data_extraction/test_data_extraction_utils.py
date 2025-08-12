import datetime

import pandas as pd

from awear_neuroscience.data_extraction.utils import (
    convert_string_to_utc_timestamp, format_firestore_timestamp)


def test_format_firestore_timestamp_naive():
    dt = datetime.datetime(2025, 7, 1, 12, 0, 0, 123456)
    out = format_firestore_timestamp(dt)
    assert out.endswith("+00:00")
    assert "123456" in out


def test_format_firestore_timestamp_pd_ts():
    pdt = pd.Timestamp("2025-07-01T10:00:00.654321")
    out = format_firestore_timestamp(pdt)
    assert "654321" in out and out.endswith("+00:00")


def test_convert_string_robust_with_z():
    ts = "2025-07-01T00:00:00.000001Z"
    val = convert_string_to_utc_timestamp(ts)
    # Correct expected value for 2025-07-01T00:00:00.000001Z
    expected = 1_751_328_000.000001
    assert abs(val - expected) < 1e-6


def test_convert_string_without_timezone():
    ts = "2025-07-01T10:00:00.123456"
    val = convert_string_to_utc_timestamp(ts)
    assert (
        abs(
            val
            - datetime.datetime(
                2025, 7, 1, 10, 0, 0, 123456, tzinfo=datetime.timezone.utc
            ).timestamp()
        )
        < 1e-6
    )
