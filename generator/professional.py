"""Render anonymized professional aggregates exported outside the public workflow."""

import json
import math
from datetime import datetime

from generator.config import ConfigError
from generator.motion import Motion
from generator.svg import frame
from generator.typeset import Typesetter, wrap

METRICS = (
    ("prs_opened", "PRs opened"),
    ("prs_merged", "PRs merged"),
    ("prs_reviewed_from_others", "PRs reviewed"),
    ("distinct_repositories_with_prs_or_reviews", "repositories"),
)


def load(path):
    """Fail explicitly on invalid exports; unavailable values remain unavailable."""
    try:
        stats = json.loads(path.read_text(encoding="utf-8"))
        start = datetime.fromisoformat(stats["period"]["start_utc"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(stats["period"]["end_utc"].replace("Z", "+00:00"))
        collected = datetime.fromisoformat(stats["collected_at_utc"].replace("Z", "+00:00"))
        if any(day.utcoffset() is None for day in (start, end, collected)) or start >= end:
            raise ValueError("invalid UTC period")
        for key, _ in METRICS:
            value = stats["personal_activity"][key]
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"invalid metric: {key}")
        shares = stats["languages"]["distribution_percent"]
        if not isinstance(shares, dict):
            raise ValueError("language distribution must be a mapping")
        for name, value in shares.items():
            if not isinstance(name, str) or type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100:
                raise ValueError("invalid language percentage")
        if sum(shares.values()) > 101:
            raise ValueError("language percentages exceed 100% beyond rounding")
        return stats
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise ConfigError(f"Invalid professional stats export: {error}") from error


def language_shares(stats, maximum):
    """Keep exported percentages; do not renormalize the selected languages."""
    shares = stats["languages"]["distribution_percent"]
    return sorted(((name, value) for name, value in shares.items() if value > 0),
                  key=lambda item: (-item[1], item[0]))[:maximum]


def render(stats, theme, mobile=False, motion=True):
    ts, mo = Typesetter(), Motion(motion)
    width, margin, columns = (390, 24, 2) if mobile else (850, 44, 4)
    height = 330 if mobile else 230
    span = (width - margin * 2) / columns
    period = stats["period"]
    dates = f'{period["start_utc"][:10]} to {period["end_utc"][:10]} (UTC)'
    body = [ts.line(margin, 36, "Professional activity", 19, theme.ink),
            ts.line(margin, 60, dates, 13, theme.mute, "italic")]
    summary = []
    for index, (key, label) in enumerate(METRICS):
        value = stats["personal_activity"][key]
        figure = f"{value:,}" if value is not None else "N/A"
        x = margin + index % columns * span
        y = 116 + index // columns * 90
        attrs = mo.cls("soft", delay=index * .12)
        body.append(ts.line(x, y, figure, 34, theme.ink, "light", attrs=attrs))
        body.append(ts.line(x, y + 24, label, 14, theme.mute, "italic", attrs=attrs))
        summary.append(f"{figure} {label}")
    note_y = height - 48
    note = "Reviews count distinct PRs by others. Employer repositories only."
    for index, line in enumerate(wrap(note, 12, "regular", width - 2 * margin, max_lines=2)):
        body.append(ts.line(margin, note_y + index * 16, line, 12, theme.mute))
    body.append(ts.line(margin, height - 16,
                        f'Collected {stats["collected_at_utc"][:10]} · Exported snapshot',
                        11.5, theme.mute))
    return frame(theme, width, height, "".join(body), "Professional GitHub activity",
                 dates + ": " + "; ".join(summary) + ". " + note, ts.defs(), mo)
