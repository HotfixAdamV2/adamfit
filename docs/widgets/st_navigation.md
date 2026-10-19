# st.navigation, st.Page and st.page_link

`st.navigation` decides which pages exist and builds the sidebar menu from them. Each page is described with `st.Page`. Because `app.py` runs on every interaction, the menu can change, for example showing only the login page until someone logs in. `st.page_link` draws a clickable link to one of those pages.

## Basic example
```python
page = st.navigation([
    st.Page("pages/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("pages/profile.py", title="My Profile"),
])
page.run()  # runs the page the user picked
```

Pass a dictionary instead of a list to group pages under headings: `{"Me": [profile_page], "Library": [exercises_page]}`.

## Parameters
**st.navigation**
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `pages` | A list of `st.Page`s, or a dict of section name to list | required |
| `position` | `"sidebar"`, `"top"` or `"hidden"` | `"sidebar"` |

**st.Page**
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `page` | Path to the page's script (relative to `app.py`) | required |
| `title` | Name shown in the menu and browser tab | From file name |
| `icon` | Emoji or `:material/name:` icon | None |
| `default` | Page shown when the URL doesn't name one | `False` (first page) |
| `url_path` | Custom URL for the page | From file name |

**st.page_link**
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `page` | Path of the page (as registered in `st.navigation`) | required |
| `label` | Link text | The page's title |
| `icon` | Icon next to the text | None |

## Used in
- [App router (`app.py`)](../streamlit_basics.md#multipage-apps-and-the-router)
- [Home page](../home_page.md)
