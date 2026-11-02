# st.multiselect

A dropdown where you can pick several options. It returns a list of the picked options (an empty list when nothing is picked). Typing in the box searches the options.

## Basic example
```python
chosen_equipment = st.multiselect(
    "Equipment", list(equipment), format_func=equipment.get, placeholder="Any", key="exercise_filter_equipment"
)
```
Here the options are codes (`"barbell"`) and `format_func` shows their names ("Barbell"), so the list returned holds codes.

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text shown above the box | required |
| `options` | The choices | required |
| `default` | Options picked at first. Don't combine with setting the value through `st.session_state[key]` | None |
| `format_func` | Turns each option into the text shown | `str` |
| `key` | Unique name, also where the list is kept in `st.session_state` | None |
| `placeholder` | Grey hint shown when nothing is picked | "Choose options" |
| `max_selections` | Most options that can be picked | No limit |
| `on_change` | Function called before the rerun when the picks change | Rerun only |
| `disabled` | Grey out the box | `False` |

## Changing the value from code
A widget's value can only be set **before** it is drawn in a run. The Exercises page uses this to keep a muscle group out of Secondary once it is picked as Primary: it removes the group from both the options and `st.session_state[key]`, then draws the box.
```python
secondary_options = [group_id for group_id in group_names if group_id not in primary_ids]
st.session_state[f"{key}secondary"] = [
    group_id for group_id in st.session_state[f"{key}secondary"] if group_id in secondary_options
]
```

## Used in
- [Exercises page](../exercises_page.md): the Equipment and muscle group filters, and the primary and secondary muscle groups in the exercise pop-up
