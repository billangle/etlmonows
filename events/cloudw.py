#!/usr/bin/env python3
"""
Report: count CloudWatch alarm occurrences and average ALARM duration per day.

- count per day = number of transitions into ALARM that day
- avg duration per day = average duration (minutes) of those ALARM episodes
  (episode ends when state leaves ALARM; if still ALARM, ends at 'now')

Works for Metric Alarms and Composite Alarms, as long as history contains StateUpdate entries.

Requires:
  pip install boto3

Usage examples:
  python alarm_alarm_counts.py --alarm-name "MyAlarm"
  python alarm_alarm_counts.py --alarm-name "MyAlarm" --region us-east-1
  python alarm_alarm_counts.py --alarm-name "MyAlarm" --days 1 7 30 --csv out.csv
"""

from __future__ import annotations

import argparse
import boto3
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, date
from typing import Dict, List, Optional, Tuple


@dataclass
class AlarmEvent:
    ts: datetime
    new_state: Optional[str]
    old_state: Optional[str]


@dataclass
class AlarmEpisode:
    start: datetime
    end: datetime  # resolved end (or now if still ALARM)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def daterange(start_day: date, end_day: date) -> List[date]:
    # inclusive start_day, inclusive end_day
    days = []
    cur = start_day
    while cur <= end_day:
        days.append(cur)
        cur = cur + timedelta(days=1)
    return days


def parse_history_event(history_item: dict) -> Optional[AlarmEvent]:
    """
    DescribeAlarmHistory items contain:
      - Timestamp
      - HistoryData (JSON string) which often contains oldState/newState objects
    We parse newState.stateValue and oldState.stateValue when present.
    """
    ts = history_item.get("Timestamp")
    if not ts:
        return None
    ts = to_utc(ts)

    hd = history_item.get("HistoryData")
    if not hd:
        return AlarmEvent(ts=ts, new_state=None, old_state=None)

    new_state = None
    old_state = None

    # HistoryData is usually a JSON string; be defensive.
    try:
        data = json.loads(hd)
        # Typical shape:
        # {"newState":{"stateValue":"ALARM",...},"oldState":{"stateValue":"OK",...},...}
        ns = data.get("newState") if isinstance(data, dict) else None
        os = data.get("oldState") if isinstance(data, dict) else None

        if isinstance(ns, dict):
            new_state = ns.get("stateValue")
        if isinstance(os, dict):
            old_state = os.get("stateValue")

        # Some variants may have direct keys
        if new_state is None and isinstance(data, dict):
            new_state = data.get("newStateValue") or data.get("stateValue")
        if old_state is None and isinstance(data, dict):
            old_state = data.get("oldStateValue")

    except Exception:
        # If parsing fails, still return timestamp
        return AlarmEvent(ts=ts, new_state=None, old_state=None)

    return AlarmEvent(ts=ts, new_state=new_state, old_state=old_state)


def fetch_alarm_state_updates(
    cw,
    alarm_name: str,
    start_time: datetime,
    end_time: datetime,
) -> List[AlarmEvent]:
    """
    Fetch alarm history entries of type StateUpdate within [start_time, end_time].
    Handles pagination.
    """
    start_time = to_utc(start_time)
    end_time = to_utc(end_time)

    events: List[AlarmEvent] = []
    next_token = None

    while True:
        kwargs = dict(
            AlarmName=alarm_name,
            HistoryItemType="StateUpdate",
            StartDate=start_time,
            EndDate=end_time,
            MaxRecords=100,
        )
        if next_token:
            kwargs["NextToken"] = next_token

        resp = cw.describe_alarm_history(**kwargs)
        items = resp.get("AlarmHistoryItems", []) or []
        for it in items:
            ev = parse_history_event(it)
            if ev:
                events.append(ev)

        next_token = resp.get("NextToken")
        if not next_token:
            break

    # History is returned reverse-chronological; sort ascending for timeline logic
    events.sort(key=lambda e: e.ts)
    return events


def build_alarm_episodes(
    events: List[AlarmEvent],
    window_start: datetime,
    window_end: datetime,
    assume_state_before_window: Optional[str] = None,
) -> List[AlarmEpisode]:
    """
    Turn state transitions into ALARM episodes.

    We create an episode when we see a transition into ALARM.
    It ends at the first subsequent event where new_state != 'ALARM'.
    If no such event, episode ends at window_end.
    """
    window_start = to_utc(window_start)
    window_end = to_utc(window_end)

    episodes: List[AlarmEpisode] = []

    current_state = assume_state_before_window  # may be None
    current_alarm_start: Optional[datetime] = None

    for ev in events:
        ns = ev.new_state
        # If we can't parse new state, skip it
        if ns is None:
            continue

        # Track transitions
        if ns == "ALARM":
            if current_state != "ALARM":
                # entering ALARM
                current_alarm_start = ev.ts
        else:
            if current_state == "ALARM" and current_alarm_start is not None:
                # leaving ALARM
                episodes.append(AlarmEpisode(start=current_alarm_start, end=ev.ts))
                current_alarm_start = None

        current_state = ns

    # If still ALARM at window_end, close it at window_end
    if current_state == "ALARM" and current_alarm_start is not None:
        episodes.append(AlarmEpisode(start=current_alarm_start, end=window_end))

    # Clip to window (defensive)
    clipped: List[AlarmEpisode] = []
    for ep in episodes:
        s = max(ep.start, window_start)
        e = min(ep.end, window_end)
        if e > s:
            clipped.append(AlarmEpisode(start=s, end=e))

    return clipped


def episodes_to_daily_stats(
    episodes: List[AlarmEpisode],
    start_day: date,
    end_day: date,
) -> List[Tuple[date, int, Optional[float]]]:
    """
    Attribute each episode to the day it STARTED (UTC).
    Return rows: (day, count, avg_duration_minutes)
    """
    per_day: Dict[date, List[float]] = {d: [] for d in daterange(start_day, end_day)}

    for ep in episodes:
        d = ep.start.date()
        if d < start_day or d > end_day:
            continue
        duration_min = (ep.end - ep.start).total_seconds() / 60.0
        per_day.setdefault(d, []).append(duration_min)

    rows: List[Tuple[date, int, Optional[float]]] = []
    for d in daterange(start_day, end_day):
        durations = per_day.get(d, [])
        if not durations:
            rows.append((d, 0, None))
        else:
            avg = sum(durations) / len(durations)
            rows.append((d, len(durations), avg))
    return rows


def print_section(title: str, rows: List[Tuple[date, int, Optional[float]]]) -> None:
    print("\n" + title)
    print("-" * len(title))
    print(f"{'date(UTC)':<12}  {'count':>5}  {'avg_duration_min':>16}")
    for d, cnt, avg in rows:
        avg_str = f"{avg:.2f}" if avg is not None else "N/A"
        print(f"{d.isoformat():<12}  {cnt:>5}  {avg_str:>16}")


def write_csv(path: str, sections: List[Tuple[str, List[Tuple[date, int, Optional[float]]]]]) -> None:
    import csv
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["section", "date_utc", "count", "avg_duration_minutes"])
        for section_name, rows in sections:
            for d, cnt, avg in rows:
                w.writerow([section_name, d.isoformat(), cnt, "" if avg is None else f"{avg:.6f}"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alarm-name", required=True, help="CloudWatch alarm name (exact match).")
    ap.add_argument("--region", default=None, help="AWS region (defaults to your AWS config).")
    ap.add_argument("--days", nargs="+", type=int, default=[1, 7, 30], help="Windows in days.")
    ap.add_argument("--csv", default=None, help="Optional output CSV path.")
    args = ap.parse_args()

    cw = boto3.client("cloudwatch", region_name=args.region) if args.region else boto3.client("cloudwatch")

    now = utc_now()

    sections_out: List[Tuple[str, List[Tuple[date, int, Optional[float]]]]] = []

    for n_days in args.days:
        # Window covers N days back from now
        window_start = now - timedelta(days=n_days)
        window_end = now

        # For daily rows, use UTC day boundaries within the window
        start_day = window_start.date()
        end_day = window_end.date()

        events = fetch_alarm_state_updates(cw, args.alarm_name, window_start, window_end)
        episodes = build_alarm_episodes(events, window_start, window_end)

        rows = episodes_to_daily_stats(episodes, start_day, end_day)
        section_name = f"last_{n_days}_days"
        print_section(f"Alarm '{args.alarm_name}' — {section_name} (UTC)", rows)
        sections_out.append((section_name, rows))

    if args.csv:
        write_csv(args.csv, sections_out)
        print(f"\nWrote CSV: {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
