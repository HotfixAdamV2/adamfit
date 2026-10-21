"""Small helpers shared by several pages."""

from collections.abc import Callable

import pandas as pd
import streamlit as st

from adamfit.nutrition import MACROS, scale_entries, to_amount, totals_row

_FLASH_KEY = "_flash"


def flash(message: str, kind: str = "success") -> None:
    """
    Store a message to show after the next rerun.

    ``st.rerun()`` wipes anything already drawn, so a message shown just
    before it would vanish. Call this, then ``st.rerun()``, and call
    ``show_flash`` near the top of the page.

    Parameters
    ----------
    message : str
        The message to show.
    kind : str, optional
        ``"success"`` (green box) or ``"error"`` (red box).
    """
    st.session_state[_FLASH_KEY] = (message, kind)


def show_flash() -> None:
    """
    Show and clear the message stored by ``flash``, if there is one.
    """
    stored = st.session_state.pop(_FLASH_KEY, None)
    if stored is None:
        return
    message, kind = stored
    if kind == "error":
        st.error(message)
    else:
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


def macro_tiles(totals: pd.Series) -> None:
    """
    Show macro totals as a row of boxed tiles, one per macro.

    Calories are shown as a whole number and grams with one decimal. The
    row wraps onto more lines on small screens.

    Parameters
    ----------
    totals : pd.Series
        Values keyed by the macro column names in ``MACROS``, e.g. one row
        of ``nutrition.totals_row``.
    """
    with st.container(horizontal=True):
        for column, label in MACROS.items():
            value = float(totals[column])
            st.metric(label, f"{value:,.0f}" if column == "calories" else f"{value:.1f}", border=True)


def item_picker(
    options: dict[str, dict],
    key: str,
    on_add: Callable[[str, float], None],
    label: str = "Food or recipe",
) -> None:
    """
    Show category filters, then a searchable item list, a servings box and
    an Add button in one row.

    The Category and Sub-category boxes narrow the item list. Sub-category
    only has choices once a category is picked. If the chosen item is
    filtered out, the item list is cleared. Once an item is chosen, a
    caption shows what one serving is (e.g. "1 serving = 30 g") and the
    servings box starts at 1. When Add is clicked, ``on_add`` is called with
    the chosen key and the number of servings, and the picker is cleared.

    Parameters
    ----------
    options : dict[str, dict]
        Items to choose from, keyed by an id string such as ``"food:12"``.
        Each value needs ``label``, ``serving_size``, ``serving_unit``,
        ``category`` and ``sub_category`` (None when the item has no
        sub-category, such as a recipe).
    key : str
        Prefix for the widget keys. Must be unique on the page.
    on_add : Callable[[str, float], None]
        Called with ``(option_key, servings)`` when Add is clicked.
    label : str, optional
        Label for the item list.
    """
    item_key = f"{key}_item"
    category_key = f"{key}_category"
    sub_key = f"{key}_sub_category"

    def _add() -> None:
        """
        Pass the chosen item to ``on_add``, then clear the picker.
        """
        choice = st.session_state.get(item_key)
        servings = st.session_state.get(f"{key}_servings_{choice}")
        if choice is None or not servings:
            return
        on_add(choice, servings)
        st.session_state[item_key] = None

    def _reset_sub_category() -> None:
        """
        Show every sub-category again when a new category is picked.
        """
        st.session_state[sub_key] = "All"

    # dict.fromkeys drops repeats but keeps the order of the options
    categories = ["All", *dict.fromkeys(option["category"] for option in options.values())]
    # A widget's value can only be changed before it is drawn, so any choice
    # that is no longer on offer is reset here, before the boxes below
    if st.session_state.get(category_key) not in categories:
        st.session_state[category_key] = "All"

    with st.container(horizontal=True):
        category = st.selectbox(
            "Category",
            categories,
            key=category_key,
            on_change=_reset_sub_category,
            width=220,
        )
        sub_categories = ["All"]
        if category != "All":
            sub_categories += [
                *dict.fromkeys(
                    option["sub_category"]
                    for option in options.values()
                    if option["category"] == category and option["sub_category"] is not None
                )
            ]
        if st.session_state.get(sub_key) not in sub_categories:
            st.session_state[sub_key] = "All"
        sub_category = st.selectbox(
            "Sub-category",
            sub_categories,
            key=sub_key,
            disabled=len(sub_categories) == 1,
            width=220,
        )

    visible = [
        option_key
        for option_key, option in options.items()
        if category in ("All", option["category"]) and sub_category in ("All", option["sub_category"])
    ]
    if st.session_state.get(item_key) is not None and st.session_state[item_key] not in visible:
        st.session_state[item_key] = None

    with st.container(horizontal=True, vertical_alignment="bottom"):
        choice = st.selectbox(
            label,
            options=visible,
            format_func=lambda k: options[k]["label"],
            index=None,
            placeholder="Type to search..." if visible else "Nothing matches these filters",
            key=item_key,
        )
        if choice is None:
            st.number_input("Servings", value=None, disabled=True, width=150, key=f"{key}_servings_none")
        else:
            option = options[choice]
            # A key per item resets the box to 1 serving when the item changes
            st.number_input(
                "Servings",
                min_value=0.25,
                value=1.0,
                step=0.25,
                format="%.2f",
                width=150,
                key=f"{key}_servings_{choice}",
            )
            one_serving = to_amount(1, option["serving_size"])
            st.caption(f"1 serving = {one_serving:g} {option['serving_unit']}", width="content")
        st.button("Add", icon=":material/add:", type="primary", disabled=choice is None, on_click=_add)


# ---- Staged (unsaved) changes ------------------------------------------
# The Daily log and the recipe ingredients do not write to the database on
# every click. Adds, servings edits and deletes are collected in
# st.session_state as a "changes" dictionary:
#
#     {
#         "adds": {-1: {"option_key": "food:12", "servings": 1.5}},
#         "updates": {57: 2.0},   # row id -> new servings
#         "deletes": [58],        # row ids
#     }
#
# Staged adds have no database id yet, so they get temporary negative ids.
# The table is drawn from the database rows with these changes applied, and
# nothing is written until the user presses Save changes.


def pending_changes(key: str) -> dict:
    """
    Return the staged changes stored under ``key``, creating them if needed.

    Parameters
    ----------
    key : str
        Session state key, e.g. ``"log_changes_2026-10-19"``.

    Returns
    -------
    dict
        The changes dictionary, with ``adds``, ``updates`` and ``deletes``.
        Changing it changes what is stored in session state.
    """
    return st.session_state.setdefault(key, {"adds": {}, "updates": {}, "deletes": []})


def count_changes(changes: dict) -> int:
    """
    Count the staged changes.

    Parameters
    ----------
    changes : dict
        A changes dictionary from ``pending_changes``.

    Returns
    -------
    int
        Number of staged adds, servings edits and deletes.
    """
    return len(changes["adds"]) + len(changes["updates"]) + len(changes["deletes"])


def stage_add(changes: dict, option_key: str, servings: float) -> None:
    """
    Stage a new row, giving it the next free temporary (negative) id.

    Parameters
    ----------
    changes : dict
        A changes dictionary from ``pending_changes``.
    option_key : str
        The picker option added, e.g. ``"food:12"``.
    servings : float
        Number of servings.
    """
    temp_id = min([0, *changes["adds"]]) - 1
    changes["adds"][temp_id] = {"option_key": option_key, "servings": servings}


def stage_update(changes: dict, row_id: int, servings: float) -> None:
    """
    Stage a new number of servings for a row.

    Parameters
    ----------
    changes : dict
        A changes dictionary from ``pending_changes``.
    row_id : int
        Database id of the row, or a temporary id for a staged add.
    servings : float
        New number of servings.
    """
    if row_id < 0:
        changes["adds"][row_id]["servings"] = servings
    else:
        changes["updates"][row_id] = servings


def stage_delete(changes: dict, row_id: int) -> None:
    """
    Stage the removal of a row.

    Removing a staged add simply forgets it, as it was never saved.

    Parameters
    ----------
    changes : dict
        A changes dictionary from ``pending_changes``.
    row_id : int
        Database id of the row, or a temporary id for a staged add.
    """
    if row_id < 0:
        changes["adds"].pop(row_id, None)
    else:
        changes["updates"].pop(row_id, None)
        if row_id not in changes["deletes"]:
            changes["deletes"].append(row_id)


def apply_changes(entries: pd.DataFrame, changes: dict, options: dict[str, dict]) -> pd.DataFrame:
    """
    Return the rows as they will be once the staged changes are saved.

    Parameters
    ----------
    entries : pd.DataFrame
        Rows from the database, indexed by id, in the shape
        ``nutrition.scale_entries`` expects.
    changes : dict
        A changes dictionary from ``pending_changes``.
    options : dict[str, dict]
        The picker options. Each value needs ``item_name``,
        ``serving_size``, ``serving_unit`` and the per-serving macro columns
        in ``MACROS``, to build the rows for staged adds.

    Returns
    -------
    pd.DataFrame
        ``entries`` without the deleted rows, with the edited servings, and
        with one row per staged add at the end (indexed by its temporary id).
        Staged adds whose item is no longer in ``options`` are removed from
        ``changes``.
    """
    view = entries.drop(index=[row_id for row_id in changes["deletes"] if row_id in entries.index])
    for row_id, servings in changes["updates"].items():
        if row_id in view.index:
            view.loc[row_id, "servings"] = servings

    # An item removed (e.g. in the Foods tab) after it was staged can't be
    # shown, so its staged add is dropped too, keeping table and save in step
    for temp_id in [t for t, add in changes["adds"].items() if add["option_key"] not in options]:
        del changes["adds"][temp_id]

    new_rows = pd.DataFrame(
        [
            {
                "item_name": options[add["option_key"]]["item_name"],
                "servings": add["servings"],
                "serving_size": options[add["option_key"]]["serving_size"],
                "serving_unit": options[add["option_key"]]["serving_unit"],
                **{column: options[add["option_key"]][column] for column in MACROS},
            }
            for add in changes["adds"].values()
        ],
        index=list(changes["adds"]),
        columns=entries.columns,
    )
    if new_rows.empty:
        return view
    if view.empty:
        return new_rows
    return pd.concat([view, new_rows])


def save_bar(key: str) -> bool:
    """
    Show Save changes and Revert changes buttons, and how many changes are unsaved.

    Both buttons are disabled when nothing is staged. Revert throws the
    staged changes away. Saving is left to the caller, because each table
    saves differently.

    Parameters
    ----------
    key : str
        Session state key of the changes (see ``pending_changes``). The
        button keys are ``"save_<key>"`` and ``"revert_<key>"``.

    Returns
    -------
    bool
        True on the run right after Save changes was clicked.
    """
    count = count_changes(pending_changes(key))
    with st.container(horizontal=True, vertical_alignment="center"):
        save = st.button(
            "Save changes",
            icon=":material/save:",
            type="primary",
            disabled=count == 0,
            key=f"save_{key}",
        )
        st.button(
            "Revert changes",
            icon=":material/undo:",
            disabled=count == 0,
            key=f"revert_{key}",
            on_click=lambda: st.session_state.pop(key, None),
        )
        if count:
            st.caption(f"{count} unsaved change{'s' if count != 1 else ''}", width="content")
    return save


def entries_editor(
    entries: pd.DataFrame,
    key: str,
    on_update: Callable[[int, float], None],
    on_delete: Callable[[int], None],
    alt: str,
    totals_as_tiles: bool = False,
) -> None:
    """
    Show an editable table of foods eaten, with the totals underneath.

    Only the Servings column can be edited, matching ``item_picker``. The
    Amount column next to it shows what those servings come to in the
    food's own unit (e.g. "45 g") and is read-only. Rows can be deleted by
    selecting them and pressing the delete key or the trash icon. Every
    change is passed to ``on_update`` or ``on_delete`` straight away (the
    Nutrition page stages it, see ``stage_update``), and the table redraws
    with whatever ``entries`` holds on the next run.

    Parameters
    ----------
    entries : pd.DataFrame
        Rows indexed by their database id, in the shape
        ``nutrition.scale_entries`` expects.
    key : str
        Prefix for the widget key. Must be unique on the page.
    on_update : Callable[[int, float], None]
        Called with ``(row_id, servings)`` when the servings change.
        ``row_id`` is the row's index value, so it may be a temporary id.
    on_delete : Callable[[int], None]
        Called with ``row_id`` when a row is deleted.
    alt : str
        Accessible name for the table.
    totals_as_tiles : bool, optional
        Show the totals as a row of boxed tiles (see ``macro_tiles``)
        instead of a one-row table lined up under the editor.
    """
    # Bumping the version gives the editor a fresh key, which clears its
    # edits once they have been handed to the callbacks
    version_key = f"{key}_version"
    st.session_state.setdefault(version_key, 0)
    editor_key = f"{key}_{st.session_state[version_key]}"
    ids = entries.index.tolist()

    def _save() -> None:
        """
        Hand the editor's changes to ``on_delete`` and ``on_update``.
        """
        changes = st.session_state[editor_key]
        deleted = set(changes["deleted_rows"])
        for position in deleted:
            on_delete(ids[position])
        for position, edits in changes["edited_rows"].items():
            servings = edits.get("servings")
            if position in deleted or not servings or servings <= 0:
                continue
            on_update(ids[position], servings)
        st.session_state[version_key] += 1

    scaled = scale_entries(entries)
    column_config = {
        "item_name": st.column_config.TextColumn("Item", width="large", disabled=True),
        "servings": st.column_config.NumberColumn(
            "Servings", min_value=0.25, step=0.25, format="%.2f", width="small", required=True
        ),
        "amount": st.column_config.TextColumn("Amount", width="small", disabled=True),
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
    totals = totals_row(scaled)
    if totals_as_tiles:
        macro_tiles(totals.iloc[0])
    else:
        st.dataframe(
            totals,
            hide_index=True,
            column_config=column_config,
            alt=f"Totals for: {alt}",
        )
