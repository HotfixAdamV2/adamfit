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

The letter after the column name tells Altair the data type: `T` time, `Q` number, `N` category. Charts can be stacked on top of each other with `+`, which is how the profile page draws both weigh-ins and the rolling average.

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `altair_chart` | The Altair chart object | required |
| `width` | `"stretch"` (fill the page) or pixels | `"stretch"` |
| `height` | Height in pixels | Chart's own height |
| `theme` | `"streamlit"` to match the app's style, or `None` | `"streamlit"` |

## Used in
- [My Profile page](../profile_page.md)
