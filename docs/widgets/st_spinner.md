# st.spinner

Shows a spinning "busy" indicator with a message while the code inside its `with` block runs. It disappears when the block finishes.

## Basic example
```python
with st.spinner("Loading..."):
    data = slow_function()
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `text` | Message next to the spinner (supports markdown) | `"In progress..."` |
| `show_time` | Also show how many seconds have passed | `False` |

## Used in
- [My Profile page](../profile_page.md): while weigh-ins are fetched from Google Health
