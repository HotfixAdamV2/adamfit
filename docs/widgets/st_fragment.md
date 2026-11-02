# st.fragment

A decorator that turns a function into a "fragment": a part of the page that can rerun on its own. When a widget inside the fragment changes, only that function runs again instead of the whole page script. Useful for a chart with its own controls, so tweaking them doesn't reload everything else on the page.

## Basic example
```python
@st.fragment
def show_macros_over_time(user_id: int, key: str) -> None:
    macro = st.segmented_control("Show", list(MACROS), default="calories", key=f"{key}_macro")
    ...  # load data and draw the chart


show_macros_over_time(user_id, key="home_macros")
```

When the page runs normally, the fragment runs as part of it. When one of its own widgets changes, only the fragment reruns, using the arguments it was last called with. Code outside the fragment (and other fragments) is left as it was. A full page rerun, such as `st.rerun()` after a save, runs it again with fresh arguments.

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `func` | The function to turn into a fragment (given automatically when used as `@st.fragment`) | required |
| `run_every` | Rerun the fragment on a timer, e.g. `"10s"` | None |
| `key` | A name so a callback can rerun just this fragment with `st.rerun("<key>")` | None |
| `parallel` | Run this fragment at the same time as other parallel fragments during a full rerun | `False` |

## Used in
- [Charts over time](../charts.md): `show_weight_over_time`, `show_weight_change` and `show_macros_over_time`, on the [Home page](../home_page.md), [My Profile page](../profile_page.md) and [Nutrition page](../nutrition_page.md)
- [My Profile page](../profile_page.md): the page's own `show_weight_over_time` section
