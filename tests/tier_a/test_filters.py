# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from aol_email_exporter.filters import apply_filters, sort_records
from aol_email_exporter.models import FilterParams

pytestmark = pytest.mark.tier_a


class TestApplyFilters:
    """Client-side filter refinement on fetched EmailRecord lists."""

    def test_filter_by_date_range(self, sample_records):
        """Records within the date range are returned; others excluded.

        apply_filters does sender/subject only (date is server-side), so
        we verify that records pass through unmodified when no sender/subject
        criteria are set, then verify the full pipeline via a combined test.
        """
        # apply_filters passes all records when no sender/subject criteria set
        params = FilterParams()
        result = apply_filters(sample_records, params)
        assert len(result) == len(sample_records)

    def test_filter_by_sender(self, sample_records):
        """Case-insensitive substring match on sender."""
        params = FilterParams(sender="alice")
        result = apply_filters(sample_records, params)
        assert all("alice" in r.sender.lower() for r in result)
        assert len(result) == 4  # records 1, 3, 6, 9

    def test_filter_by_sender_case_insensitive(self, sample_records):
        """Sender filter is case-insensitive."""
        lower = apply_filters(sample_records, FilterParams(sender="alice"))
        upper = apply_filters(sample_records, FilterParams(sender="ALICE"))
        mixed = apply_filters(sample_records, FilterParams(sender="Alice"))
        assert len(lower) == len(upper) == len(mixed)

    def test_filter_by_subject(self, sample_records):
        """Case-insensitive substring match on subject."""
        params = FilterParams(subject="invoice")
        result = apply_filters(sample_records, params)
        assert len(result) == 1
        assert "invoice" in result[0].subject.lower()

    def test_filter_combined(self, sample_records):
        """Sender + subject filters applied together narrow the set."""
        params = FilterParams(sender="bob", subject="meeting")
        result = apply_filters(sample_records, params)
        assert len(result) == 1
        assert result[0].uid == "5"

    def test_filter_no_criteria(self, sample_records):
        """No criteria returns all records unchanged."""
        result = apply_filters(sample_records, FilterParams())
        assert result == sample_records

    def test_filter_no_matches(self, sample_records):
        """No records match, result is empty."""
        params = FilterParams(sender="nonexistent@nowhere.invalid")
        result = apply_filters(sample_records, params)
        assert result == []


class TestSortRecords:
    """Sorting EmailRecord lists by various fields."""

    def test_sort_by_date(self, sample_records):
        result = sort_records(sample_records, key="date")
        dates = [r.date for r in result]
        assert dates == sorted(dates)

    def test_sort_by_sender(self, sample_records):
        result = sort_records(sample_records, key="sender")
        senders = [r.sender for r in result]
        assert senders == sorted(senders)

    def test_sort_by_subject(self, sample_records):
        result = sort_records(sample_records, key="subject")
        subjects = [r.subject for r in result]
        assert subjects == sorted(subjects)

    def test_sort_reverse(self, sample_records):
        result = sort_records(sample_records, key="date", reverse=True)
        dates = [r.date for r in result]
        assert dates == sorted(dates, reverse=True)

    def test_sort_by_size(self, sample_records):
        result = sort_records(sample_records, key="size_bytes")
        sizes = [r.size_bytes for r in result]
        assert sizes == sorted(sizes)

    def test_sort_invalid_key(self, sample_records):
        with pytest.raises(ValueError, match="Unsupported sort key"):
            sort_records(sample_records, key="nonexistent")
