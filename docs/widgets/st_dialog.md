# st.dialog

A decorator that turns a function into a pop-up (a "modal dialog"). Calling the function opens the pop-up, and whatever the function draws appears inside it. The rest of the page is greyed out until the pop-up closes.

A pop-up behaves like a [fragment](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment): when you use a widget inside it, only the dialog function reruns, not the whole page. To close it from code, call `st.rerun()`. That reruns the whole page, and the pop-up stays closed as long as the page doesn't call the dialog function again.

## Basic example
```python
@st.dialog("Cast your vote")
def vote(item):
    reason = st.text_input("Because...")
    if st.button("Submit"):
        st.session_state["vote"] = {"item": item, "reason": reason}
        st.rerun()


if st.button("A"):
    vote("A")
```

## One function, two titles
The title is fixed when you decorate the function. To get two pop-ups with different titles from the same code, apply the decorator as a normal function call:
```python
add_food_dialog = st.dialog("Add food", width="medium", on_dismiss=close_food_dialog)(food_form)
edit_food_dialog = st.dialog("Edit food", width="medium", on_dismiss=close_food_dialog)(food_form)
```

## Keeping it open across reruns
In the basic example, the pop-up opens only on the run right after the button click. If anything else reruns the whole page, the pop-up closes. A sturdier pattern is to remember in `st.session_state` that it is open. Call the dialog function on every run while that key exists, and remove the key when the pop-up closes (Save, Cancel, or the X via `on_dismiss`).

## Forms and callbacks inside a pop-up
Because a pop-up reruns on its own, widgets inside it can react straight away (e.g. choosing "+ New category" shows extra boxes). Inside a [st.form](st_form.md) they couldn't: nothing reruns until the form is submitted. That is why the food pop-up uses plain `st.button`s for Save and Cancel instead of a form.

Two more things to know:
- Data read *outside* the pop-up function is not read again when only the pop-up reruns. The Manage categories pop-up reads the categories inside itself, so a change made in it shows straight away.
- A button's `on_click` callback runs before the pop-up is drawn again. That makes it the place to save and then clear input boxes (a widget's value can't be changed once it is drawn). The callback stores a message in `st.session_state`, and the pop-up shows it on its next draw.

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `title` | Text at the top of the pop-up. Cannot be empty | required |
| `width` | `"small"` (up to 500 px), `"medium"` (750 px) or `"large"` (1280 px) | `"small"` |
| `dismissible` | Whether the user can close it with the X, Esc or a click outside it | `True` |
| `on_dismiss` | What happens when the user closes it that way: `"ignore"` (nothing), `"rerun"` (rerun the page) or a function to call before the rerun | `"ignore"` |
| `icon` | Emoji or `:material/name:` icon next to the title | None |
| `position` | `"center"`, or `"left"` / `"right"` for a full-height side drawer | `"center"` |

Only one pop-up can be open per run, and pop-ups can't be nested.

## Used in
- [Nutrition page](../nutrition_page.md): the Add food and Edit food pop-ups, and the Manage categories pop-up, in the Foods tab
