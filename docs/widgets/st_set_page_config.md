# st.set_page_config

Sets page-level options such as the browser tab title, icon and page width. Call it near the top of the script, before other Streamlit output.

## Basic example
```python
st.set_page_config(page_title="AdamFit", page_icon=":muscle:", layout="wide")
```

## Page width
- `"centered"` (the default) caps the content at roughly 736px wide. `"wide"` uses the full browser window, which helps wide tables avoid horizontal scrolling.
- AdamFit sets `layout="wide"` once in `app.py`. Every page runs inside that router, so it applies to all pages.
- A page can override it by calling `st.set_page_config(layout="centered")` at its top. Streamlit 1.4x and later allow repeated calls; the later call wins.
- For a custom width in between, you can inject CSS:
  ```python
  st.markdown(
      "<style>.block-container { max-width: 1200px; }</style>",
      unsafe_allow_html=True,
  )
  ```
  This is unofficial: it relies on Streamlit's internal class names, which may change between versions.

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `page_title` | Text shown in the browser tab | The script name |
| `page_icon` | Emoji, `:shortcode:` or image shown in the tab | Streamlit logo |
| `layout` | `"centered"` or `"wide"` | `"centered"` |
| `initial_sidebar_state` | `"auto"`, `"expanded"` or `"collapsed"` | `"auto"` |

## Used in
- [App router (`app.py`)](../streamlit_basics.md#multipage-apps-and-the-router)
