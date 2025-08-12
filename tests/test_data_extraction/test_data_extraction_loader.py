from datetime import datetime, timedelta

import pandas as pd
import pytest

from awear_neuroscience.data_extraction.constants import (FIELD_KEYS,
                                                          SAMPLING_RATE)
from awear_neuroscience.data_extraction.firestore_loader import (
    process_eeg_records, query_eeg_data)


class DummyDoc:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class DummyCol:
    def __init__(self, docs):
        self._docs = docs

    def where(self, *a, **k):
        return self

    def order_by(self, *a, **k):
        return self

    def stream(self):
        return [DummyDoc(d) for d in self._docs]


class DummyClient:
    def __init__(self, docs):
        self._docs = docs

    def collection(self, *args):
        class C:
            def document(self_inner, *a, **k):
                return self_inner

            def collection(self_inner, *a, **k):
                return DummyCol(self._docs)

        return C()


def make_rec(timestamp: str, length: int) -> dict:
    base = {
        "timestamp": timestamp,
        "waveformRIGHT_TEMP": [0] * length,
        "focus_type": "distracted",
    }

    # Add all FIELD_KEYS (except timestamp which is already in base)
    for key in FIELD_KEYS:
        if key != "timestamp":
            base[key] = 10.0  # Dummy float for test

    return base


def test_query_with_explicit_time_range():
    now = datetime.now()
    client = DummyClient([make_rec("2025-07-01T10:00:00Z", SAMPLING_RATE)])
    recs = query_eeg_data(client, "c", "d", "s", time_ranges=[(now, now)])
    assert isinstance(recs, list) and len(recs) == 1


def test_process_filters_invalid_waveform_and_maps_fields():
    recs = [
        make_rec("2025-07-01T00:00:00Z", SAMPLING_RATE),
        make_rec("2025-07-01T00:00:00Z", 10),
    ]
    df = process_eeg_records(recs)
    assert len(df) == 1
    assert set(df.columns) == {
        "waveform",
        "timestamp",
        "utc_ts",
        "focus_type",
    }  # Only expect these columns
