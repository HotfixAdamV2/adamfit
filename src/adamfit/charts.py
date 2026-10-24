"""Shared building blocks for charts over time (weight, weight change, macros).

Each chart is written once here and used on several pages. Every widget key
starts with a ``key`` prefix chosen by the page (e.g. ``"home_weight"``), so
the same chart can appear on different pages, or twice on one page, without
two widgets sharing a key.

The pieces are:

- ``chart_card`` and ``chart_grid``: a bordered card per chart with a Show
  toggle, and a dashboard grid that is always two cards wide.
- ``chart_controls``: time period (with a custom date range), rolling-average
  window and which lines to show.
- ``add_rolling_average``, ``filter_dates`` and ``period_changes``: the maths.
  The average is worked out on the full history *before* trimming to the
  visible dates, so the first days on the chart still average the days
  before them.
- ``time_series_chart``: an Altair line chart with a thin line (with dots)
  for the raw values, a bold line for the rolling average, and one tooltip
  showing both values for the date under the pointer.
- ``show_weight_over_time``, ``show_weight_change`` and
  ``show_macros_over_time``: ready-made charts with their controls.

Every card draws its plot straight under the header, at the same fixed
height (``CHART_HEIGHT``), and puts the controls *below* the plot. Cards have
different controls (the macros chart has a macro picker, a custom range adds
a date picker...), so this is what keeps plots in the same dashboard row
lined up, top and bottom, whatever the controls are.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from adamfit import food_logs
from adamfit.nutrition import MACROS

# Time period choices and how many days back each one shows.
# None means "no limit" for "All", and "pick your own dates" for "Custom".
PERIODS = {"1M": 30, "3M": 91, "6M": 182, "1Y": 365, "All": None, "Custom": None}
DEFAULT_PERIOD = "3M"
DEFAULT_WINDOW_DAYS = 7
# Earliest date offered in the custom date range picker
EARLIEST_DATE = date(2010, 1, 1)
# Height in pixels of every chart, so charts side by side line up
CHART_HEIGHT = 300

# The two lines every chart can show. The keys never change, so the pills
# keep their selection; only the text shown on the chart says e.g. "7-day average".
RAW = "raw"
AVERAGE = "avg"
WEIGHT_LINES = {RAW: "Weigh-ins", AVERAGE: "Rolling average"}
MACRO_LINES = {RAW: "Daily total", AVERAGE: "Rolling average"}

# Weight change: how long each bar's period is, as pandas period codes.
# "W" weeks run Monday to Sunday; "M" is a calendar month.
GRANULARITIES = {"D": "Daily", "W": "Weekly", "M": "Monthly"}
# Weight change chart types, and the dash patterns telling its two axes
# apart: solid lines are lb/kg (left axis), dashed lines are % (right axis)
CHANGE_CHART_TYPES = ["Bars", "Lines"]
SOLID = [1, 0]
DASHED = [6, 4]
# % change lines are light green in both chart types, so they stand out
# from the grey/blue lines and the orange/blue bars
PCT_LINE_COLOR = "#4caf50"
# Two clearly different colours (blue and orange, safe for colour blindness).
# Neither is "good" or "bad": whether gaining is good depends on your goal.
GAIN_COLOR = "#e8743b"
LOSS_COLOR = "#2f7ed8"

# Line colours: a soft grey for the raw values, a strong blue for the average
RAW_COLOR = "#8c96a3"
AVERAGE_COLOR = "#2f7ed8"

DATE_FORMAT = "%Y-%m-%d"
# Every chart control keeps its value for the whole session, even while its
# card is hidden or the user is on another page
PERSIST = "session"


@dataclass
class ChartSettings:
    """
    The choices made with ``chart_controls``.

    Attributes
    ----------
    period : str
        The chosen period button, e.g. ``"3M"`` or ``"Custom"``.
    start : date | None
        First day to show. None means from the very first entry ("All").
    end : date
        Last day to show (today, unless a custom range ends earlier).
    window_days : int
        Size of the rolling-average window in calendar days.
    lines : list[str]
        Which lines (or bar sources) to draw: any of ``RAW`` and ``AVERAGE``.
    """

    period: str
    start: date | None
    end: date
    window_days: int
    lines: list[str]


@dataclass
class Card:
    """
    One chart card for ``chart_grid``.

    Attributes
    ----------
    title : str
        Heading shown at the top of the card, e.g. ``"Weight over time"``.
    key : str
        Prefix for the card's widget keys. Must be unique on the page.
    draw : Callable[[str], None]
        Draws the chart and its controls. It is called with ``key``.
    """

    title: str
    key: str
    draw: Callable[[str], None]


def chart_card(title: str, key: str, draw: Callable[[str], None], stretch: bool = False) -> None:
    """
    Show a bordered card with a heading and a Show toggle, then the chart.

    When the toggle is off, ``draw`` is not called at all, so a hidden chart
    runs no database queries. The toggle remembers its state for the whole
    session, including after visiting other pages.

    Parameters
    ----------
    title : str
        Heading shown at the top of the card.
    key : str
        Prefix for the widget keys. Must be unique on the page.
    draw : Callable[[str], None]
        Draws the chart and its controls. It is called with ``key``.
    stretch : bool, optional
        Make the card as tall as the tallest card in its row, so the
        borders of cards side by side line up too (used by ``chart_grid``).
    """
    with st.container(border=True, height="stretch" if stretch else "content"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.subheader(title)
            shown = st.toggle("Show", value=True, key=f"{key}_shown", persist_state=PERSIST)
        if shown:
            draw(key)


def chart_grid(cards: list[Card]) -> None:
    """
    Lay chart cards out in rows of two, filling each row left to right.

    With an odd number of cards, the last one sits in the left column.

    Parameters
    ----------
    cards : list[Card]
        The cards to show, in reading order.
    """
    for first in range(0, len(cards), 2):
        columns = st.columns(2)
        for column, card in zip(columns, cards[first : first + 2]):
            with column:
                chart_card(card.title, card.key, card.draw, stretch=True)


def date_range_control(key: str) -> tuple[str, date | None, date]:
    """
    Show the time period buttons, and a date range picker for "Custom".

    Parameters
    ----------
    key : str
        Prefix for the widget keys. Must be unique on the page.

    Returns
    -------
    tuple[str, date | None, date]
        The chosen period, the first day (None for "All") and the last day.
    """
    today = date.today()
    period = st.segmented_control(
        "Time period",
        list(PERIODS),
        default=DEFAULT_PERIOD,
        required=True,
        key=f"{key}_period",
        persist_state=PERSIST,
    )
    if period != "Custom":
        days_back = PERIODS[period]
        start = None if days_back is None else today - timedelta(days=days_back)
        return period, start, today

    # Passing a (start, end) pair makes st.date_input pick a range
    picked = st.date_input(
        "Date range",
        value=(today - timedelta(days=PERIODS[DEFAULT_PERIOD]), today),
        min_value=EARLIEST_DATE,
        max_value=today,
        format="YYYY-MM-DD",
        key=f"{key}_range",
        persist_state=PERSIST,
    )
    # While the user is choosing, only the first date has been clicked, so
    # the picker returns a single date. Show up to today until they finish.
    if len(picked) == 2:
        return period, picked[0], picked[1]
    if len(picked) == 1:
        st.caption("Pick an end date. Showing up to today for now.")
        return period, picked[0], today
    return period, None, today


def chart_controls(
    key: str,
    lines: dict[str, str],
    default_lines: list[str] | None = None,
    lines_label: str = "Lines",
) -> ChartSettings:
    """
    Show the chart controls stacked so they fit in a half-width column.

    Parameters
    ----------
    key : str
        Prefix for the widget keys. Must be unique on the page.
    lines : dict[str, str]
        The lines the user can turn on and off, as ``{RAW: label,
        AVERAGE: label}``.
    default_lines : list[str] | None, optional
        Which lines are on at first. None turns them all on.
    lines_label : str, optional
        Label above the line pills.

    Returns
    -------
    ChartSettings
        The chosen period, dates, rolling window and lines.
    """
    period, start, end = date_range_control(key)
    with st.container(horizontal=True, vertical_alignment="bottom"):
        window_days = st.number_input(
            "Rolling average (days)",
            min_value=1,
            max_value=90,
            value=DEFAULT_WINDOW_DAYS,
            step=1,
            width=170,
            key=f"{key}_window",
            persist_state=PERSIST,
        )
        shown = st.pills(
            lines_label,
            list(lines),
            selection_mode="multi",
            default=list(lines) if default_lines is None else default_lines,
            format_func=lines.get,
            key=f"{key}_lines",
            persist_state=PERSIST,
        )
    return ChartSettings(period, start, end, int(window_days), shown)


def add_rolling_average(
    df: pd.DataFrame,
    date_column: str,
    value_column: str,
    window_days: int,
) -> pd.DataFrame:
    """
    Add a time-based rolling average column called ``rolling_avg``.

    The window covers calendar days, not a number of rows, so skipped days
    are handled correctly: a 7-day average on any date is the mean of all
    rows in the 7 days ending on that date. Days with no row are simply not
    counted (they are not treated as zero).

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``date_column`` as datetimes, sorted oldest first.
    date_column : str
        Name of the date column, e.g. ``"weigh_date"``.
    value_column : str
        Name of the column to average.
    window_days : int
        Size of the window in days.

    Returns
    -------
    pd.DataFrame
        A copy of ``df`` with an added ``rolling_avg`` column.
    """
    out = df.copy()
    out["rolling_avg"] = (
        out.set_index(date_column)[value_column].rolling(f"{window_days}D").mean().to_numpy()
    )
    return out


def filter_dates(df: pd.DataFrame, date_column: str, start: date | None, end: date) -> pd.DataFrame:
    """
    Keep only the rows between two dates (both included).

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``date_column`` as datetimes.
    date_column : str
        Name of the date column.
    start : date | None
        First day to keep. None keeps everything up to ``end``.
    end : date
        Last day to keep.

    Returns
    -------
    pd.DataFrame
        The matching rows.
    """
    keep = df[date_column] <= pd.Timestamp(end)
    if start is not None:
        keep &= df[date_column] >= pd.Timestamp(start)
    return df[keep]


def period_changes(
    df: pd.DataFrame,
    date_column: str,
    value_column: str,
    freq: str,
    start: date | None,
    end: date,
) -> pd.DataFrame:
    """
    Work out how much a value changed from one period to the next.

    Each period (day, Monday-to-Sunday week, or calendar month) is
    represented by its *last* value: the last weigh-in in the period, or the
    rolling average on the last date that has one. The change is that value
    minus the value of the previous period that has data, and the
    percentage change is that change as a percentage of the previous
    period's value. Periods with no data are skipped, so after a gap both
    are measured against the last period before the gap.

    Parameters
    ----------
    df : pd.DataFrame
        The full history, oldest first, with ``date_column`` as datetimes.
        Use the full history (not just the visible dates), so the first
        visible period still has a previous period to compare with.
    date_column : str
        Name of the date column.
    value_column : str
        Name of the column to compare, e.g. ``"weight"`` or ``"rolling_avg"``.
    freq : str
        ``"D"``, ``"W"`` or ``"M"`` (see ``GRANULARITIES``).
    start : date | None
        Only return periods that overlap this date or later. None returns
        all periods.
    end : date
        Ignore data after this date.

    Returns
    -------
    pd.DataFrame
        One row per period, oldest first, with ``period_start``
        (datetime), ``last_date`` (the date the period-end value comes
        from), ``value``, ``previous`` (the previous period's value),
        ``change`` and ``pct`` (``change / previous * 100``; NaN if the
        previous value is 0). The very first period with data has nothing
        to compare with, so it is left out.
    """
    data = df[df[date_column] <= pd.Timestamp(end)].dropna(subset=[value_column])
    # e.g. every date from Mon 2026-10-19 to Sun 2026-10-25 becomes 2026-10-19
    period_start = data[date_column].dt.to_period(freq).dt.start_time
    last_rows = data.groupby(period_start).last()

    out = pd.DataFrame(
        {
            "period_start": last_rows.index,
            "last_date": last_rows[date_column].to_numpy(),
            "value": last_rows[value_column].to_numpy(),
        }
    )
    out["previous"] = out["value"].shift(1)
    out["change"] = out["value"] - out["previous"]
    # A previous value of 0 would divide by zero, so it gives NaN instead
    out["pct"] = out["change"] / out["previous"].where(out["previous"] != 0) * 100
    out = out.dropna(subset=["change"])
    if start is not None:
        first_period = pd.Timestamp(start).to_period(freq).start_time
        out = out[out["period_start"] >= first_period]
    return out.reset_index(drop=True)


def date_ticks(dates: pd.Series) -> dict:
    """
    Choose how often to put a date label on the x axis.

    Vega-Lite picks ticks on its own, but on short ranges it can add ticks
    between days, which repeats the same ``YYYY-MM-DD`` label. Choosing a
    calendar step from the length of the range avoids that.

    Parameters
    ----------
    dates : pd.Series
        The dates on the chart, as datetimes.

    Returns
    -------
    dict
        A Vega-Lite ``tickCount`` value, e.g. ``{"interval": "month", "step": 1}``.
    """
    span_days = (dates.max() - dates.min()).days
    if span_days <= 10:
        return {"interval": "day", "step": 1}
    if span_days <= 35:
        return {"interval": "week", "step": 1}
    if span_days <= 70:
        return {"interval": "week", "step": 2}
    if span_days <= 200:
        return {"interval": "month", "step": 1}
    if span_days <= 400:
        return {"interval": "month", "step": 2}
    if span_days <= 1100:
        return {"interval": "month", "step": 6}
    return {"interval": "year", "step": 1}


def format_value(value: float, value_format: str, unit: str) -> str:
    """
    Turn a number into tooltip text such as ``"160.4 lb"``.

    Parameters
    ----------
    value : float
        The number. NaN (no value that day) gives ``"–"``.
    value_format : str
        Python format spec, e.g. ``".1f"`` or ``",.0f"``.
    unit : str
        Unit written after the number, e.g. ``"lb"`` or ``"kcal"``.

    Returns
    -------
    str
        The formatted text.
    """
    if pd.isna(value):
        return "–"
    return f"{value:{value_format}} {unit}"


def time_series_chart(
    view: pd.DataFrame,
    date_column: str,
    value_column: str,
    settings: ChartSettings,
    lines: dict[str, str],
    y_title: str,
    unit: str,
    value_format: str,
    zero: bool,
    alt_text: str,
) -> None:
    """
    Draw a line chart of a value and its rolling average over time.

    The raw values are a thin line with dots, the rolling average a bold
    line. Each line keeps the same colour whichever lines are shown.

    Hovering anywhere on the chart picks the nearest date: a grey rule
    marks it, the visible lines get a dot there, and one tooltip shows the
    date, the raw value and the average. The tooltip always shows both
    values, even when a line is hidden, so the exact numbers are always
    one hover away; hiding a line only tidies the picture.

    Parameters
    ----------
    view : pd.DataFrame
        The rows to plot, with ``date_column``, ``value_column`` and
        ``rolling_avg`` (see ``add_rolling_average``). Must not be empty.
    date_column : str
        Name of the date column.
    value_column : str
        Name of the column with the raw values.
    settings : ChartSettings
        From ``chart_controls``; decides which lines are drawn.
    lines : dict[str, str]
        Legend label for each line, keyed ``RAW`` and ``AVERAGE``.
    y_title : str
        Title of the y axis, e.g. ``"Weight (lb)"``.
    unit : str
        Unit shown after values in the tooltip, e.g. ``"lb"``.
    value_format : str
        Python format spec for tooltip values, e.g. ``".1f"``.
    zero : bool
        Start the y axis at zero (good for calories) or fit it to the data
        (good for weight, which only changes a little).
    alt_text : str
        Accessible name of the chart.
    """
    raw_label = lines[RAW]
    avg_label = f"{settings.window_days}-day average"
    labels = {value_column: raw_label, "rolling_avg": avg_label}

    # Long data (one row per date and line) draws the lines. A missing
    # value (e.g. no raw value that day) is dropped, so it can't break a line.
    long = view.melt(
        id_vars=date_column,
        value_vars=[value_column, "rolling_avg"],
        var_name="series",
        value_name="value",
    ).dropna(subset=["value"])
    long["series"] = long["series"].map(labels)
    shown = [raw_label if line == RAW else avg_label for line in settings.lines]

    # Wide data (one row per date, both values as text) feeds the tooltip
    wide = view[[date_column]].copy()
    wide["raw_text"] = view[value_column].map(lambda v: format_value(v, value_format, unit))
    wide["avg_text"] = view["rolling_avg"].map(lambda v: format_value(v, value_format, unit))

    # The date nearest the pointer. empty=False means "nothing selected"
    # until the pointer is over the chart, so no rule or dots show at first.
    hover = alt.selection_point(
        nearest=True, on="pointerover", clear="pointerout", fields=[date_column], empty=False
    )
    x = alt.X(
        f"{date_column}:T",
        title="Date",
        axis=alt.Axis(format=DATE_FORMAT, labelOverlap=True, tickCount=date_ticks(view[date_column])),
    )
    base = alt.Chart(long).encode(
        x=x,
        y=alt.Y("value:Q", title=y_title, scale=alt.Scale(zero=zero)),
        # A fixed domain keeps each line's colour the same when the other
        # one is hidden. The legend only lists the lines that are shown.
        color=alt.Color(
            "series:N",
            title=None,
            scale=alt.Scale(domain=[raw_label, avg_label], range=[RAW_COLOR, AVERAGE_COLOR]),
            legend=alt.Legend(orient="bottom", values=shown),
        ),
    )
    layers = []
    if RAW in settings.lines:
        layers.append(
            base.transform_filter(alt.datum.series == raw_label).mark_line(point=True, opacity=0.5)
        )
    if AVERAGE in settings.lines:
        layers.append(base.transform_filter(alt.datum.series == avg_label).mark_line(strokeWidth=3))
    # A bigger dot on each visible line at the hovered date
    layers.append(
        base.transform_filter(alt.FieldOneOfPredicate(field="series", oneOf=shown))
        .mark_point(filled=True, size=80)
        .encode(opacity=alt.condition(hover, alt.value(1), alt.value(0)))
    )
    # One rule per date. They are invisible until hovered, but they hold the
    # selection and the tooltip with both values.
    layers.append(
        alt.Chart(wide)
        .mark_rule(color="gray", strokeWidth=1)
        .encode(
            x=x,
            opacity=alt.condition(hover, alt.value(0.6), alt.value(0)),
            tooltip=[
                alt.Tooltip(f"{date_column}:T", title="Date", format=DATE_FORMAT),
                alt.Tooltip("raw_text:N", title=raw_label),
                alt.Tooltip("avg_text:N", title=avg_label),
            ],
        )
        .add_params(hover)
    )
    # height="container" makes the plot fill the fixed CHART_HEIGHT element
    chart = alt.layer(*layers).properties(height="container")
    st.altair_chart(chart, height=CHART_HEIGHT, alt=alt_text)


def weight_chart(view: pd.DataFrame, unit: str, settings: ChartSettings) -> None:
    """
    Draw the weight chart, or a note if there is nothing to draw.

    Parameters
    ----------
    view : pd.DataFrame
        Weigh-ins to plot, with ``weigh_date``, ``weight`` (in the display
        unit) and ``rolling_avg``.
    unit : str
        The display unit, ``"lb"`` or ``"kg"``.
    settings : ChartSettings
        From ``chart_controls``.
    """
    if view.empty:
        st.info("No weigh-ins in this time period. Try a longer one.")
    elif not settings.lines:
        st.info("Choose at least one line to show.")
    else:
        time_series_chart(
            view,
            date_column="weigh_date",
            value_column="weight",
            settings=settings,
            lines=WEIGHT_LINES,
            y_title=f"Weight ({unit})",
            unit=unit,
            value_format=".1f",
            zero=False,
            alt_text="Weight over time",
        )


@st.fragment
def show_weight_over_time(weigh_ins: pd.DataFrame, unit: str, key: str) -> None:
    """
    Show the weight chart with its controls underneath.

    This is a fragment: changing a control reruns only this chart, not the
    whole page.

    Parameters
    ----------
    weigh_ins : pd.DataFrame
        All of the user's weigh-ins, oldest first, with ``weigh_date`` and a
        ``weight`` column already converted to the display unit.
    unit : str
        The display unit, ``"lb"`` or ``"kg"``.
    key : str
        Prefix for the widget keys. Must be unique on the page.
    """
    if weigh_ins.empty:
        st.info("No weigh-ins yet. Log one on the My Profile page to see your chart.")
        return
    # Reserve the spot above the controls, then fill it once they are read
    plot = st.container()
    settings = chart_controls(key, WEIGHT_LINES)
    # Average over the full history first, so the start of the chart is accurate
    averaged = add_rolling_average(weigh_ins, "weigh_date", "weight", settings.window_days)
    with plot:
        weight_chart(filter_dates(averaged, "weigh_date", settings.start, settings.end), unit, settings)


def aligned_domains(change: pd.Series, pct: pd.Series) -> tuple[list[float], list[float]]:
    """
    Choose y axis ranges for the change (left) and % change (right) axes.

    Each axis has its own scale, so on their own the two zeros would sit at
    different heights. Here the left range ``[lo, hi]`` always includes 0
    (with 10% padding), and the right range is the same range times one
    factor ``k``: ``[lo * k, hi * k]``. Multiplying both ends by the same
    number keeps 0 at the same height on both axes.

    ``k`` is the smallest factor that still fits every % value, worked out
    separately for the top and the bottom, plus 10% headroom. A single ``max|pct| / max|change|``
    could cut off a value on the other side, because each % is divided by a
    different previous weight. If there is nothing to scale (all changes
    zero, or no % values), ``k`` is 1, so nothing is ever divided by zero.

    Parameters
    ----------
    change : pd.Series
        The changes, in lb or kg.
    pct : pd.Series
        The percentage changes (e.g. ``-0.8`` for -0.8%).

    Returns
    -------
    tuple[list[float], list[float]]
        The left domain ``[lo, hi]`` and the right domain ``[lo * k, hi * k]``.
    """
    lo = min(float(change.min()), 0.0)
    hi = max(float(change.max()), 0.0)
    span = (hi - lo) or 1.0  # all zero: still draw a small range around 0
    lo -= 0.1 * span
    hi += 0.1 * span

    pct = pct.dropna()
    k = 0.0
    if not pct.empty:
        # lo < 0 < hi after padding, so neither division is by zero
        k = max(float(pct.max()) / hi, float(pct.min()) / lo)
    if not k > 0:  # also catches NaN
        k = 1.0
    # 10% headroom, so the biggest % doesn't sit right on the axis edge
    k *= 1.1
    return [lo, hi], [lo * k, hi * k]


def weight_change_chart(
    changes: pd.DataFrame,
    unit: str,
    freq: str,
    lines: list[str],
    labels: dict[str, str],
    chart_type: str,
    show_pct: bool,
) -> None:
    """
    Draw the weight change chart: gains and losses per period.

    The change in lb or kg uses the left axis, as bars (orange gain, blue
    loss) or as solid lines (grey weigh-ins, blue average). With
    ``show_pct``, the % change is added as dashed lines on a right axis.
    Hovering picks the nearest period: a grey rule marks it and one tooltip
    lists every visible source's change (and %) and its value at the end
    of the period.

    Parameters
    ----------
    changes : pd.DataFrame
        Output of ``period_changes`` for each source, stacked, with an
        extra ``line`` column holding ``RAW`` or ``AVERAGE``.
    unit : str
        The display unit, ``"lb"`` or ``"kg"``.
    freq : str
        ``"D"``, ``"W"`` or ``"M"``, for the axis title and tooltip.
    lines : list[str]
        The sources shown, weigh-ins (``RAW``) first.
    labels : dict[str, str]
        Label for each source, e.g. ``{RAW: "Weigh-ins", AVERAGE: "7-day average"}``.
    chart_type : str
        ``"Bars"`` or ``"Lines"``.
    show_pct : bool
        Add the % change on a right-hand axis.
    """
    data = changes.copy()
    data["source"] = data["line"].map(labels)
    # Category labels (not dates) on the x axis let two sources sit side by
    # side in each period. YYYY-MM-DD text also sorts in date order.
    data["period_label"] = data["period_start"].dt.strftime(DATE_FORMAT)
    data["period_text"] = {
        "D": data["period_label"],
        "W": "Week of " + data["period_label"],
        "M": data["period_start"].dt.strftime("%Y-%m"),
    }[freq]
    data["direction"] = data["change"].map(lambda c: "Gain" if c > 0 else "Loss")
    # Vega-Lite's "%" format multiplies by 100, so the right axis plots fractions
    data["pct_fraction"] = data["pct"] / 100
    data["change_text"] = [
        format_value(c, "+.1f", unit) + (f" ({p:+.1f}%)" if show_pct and not pd.isna(p) else "")
        for c, p in zip(data["change"], data["pct"])
    ]
    data["end_text"] = data["value"].map(lambda v: format_value(v, ".1f", unit))
    data["last_text"] = data["last_date"].dt.strftime(DATE_FORMAT)

    sources = [labels[line] for line in lines]
    left_domain, right_domain = aligned_domains(data["change"], data["pct"])
    change_title = f"Change ({unit})"
    pct_title = "Change (%)"
    x = alt.X(
        "period_label:O",
        title={"D": "Day", "W": "Week starting", "M": "Month starting"}[freq],
        axis=alt.Axis(labelOverlap=True, labelAngle=0),
    )
    left_y = alt.Y("change:Q", title=change_title, scale=alt.Scale(domain=left_domain))
    # The dash pattern says which axis a line belongs to. Each layer adds a
    # "measure" field, and they share one strokeDash scale and legend.
    dash = alt.StrokeDash(
        "measure:N",
        title=None,
        scale=alt.Scale(domain=[change_title, pct_title], range=[SOLID, DASHED]),
        # symbolType="stroke" draws the legend entries as solid and dashed lines
        legend=alt.Legend(
            orient="bottom",
            symbolType="stroke",
            symbolStrokeColor="gray",
            symbolStrokeWidth=2,
            symbolSize=300,
            values=[change_title, pct_title] if chart_type == "Lines" else [pct_title],
        ),
    )
    source_color = alt.Color(
        "source:N",
        title=None,
        sort=sources,
        scale=alt.Scale(domain=[labels[RAW], labels[AVERAGE]], range=[RAW_COLOR, AVERAGE_COLOR]),
        legend=alt.Legend(orient="bottom", values=sources),
    )
    hover = alt.selection_point(
        nearest=True, on="pointerover", clear="pointerout", fields=["period_label"], empty=False
    )
    highlight = alt.condition(hover, alt.value(1), alt.value(0))

    # ---- Left axis: change in lb/kg, plus the one zero rule
    base = alt.Chart(data).encode(x=x)
    if chart_type == "Bars":
        bar_encoding = {
            "y": left_y,
            "color": alt.Color(
                "direction:N",
                title=None,
                scale=alt.Scale(domain=["Gain", "Loss"], range=[GAIN_COLOR, LOSS_COLOR]),
                legend=alt.Legend(orient="bottom"),
            ),
        }
        if len(lines) > 1:
            # Side by side bars, the weigh-in bar (first) paler than the average bar
            bar_encoding["xOffset"] = alt.XOffset("source:N", sort=sources)
            bar_encoding["opacity"] = alt.Opacity(
                "source:N",
                title=None,
                sort=sources,
                scale=alt.Scale(domain=sources, range=[0.45, 1.0]),
                legend=alt.Legend(orient="bottom"),
            )
        left_layers = [base.mark_bar().encode(**bar_encoding)]
    else:
        change_points = base.encode(y=left_y, color=source_color)
        # Dots are their own layers without strokeDash. Dots on the line
        # itself (point=True) would hide the solid/dashed legend entries.
        left_layers = [
            change_points.transform_calculate(measure=f"'{change_title}'").encode(strokeDash=dash).mark_line(),
            change_points.mark_point(filled=True, size=30, opacity=1),
            change_points.mark_point(filled=True, size=80).encode(opacity=highlight),
        ]
    zero_line = (
        alt.Chart(pd.DataFrame({"zero": [0]}))
        .mark_rule(color="gray")
        .encode(y=alt.Y("zero:Q", scale=alt.Scale(domain=left_domain)))
    )
    left = alt.layer(*left_layers, zero_line)

    # ---- Hover rules: one per period, holding the selection and the tooltip
    wide = data.pivot(index="period_label", columns="line", values=["change_text", "end_text"])
    wide.columns = [f"{line}_{name}" for name, line in wide.columns]
    wide = wide.reindex(columns=[f"{line}_{name}" for line in lines for name in ("change_text", "end_text")])
    wide = wide.fillna("–")
    wide = wide.join(data.groupby("period_label")[["period_text", "last_text"]].first()).reset_index()
    tooltip = [alt.Tooltip("period_text:N", title="Period")]
    for line in lines:
        tooltip.append(alt.Tooltip(f"{line}_change_text:N", title=f"{labels[line]} change"))
        tooltip.append(alt.Tooltip(f"{line}_end_text:N", title=f"{labels[line]} at period end"))
    tooltip.append(alt.Tooltip("last_text:N", title="Last date with data"))
    rules = (
        alt.Chart(wide)
        .mark_rule(color="gray", strokeWidth=1)
        .encode(x=x, opacity=alt.condition(hover, alt.value(0.6), alt.value(0)), tooltip=tooltip)
        .add_params(hover)
    )

    if not show_pct:
        chart = alt.layer(left, rules)
    else:
        # ---- Right axis: % change as dashed lines
        pct_points = base.encode(
            y=alt.Y(
                "pct_fraction:Q",
                title=pct_title,
                scale=alt.Scale(domain=[d / 100 for d in right_domain]),
                axis=alt.Axis(orient="right", format="+.1%", titleColor=PCT_LINE_COLOR),
            ),
        )
        pct_base = pct_points.transform_calculate(measure=f"'{pct_title}'").encode(strokeDash=dash)
        # One light green line per source, in both chart types; with two
        # sources the weigh-in line is paler, like its bars
        pct_lines = pct_base.mark_line(color=PCT_LINE_COLOR, strokeWidth=2.5)
        pct_dots = pct_points.mark_point(filled=True, size=30, color=PCT_LINE_COLOR, opacity=1)
        layers = []
        if len(lines) > 1:
            by_source = alt.Opacity(
                "source:N", sort=sources, scale=alt.Scale(domain=sources, range=[0.45, 1.0])
            )
            pct_lines = pct_lines.encode(opacity=by_source, detail="source:N")
            pct_dots = pct_dots.encode(opacity=by_source)
        if chart_type == "Lines":
            layers.append(
                pct_points.mark_point(filled=True, size=80, color=PCT_LINE_COLOR).encode(opacity=highlight)
            )
        right = alt.layer(pct_lines, pct_dots, *layers)
        # Two y axes: left in lb/kg, right in %. Their domains line up at 0.
        chart = alt.layer(left, right, rules).resolve_scale(y="independent")

    chart = chart.properties(height="container")
    st.altair_chart(chart, height=CHART_HEIGHT, alt="Weight change per period")


@st.fragment
def show_weight_change(weigh_ins: pd.DataFrame, unit: str, key: str) -> None:
    """
    Show the weight change chart (gain or loss per period) with its controls.

    The user picks daily, weekly or monthly periods, bars or lines, whether
    to add the % change on a right-hand axis, and whether to base it on the
    raw weigh-ins, the rolling average, or both. The rolling average is the
    default because it smooths out day-to-day swings such as water weight.

    This is a fragment: changing a control reruns only this chart.

    Parameters
    ----------
    weigh_ins : pd.DataFrame
        All of the user's weigh-ins, oldest first, with ``weigh_date`` and a
        ``weight`` column already converted to the display unit.
    unit : str
        The display unit, ``"lb"`` or ``"kg"``.
    key : str
        Prefix for the widget keys. Must be unique on the page.
    """
    if weigh_ins.empty:
        st.info("No weigh-ins yet. Log one on the My Profile page to see your chart.")
        return
    plot = st.container()
    with st.container(horizontal=True, vertical_alignment="bottom"):
        freq = st.segmented_control(
            "Compare",
            list(GRANULARITIES),
            default="W",
            required=True,
            format_func=GRANULARITIES.get,
            key=f"{key}_granularity",
            persist_state=PERSIST,
        )
        chart_type = st.segmented_control(
            "Chart",
            CHANGE_CHART_TYPES,
            default="Bars",
            required=True,
            key=f"{key}_chart_type",
            persist_state=PERSIST,
        )
        show_pct = st.toggle("% change", value=True, key=f"{key}_pct", persist_state=PERSIST)
    settings = chart_controls(key, WEIGHT_LINES, default_lines=[AVERAGE], lines_label="Based on")

    # Average over the full history first, so every period-end average is accurate
    averaged = add_rolling_average(weigh_ins, "weigh_date", "weight", settings.window_days)
    labels = {RAW: WEIGHT_LINES[RAW], AVERAGE: f"{settings.window_days}-day average"}
    columns = {RAW: "weight", AVERAGE: "rolling_avg"}
    parts = []
    for line in settings.lines:
        part = period_changes(averaged, "weigh_date", columns[line], freq, settings.start, settings.end)
        part["line"] = line
        parts.append(part)

    with plot:
        if not settings.lines:
            st.info("Choose weigh-ins, the rolling average, or both.")
        elif all(part.empty for part in parts):
            st.info("Not enough weigh-ins in this time period to compare. Try a longer one.")
        else:
            changes = pd.concat([part for part in parts if not part.empty])
            # Always weigh-ins first, whatever order the pills were clicked in
            lines = [line for line in (RAW, AVERAGE) if line in settings.lines]
            weight_change_chart(changes, unit, freq, lines, labels, chart_type, show_pct)


@st.fragment
def show_macros_over_time(user_id: int, key: str) -> None:
    """
    Show one macro's daily totals and rolling average over time, with controls.

    Only one macro is shown at a time. Calories (hundreds to thousands of
    kcal) and grams (tens) have very different scales, so on a shared axis
    the gram lines would be flat along the bottom. Picking one macro keeps
    a single, readable y axis.

    Days with nothing logged are left out, not counted as zero, because a
    day you didn't log is not a day you ate nothing. The rolling average is
    therefore the mean of the *logged* days in the window.

    This is a fragment: changing a control reruns only this chart.

    Parameters
    ----------
    user_id : int
        The user whose log to chart.
    key : str
        Prefix for the widget keys. Must be unique on the page.
    """
    plot = st.container()
    macro = st.segmented_control(
        "Show",
        list(MACROS),
        default="calories",
        required=True,
        format_func=MACROS.get,
        key=f"{key}_macro",
        persist_state=PERSIST,
    )
    settings = chart_controls(key, MACRO_LINES)

    # Load the extra days before the start that the first averages need
    load_from = None if settings.start is None else settings.start - timedelta(days=settings.window_days)
    totals = food_logs.get_daily_totals(user_id, load_from, settings.end)
    averaged = add_rolling_average(totals, "log_date", macro, settings.window_days)
    view = filter_dates(averaged, "log_date", settings.start, settings.end)

    with plot:
        if view.empty:
            st.info("Nothing logged in this time period. Log food on the Nutrition page, or try a longer period.")
        elif not settings.lines:
            st.info("Choose at least one line to show.")
        else:
            time_series_chart(
                view,
                date_column="log_date",
                value_column=macro,
                settings=settings,
                lines=MACRO_LINES,
                y_title=MACROS[macro],
                unit="kcal" if macro == "calories" else "g",
                value_format=",.0f" if macro == "calories" else ".1f",
                zero=True,
                alt_text=f"{MACROS[macro]} per day over time",
            )
