# st.altair_chart

Displays a chart built with [Altair](https://altair-viz.github.io/), a Python charting library that ships with Streamlit. You describe the chart (data, which column goes on which axis, what kind of mark) and Altair draws it. Charts are interactive: hover for tooltips, scroll to zoom.

## Basic example
```python
chart = alt.Chart(df).mark_line(point=True).encode(
    x=alt.X("weigh_date:T", title="Date"),
    y=alt.Y("weight:Q", title="Weight (lb)", scale=alt.Scale(zero=False)),
)
st.altair_chart(chart)
```

The letter after the column name tells Altair the data type: `T` time, `Q` number, `N` category. Charts can be stacked on top of each other with `+` or `alt.layer(...)`, which is how the weight chart draws both weigh-ins and the rolling average.

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `altair_chart` | The Altair chart object | required |
| `width` | `"stretch"` (fill the page) or pixels | `"stretch"` |
| `height` | `"content"`, `"stretch"`, or a fixed height in pixels. Charts that should line up use the same number; add `.properties(height="container")` to the Altair chart so the plot fills it | `"content"` |
| `theme` | `"streamlit"` to match the app's style, or `None` | `"streamlit"` |
| `alt` | Short description of the chart for screen readers | None |

## Date axes
Every chart over time writes dates as `YYYY-MM-DD` (no weekday), on the axis and in the tooltip. `labelOverlap=True` hides labels that would run into each other, and `tickCount` sets the step between ticks (see `date_ticks` in `charts.py`):
```python
x=alt.X(
    "weigh_date:T",
    title="Date",
    axis=alt.Axis(format="%Y-%m-%d", labelOverlap=True, tickCount={"interval": "month", "step": 1}),
),
tooltip=[alt.Tooltip("weigh_date:T", title="Date", format="%Y-%m-%d")],
```

## Hover tooltip with several values
To show every line's value for one date in a single tooltip, use a *nearest point selection* on the date, and put the tooltip on a layer of vertical rules built from wide data (one row per date, one column per value):
```python
hover = alt.selection_point(nearest=True, on="pointerover", clear="pointerout", fields=["weigh_date"], empty=False)
rules = (
    alt.Chart(wide)
    .mark_rule(color="gray")
    .encode(
        x="weigh_date:T",
        opacity=alt.condition(hover, alt.value(0.6), alt.value(0)),
        tooltip=["weigh_date:T", "raw_text:N", "avg_text:N"],
    )
    .add_params(hover)
)
```
Other layers can react to the same selection, e.g. `opacity=alt.condition(hover, alt.value(1), alt.value(0))` on a point layer to put a dot on each line at the hovered date.

## Bar charts side by side
`mark_bar()` with a category x axis and `xOffset` puts several bars in each slot, e.g. one per source:
```python
alt.Chart(data).mark_bar().encode(
    x="period_label:O",
    xOffset="source:N",
    y="change:Q",
    color=alt.Color("direction:N", scale=alt.Scale(domain=["Gain", "Loss"], range=["#e8743b", "#2f7ed8"])),
)
```
A fixed `domain` and `range` on the colour scale keeps each category's colour the same, whichever categories are in the data.

## Two y axes
Layer two charts and give each its own y scale with `resolve_scale(y="independent")`. Put the second axis on the right with `axis=alt.Axis(orient="right")`. Group layers that should share an axis into their own `alt.layer(...)` first, or every layer gets its own axis:
```python
left = alt.layer(bars, zero_line)  # lb/kg, share the left axis
right = alt.layer(pct_lines, pct_dots)  # %, share the right axis
chart = alt.layer(left, right, rules).resolve_scale(y="independent")
```
Independent scales don't line up on their own. To keep 0 at the same height on both, set each `scale=alt.Scale(domain=[...])` by hand, with the right domain equal to the left one times a single factor (see `aligned_domains` in `charts.py`). The format `"+.1%"` multiplies by 100, so plot fractions (0.012 for +1.2%).

**Legend for dashed lines.** A `strokeDash` encoding on a small constant field (added with `transform_calculate`) gives a solid/dashed legend. Use `symbolType="stroke"`, and draw dots as separate `mark_point` layers: `mark_line(point=True)` makes the legend's line symbols invisible.

## Used in
- [Charts over time](../charts.md): the weight, weight change and macros charts, on the [Home page](../home_page.md), [My Profile page](../profile_page.md) and [Nutrition page](../nutrition_page.md)
