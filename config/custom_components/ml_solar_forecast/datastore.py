"""Data store module for caching and managing time-series data with delta-fetching and serialization.

This module provides a base class for data stores that handle:
- Fetching missing data from external sources
- Applying horizon limits to prevent querying unavailable data
- Serialization and deserialization of data to/from disk
- Delta-fetching to efficiently update data ranges
"""

import abc
import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

import pandas as pd

log = logging.getLogger(__name__)


class DataStore:
    """Base class for caching data store with delta-fetching and serialization."""

    data: pd.DataFrame
    storage_dir: str | None
    storage_fn_prefix: str | None

    # Used during model performance evaluation to not accidently access prices we shouldn't know about yet
    horizon_cutoff: datetime | None

    # actually known horizon limit of the data source. Do not query missing data after the actual source horizon constantly
    known_source_horizon: datetime | None
    # when is next revalidation due?
    source_horizon_revalitation_ts: datetime | None

    last_updated: datetime

    def __init__(
        self,
        storage_dir: str | None = None,
        storage_fn_prefix: str | None = None,
    ) -> None:
        """Initialize the data store with optional storage parameters."""
        self.data = pd.DataFrame()
        self.storage_dir = storage_dir
        self.storage_fn_prefix = storage_fn_prefix

        self.last_updated = datetime(1970, 1, 1, tzinfo=UTC)

        self.horizon_cutoff = None
        self.known_source_horizon = None
        self.source_horizon_revalitation_ts = None

    def set_source_horizon(self, horizon: datetime, revalidation_ts: datetime | None):
        """Store the source horizon and when it should be revalidated.

        The horizon is the last timestamp the external data source is known to
        have available.  The revalidation timestamp is used to schedule the
        next check of the source horizon so we do not query past the actual
        available data.

        Parameters
        ----------
        horizon : datetime
            Last known available data point from the source.
        revalidation_ts : datetime | None
            When the horizon should be checked again, or ``None`` if no
            revalidation is scheduled.
        """
        self.known_source_horizon = horizon
        self.source_horizon_revalitation_ts = revalidation_ts

    def _apply_horizon(
        self, start: datetime, end: datetime
    ) -> tuple[datetime, datetime]:
        if self.horizon_cutoff:
            start = min(start, self.horizon_cutoff)
            end = min(end, self.horizon_cutoff)

        if self.known_source_horizon and (
            self.source_horizon_revalitation_ts is None
            or datetime.now(UTC) < self.source_horizon_revalitation_ts
        ):
            start = min(start, self.known_source_horizon)
            end = min(end, self.known_source_horizon)
        return (start, end)

    async def get_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch data between the given timestamps, applying horizon limits.

        This method fetches data from the start to end timestamps, ensuring
        that the data respects any horizon cutoff or known source horizon.
        It also fetches any missing data in the requested range.

        Parameters
        ----------
        start : datetime
            The start timestamp for the data range.
        end : datetime
            The end timestamp for the data range.

        Returns:
        -------
        pd.DataFrame
            A DataFrame containing the requested data.
        """
        start = start.astimezone(UTC)
        end = end.astimezone(UTC)
        start, end = self._apply_horizon(start, end)

        await self.fetch_missing_data(start, end)

        last_known = self.get_last_known()
        if last_known and last_known < end:
            # source horizon reached - remember/reschedule source query
            self.known_source_horizon = last_known
            self.source_horizon_revalitation_ts = (
                self.get_next_horizon_revalidation_time()
            )

        if self.horizon_cutoff and self.horizon_cutoff < end:
            end = self.horizon_cutoff
        return self.data.loc[start:end]

    def needs_horizon_revalidation(self) -> bool:
        """Check if the source horizon needs revalidation."""
        return (
            self.source_horizon_revalitation_ts is not None
            and datetime.now(UTC) > self.source_horizon_revalitation_ts
        )

    @abc.abstractmethod
    async def fetch_missing_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        pass

    @abc.abstractmethod
    def get_next_horizon_revalidation_time(self) -> datetime | None:
        pass

    def gen_missing_date_ranges(
        self, start: datetime, end: datetime
    ) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
        # Full 15-minute grid
        needed = pd.date_range(
            start=pd.to_datetime(start).floor("15min"),
            end=pd.to_datetime(end).ceil("15min"),
            freq="15min",
        )

        # Reindex to find missing timestamps
        missing = self.data.reindex(needed).isna().all(axis=1)

        # Keep only missing slots
        missing = missing[missing]

        if missing.empty:
            return []

        # Group consecutive 15-minute gaps
        groups = missing.index.to_series().diff().ne(pd.Timedelta("15min")).cumsum()

        ranges = missing.index.to_series().groupby(groups).agg(["min", "max"])

        return list(ranges.itertuples(index=False, name=None))

    def get_last_known(self) -> datetime | None:
        data = self.data
        if self.horizon_cutoff:
            data = data[: self.horizon_cutoff]
        if len(data) == 0:
            return None
        return data.index[-1]

    def drop_after(self, dt: datetime):
        if self.data.empty:
            return
        self.data = self.data[self.data.index <= pd.to_datetime(dt, utc=True)]

    def drop_before(self, dt: datetime):
        if self.data.empty:
            return
        self.data = self.data[self.data.index >= pd.to_datetime(dt, utc=True)]

    def _update_data(self, df: pd.DataFrame) -> bool:
        olddata = self.data
        self.data = df.combine_first(
            self.data
        ).dropna()  # keeps new data from df, fills it with existing data from self

        changed = not olddata.round(decimals=10).equals(self.data.round(decimals=10))
        if changed:
            self.last_updated = datetime.now(UTC)
        return changed

    def get_storage_file(self):
        if self.storage_dir is None or self.storage_fn_prefix is None:
            return None
        if not Path(self.storage_dir).exists():
            Path(self.storage_dir).mkdir(parents=True)
        return f"{self.storage_dir}/{self.storage_fn_prefix}.json.gz"

    async def serialize(self):
        fn = self.get_storage_file()
        if fn is not None:
            log.info("storing new %s data", self.storage_fn_prefix)
            await asyncio.to_thread(self.data.to_json, fn, compression="gzip")

    async def load(self) -> Self:
        fn = self.get_storage_file()
        if fn is not None and Path(fn).exists():
            log.info("loading persisted %s data", self.storage_fn_prefix)
            self.data = await asyncio.to_thread(pd.read_json, fn, compression="gzip")

            # Handle index type: to_json saves DatetimeIndex as epoch milliseconds,
            # which read_json loads as Int64Index. Convert back to DatetimeIndex.
            if pd.api.types.is_integer_dtype(self.data.index.dtype):
                # Index values are epoch milliseconds
                self.data.index = pd.to_datetime(self.data.index, unit="ms", utc=True)
            elif (
                isinstance(self.data.index, pd.DatetimeIndex)
                and self.data.index.tz is None
            ):
                # Index is DatetimeIndex but naive, localize to UTC
                self.data.index = self.data.index.tz_localize("UTC")

            self.data.index.set_names("time", inplace=True)
            self.data.dropna(inplace=True)

            self.last_updated = datetime.fromtimestamp(Path(fn).stat().st_mtime, tz=UTC)
        return self
