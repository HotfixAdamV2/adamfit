# st.link_button

A button that opens a web address in a **new browser tab**. By default clicking it does not rerun the app, so the current tab stays exactly as it was.

## Basic example
```python
st.link_button("Open Google", "https://www.google.com", icon=":material/open_in_new:")
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text on the button | required |
| `url` | Address to open in a new tab | required |
| `type` | `"primary"` (filled), `"secondary"` or `"tertiary"` (plain text) | `"secondary"` |
| `icon` | Icon next to the label, e.g. `":material/link:"` | `None` |
| `on_click` | `"ignore"` (just open the link), `"rerun"`, or a callback function | `"ignore"` |
| `disabled` | Greys the button out | `False` |
| `help` | Tooltip on hover | `None` |

If the address points back at the app itself, the new tab is a **new session**: it has its own `st.session_state`, so it is not logged in.

## Used in
- [My Profile page](../profile_page.md): **Connect Google Health**, which opens Google's consent page in a new tab
