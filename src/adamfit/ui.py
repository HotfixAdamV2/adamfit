"""Small helpers shared by several pages."""

from collections.abc import Callable

import pandas as pd
import streamlit as st

from adamfit.nutrition import MACROS, amount_unit, scale_entries, to_amount, to_servings, totals_row

_FLASH_KEY = "_flash"


def flash(message: str) -> None:
    """
    Store a success message to show after the next rerun.

    ``st.rerun()`` wipes anything already drawn, so a message shown just
    before it would vanish. Call this, then ``st.rerun()``, and call
    ``show_flash`` near the top of the page.

    Parameters
    ----------
    message : str
        The message to show.
    """
    st.session_state[_FLASH_KEY] = message


def show_flash() -> None:
    """
    Show and clear the message stored by ``flash``, if there is one.
    """
    message = st.session_state.pop(_FLASH_KEY, None)
    if message:
        st.success(message)


def macro_column_config() -> dict:
    """
    Return column settings for the macro columns of a nutrition table.

    Returns
    -------
    dict
        ``st.column_config`` entries keyed by macro column name, read-only
        and formatted to whole calories and one-decimal grams.
    """
    return {
        column: st.column_config.NumberColumn(
            label,
            format="%.0f" if column == "calories" else "%.1f",
            width="small",
            disabled=True,
        )
        for column, label in MACROS.items()
    }


def item_picker(
    options: dict[str, dict],
    key: str,
    unit_system: str,
    on_add: Callable[[str, float], None],
    label: str = "Food or recipe",
) -> None:
    """
    Show a searchable item list, an amount box and an Add button in one row.

    The amount is entered in the item's own unit (weights in the user's
    preferred oz or g) and starts at one serving. When Add is clicked,
    ``on_add`` is called with the chosen key and the number of servings, and
    the picker is cleared.

    Parameters
    ----------
    options : dict[str, dict]
        Items to choose from, keyed by an id string such as ``"food:12"``.
        Each value needs ``label``, ``serving_size``, ``serving_unit`` and
        ``grams_per_unit`` (None unless the unit is a weight).
    key : str
        Prefix for the widget keys. Must be unique on the page.
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.
    on_add : Callable[[str, float], None]
        Called with ``(option_key, servings)`` to save the new row.
    label : str, optional
        Label for the item list.
    """
    item_key = f"{key}_item"

    def _add() -> None:
        """
        Save the chosen item, then clear the picker.
        """
        choice = st.session_state.get(item_key)
        amount = st.session_state.get(f"{key}_amount_{choice}")
        if choice is None or not amount:
            return
        option = options[choice]
        servings = to_servings(amount, option["serving_size"], option["grams_per_unit"], unit_system)
        if servings > 0:
            on_add(choice, servings)
        st.session_state[item_key] = None

    with st.container(horizontal=True, vertical_alignment="bottom"):
        choice = st.selectbox(
            label,
            options=list(options),
            format_func=lambda k: options[k]["label"],
            index=None,
            placeholder="Type to search...",
            key=item_key,
        )
        if choice is None:
            st.number_input("Amount", value=None, disabled=True, width=150, key=f"{key}_amount_none")
        else:
            option = options[choice]
            unit = amount_unit(option["serving_unit"], option["grams_per_unit"], unit_system)
            one_serving = to_amount(1, option["serving_size"], option["grams_per_unit"], unit_system)
            # A key per item resets the amount to one serving when the item changes
            st.number_input(
                f"Amount ({unit})",
                min_value=0.01,
                value=round(one_serving, 1),
                step=1.0,
                format="%.1f",
                width=150,
                key=f"{key}_amount_{choice}",
            )
        st.button("Add", icon=":material/add:", type="primary", disabled=choice is None, on_click=_add)


def entries_editor(
    entries: pd.DataFrame,
    key: str,
    unit_system: str,
    on_update: Callable[[int, float], None],
    on_delete: Callable[[int], None],
    alt: str,
) -> None:
    """
    Show an editable table of foods eaten, with a totals row underneath.

    Only the Amount column can be edited. Rows can be deleted by selecting
    them and pressing the delete key or the trash icon. Every change is saved
    straight away, and the table redraws with the new macros.

    Parameters
    ----------
    entries : pd.DataFrame
        Rows indexed by their database id, in the shape
        ``nutrition.scale_entries`` expects.
    key : str
        Prefix for the widget key. Must be unique on the page.
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.
    on_update : Callable[[int, float], None]
        Called with ``(row_id, servings)`` when an amount changes.
    on_delete : Callable[[int], None]
        Called with ``row_id`` when a row is deleted.
    alt : str
        Accessible name for the table.
    """
    # Bumping the version gives the editor a fresh key, which clears its
    # pending edits once they have been saved to the database
    version_key = f"{key}_version"
    st.session_state.setdefault(version_key, 0)
    editor_key = f"{key}_{st.session_state[version_key]}"
    ids = entries.index.tolist()

    def _save() -> None:
        """
        Write the editor's changes to the database.
        """
        changes = st.session_state[editor_key]
        deleted = set(changes["deleted_rows"])
        for position in deleted:
            on_delete(ids[position])
        for position, edits in changes["edited_rows"].items():
            amount = edits.get("amount")
            if position in deleted or not amount:
                continue
            row = entries.iloc[position]
            servings = to_servings(amount, row["serving_size"], row["grams_per_unit"], unit_system)
            if servings > 0:
                on_update(ids[position], servings)
        st.session_state[version_key] += 1

    scaled = scale_entries(entries, unit_system)
    column_config = {
        "item_name": st.column_config.TextColumn("Item", width="large", disabled=True),
        "amount": st.column_config.NumberColumn(
            "Amount", min_value=0.01, step=0.1, format="%.1f", width="small", required=True
        ),
        "unit": st.column_config.TextColumn("Unit", width="small", disabled=True),
        **macro_column_config(),
    }
    st.data_editor(
        scaled,
        hide_index=True,
        num_rows="delete",
        column_config=column_config,
        key=editor_key,
        on_change=_save,
        alt=alt,
    )
    st.dataframe(
        totals_row(scaled),
        hide_index=True,
        column_config=column_config,
        alt=f"Totals for: {alt}",
    )
