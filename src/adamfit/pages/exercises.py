"""Exercises page: the user's exercise library, with filters, a details panel
for the selected exercise, pop-ups to add and edit exercises, and a pop-up to
manage muscle groups.

The page has one tab for now ("Library"). More tabs (e.g. workouts) will be
added later, so the tab code is kept separate from the pop-ups, which any
tab can open.
"""

import pandas as pd
import streamlit as st

from adamfit import auth, exercises
from adamfit.ui import flash, set_dialog_message, show_dialog_message, show_flash

user = auth.current_user()
user_id = user["user_id"]

st.title("Exercises")
show_flash()

# on_change="rerun" makes the tabs remember which one is open, and lets us
# run only the open tab's code. With more tabs this becomes, for example:
#     library_tab, workout_tab = st.tabs(["Library", "Workouts"], ...)
(library_tab,) = st.tabs(["Library"], key="exercises_tab", on_change="rerun")

# ---- Pop-up state ------------------------------------------------------
# A pop-up (st.dialog) closes as soon as a run doesn't draw it, so the page
# remembers in session state which pop-up is open and draws it on every run
# until one of its buttons, or its X, closes it. Only one can be open:
# - "editing_exercise" holds the id of the exercise being edited (None for a new one)
# - "managing_muscle_groups" is set while Manage muscle groups is open
EDITING_EXERCISE = "editing_exercise"
MANAGING_GROUPS = "managing_muscle_groups"
# A message shown inside the Manage muscle groups pop-up (see ui.set_dialog_message)
GROUP_MESSAGE = "muscle_group_message"
# Start of every widget key in the exercise pop-up, so they can be cleared together
FORM_PREFIX = "exercise_form_"
# The exercise table's key, and the id of the exercise selected in it
TABLE_KEY = "exercise_table"
SELECTED_EXERCISE = "selected_exercise"


def open_exercise_dialog(exercise_id: int | None) -> None:
    """
    Open the exercise pop-up on the next run.

    Parameters
    ----------
    exercise_id : int | None
        The exercise to edit, or None to add a new one.
    """
    st.session_state.pop(MANAGING_GROUPS, None)
    st.session_state[EDITING_EXERCISE] = exercise_id


def close_exercise_dialog() -> None:
    """
    Close the exercise pop-up and forget what was typed in it.

    The pop-up's boxes are filled in from session state when it opens (see
    ``exercise_form``), so their keys are removed here. Otherwise reopening
    the same exercise would show the unsaved values from last time.
    """
    st.session_state.pop(EDITING_EXERCISE, None)
    for widget_key in [k for k in st.session_state if str(k).startswith(FORM_PREFIX)]:
        del st.session_state[widget_key]


def open_group_dialog() -> None:
    """
    Open the Manage muscle groups pop-up on the next run.
    """
    close_exercise_dialog()
    st.session_state[MANAGING_GROUPS] = True


def close_group_dialog() -> None:
    """
    Close the Manage muscle groups pop-up and forget its last message.
    """
    st.session_state.pop(MANAGING_GROUPS, None)
    st.session_state.pop(GROUP_MESSAGE, None)


# ---- Add / Edit exercise pop-up ------------------------------------------


def exercise_form(exercise_id: int | None) -> None:
    """
    Show the exercise form inside the Add exercise or Edit exercise pop-up.

    The boxes start with the exercise's saved values, or with defaults for
    a new one (strength, bodyweight, no tags). The muscle group boxes only
    show for strength exercises, and a group picked as primary is taken
    out of the secondary choices. The picture box shows the current
    picture with a "Remove picture" tick box, or a preview of a newly
    chosen file. Save checks and writes everything in one transaction,
    Cancel closes without saving, and Remove exercise (edit only, after
    ticking the confirm box) removes it. An error is shown in the pop-up
    and the pop-up stays open.

    Parameters
    ----------
    exercise_id : int | None
        The exercise to edit, or None to add a new one.
    """
    # Read here, not once for the page: a pop-up reruns on its own when you
    # use it, so data read outside it would be stale
    types = exercises.get_exercise_types()
    equipment = exercises.get_equipment()
    groups = exercises.get_muscle_groups(user_id)

    if exercise_id is None:
        saved = {
            "exercise_name": "",
            "exercise_type": exercises.STRENGTH,
            "equipment": "bodyweight",
            "instructions": "",
            "primary_ids": [],
            "primary_names": [],
            "secondary_ids": [],
            "secondary_names": [],
        }
    else:
        saved = exercises.get_exercises(user_id).loc[exercise_id].to_dict()

    # The muscle group choices: every active group, plus any removed group
    # this exercise is already tagged with, so that tag still shows
    group_names = dict(zip(groups["muscle_group_id"].tolist(), groups["muscle_group_name"]))
    for group_id, name in zip(
        saved["primary_ids"] + saved["secondary_ids"], saved["primary_names"] + saved["secondary_names"]
    ):
        if group_id not in group_names:
            group_names[group_id] = f"{name} (removed)"

    # Fill the boxes in once, when the pop-up opens. Setting session state
    # (instead of passing value=) lets the code below change a box's value,
    # e.g. take a group out of Secondary when it is picked as Primary.
    key = f"{FORM_PREFIX}{exercise_id or 'new'}_"
    st.session_state.setdefault(f"{key}name", saved["exercise_name"])
    st.session_state.setdefault(f"{key}type", saved["exercise_type"])
    st.session_state.setdefault(f"{key}equipment", saved["equipment"])
    st.session_state.setdefault(f"{key}primary", list(saved["primary_ids"]))
    st.session_state.setdefault(f"{key}secondary", list(saved["secondary_ids"]))
    st.session_state.setdefault(f"{key}instructions", saved["instructions"])

    name = st.text_input(
        "Name", max_chars=exercises.EXERCISE_NAME_MAX, placeholder="e.g. Bench press", key=f"{key}name"
    )
    with st.container(horizontal=True, vertical_alignment="bottom"):
        exercise_type = st.segmented_control(
            "Type", list(types), format_func=types.get, required=True, key=f"{key}type"
        )
        equipment_code = st.selectbox("Equipment", list(equipment), format_func=equipment.get, key=f"{key}equipment")

    primary_ids, secondary_ids = [], []
    if exercise_type == exercises.STRENGTH:
        primary_ids = st.multiselect(
            "Primary muscle groups",
            list(group_names),
            format_func=group_names.get,
            placeholder="The muscles it mainly works",
            key=f"{key}primary",
        )
        # A muscle is primary or secondary, never both. A widget's value can
        # only be changed before it is drawn, so this happens here.
        secondary_options = [group_id for group_id in group_names if group_id not in primary_ids]
        st.session_state[f"{key}secondary"] = [
            group_id for group_id in st.session_state[f"{key}secondary"] if group_id in secondary_options
        ]
        secondary_ids = st.multiselect(
            "Secondary muscle groups",
            secondary_options,
            format_func=group_names.get,
            placeholder="Muscles that help",
            key=f"{key}secondary",
        )
    else:
        st.caption("Cardio exercises have no muscle groups.")

    instructions = st.text_area(
        "Instructions", height=120, placeholder="How to do it, form cues...", key=f"{key}instructions"
    )

    # The picture. A new file replaces the old picture when you press Save.
    current = exercises.get_exercise_image(user_id, exercise_id) if exercise_id is not None else None
    upload = st.file_uploader(
        "Picture" if current is None else "Replace picture",
        type=exercises.IMAGE_FILE_TYPES,
        max_upload_size=5,
        help="JPEG, PNG, WebP or GIF, up to 5 MB.",
        key=f"exercise_picture_{exercise_id or 'new'}",
    )
    new_image = upload.getvalue() if upload is not None else None
    remove_picture = False
    if new_image is not None:
        try:
            exercises.check_image(new_image)
        except ValueError as e:
            st.error(str(e))
        else:
            st.image(new_image, caption="New picture (saved when you press Save)", width=300, alt=f"New picture for {name}")
    elif current is not None:
        st.image(current["image_data"], caption=current["file_name"], width=300, alt=f"Picture for {name}")
        remove_picture = st.checkbox("Remove picture", key=f"{key}remove_picture")

    with st.container(horizontal=True):
        save = st.button("Save", type="primary", icon=":material/save:", key=f"{key}save")
        cancel = st.button("Cancel", key=f"{key}cancel")

    if cancel:
        close_exercise_dialog()
        st.rerun()
    if save:
        values = {
            "exercise_name": name,
            "exercise_type": exercise_type,
            "equipment": equipment_code,
            "instructions": instructions,
            "primary_ids": primary_ids,
            "secondary_ids": secondary_ids,
        }
        try:
            exercises.save_exercise(
                user_id,
                exercise_id,
                values,
                image_data=new_image,
                image_file_name=upload.name if upload is not None else None,
                remove_image=remove_picture,
            )
        except ValueError as e:
            st.error(str(e))
        else:
            close_exercise_dialog()
            flash(f"{'Added' if exercise_id is None else 'Saved'} {name.strip()}.")
            st.rerun()

    if exercise_id is not None:
        st.divider()
        with st.container(horizontal=True, vertical_alignment="center"):
            confirm = st.checkbox("Yes, remove this exercise", key=f"{key}confirm_remove")
            if st.button("Remove exercise", icon=":material/delete:", disabled=not confirm, key=f"{key}remove"):
                try:
                    exercises.remove_exercise(user_id, exercise_id)
                except ValueError as e:
                    st.error(str(e))
                else:
                    close_exercise_dialog()
                    flash(f"Removed {saved['exercise_name']}.")
                    st.rerun()
        st.caption("A removed exercise is hidden from the library, and its name can be used again.")


# st.dialog is a decorator. Applying it twice to the same function gives two
# pop-ups with different titles that share one form. on_dismiss runs
# close_exercise_dialog (then reruns the app) when the pop-up is closed with
# its X, Esc or a click outside it.
add_exercise_dialog = st.dialog("Add exercise", width="medium", on_dismiss=close_exercise_dialog)(exercise_form)
edit_exercise_dialog = st.dialog("Edit exercise", width="medium", on_dismiss=close_exercise_dialog)(exercise_form)


# ---- Manage muscle groups pop-up -----------------------------------------


@st.dialog("Manage muscle groups", width="medium", on_dismiss=close_group_dialog)
def group_dialog() -> None:
    """
    Show the Manage muscle groups pop-up.

    It lists your own groups, the built-in ones (read only) in a closed
    expander, a box to add a group, and a box to rename or remove one of
    yours. The Add, Rename and Remove buttons do their work in callbacks,
    which run before the pop-up is drawn again, so the lists always show
    the latest groups and the boxes can be cleared after a success. Done
    (or the X) closes it and reruns the whole page.
    """
    groups = exercises.get_muscle_groups(user_id)
    own = groups[groups["is_own"]]
    own_names = dict(zip(own["muscle_group_id"].tolist(), own["muscle_group_name"]))

    st.markdown("**Your muscle groups**")
    if own_names:
        st.markdown("\n".join(f"- {name}" for name in own_names.values()))
    else:
        st.caption("You haven't made any muscle groups yet. Add one below.")
    with st.expander("Built-in muscle groups", icon=":material/lock:"):
        st.markdown(", ".join(groups.loc[~groups["is_own"], "muscle_group_name"]))
        st.caption("Built-in muscle groups are shared by everyone and can't be renamed or removed.")

    st.divider()

    def add_clicked() -> None:
        """
        Create the group typed in the Add box, then clear the box.
        """
        name = st.session_state.get("group_new_name", "")
        try:
            _, brought_back = exercises.add_muscle_group(user_id, name)
        except ValueError as e:
            set_dialog_message(GROUP_MESSAGE, "add", "error", str(e))
            return
        # Adding a name you removed earlier brings the old group back
        verb = "Brought back" if brought_back else "Added"
        set_dialog_message(GROUP_MESSAGE, "add", "success", f'{verb} "{name.strip()}".')
        st.session_state.pop("group_new_name", None)

    with st.container(horizontal=True, vertical_alignment="bottom"):
        st.text_input(
            "Add a muscle group",
            max_chars=exercises.MUSCLE_GROUP_NAME_MAX,
            placeholder="e.g. Neck",
            key="group_new_name",
        )
        st.button("Add", icon=":material/add:", on_click=add_clicked, key="group_add")
    show_dialog_message(GROUP_MESSAGE, "add")

    st.divider()
    st.markdown("**Rename or remove**")
    if not own_names:
        st.caption("Only your own muscle groups can be changed. Add one above first.")
    else:
        # A group removed since the last run is no longer on offer
        if st.session_state.get("group_choice") not in own_names:
            st.session_state.pop("group_choice", None)
        choice = st.selectbox(
            "Your muscle group",
            list(own_names),
            index=None,
            format_func=own_names.get,
            placeholder="Choose one of your muscle groups",
            key="group_choice",
        )

        def rename_clicked(group_id: int) -> None:
            """
            Save the name typed in the New name box.

            Parameters
            ----------
            group_id : int
                The group being renamed.
            """
            new_name = st.session_state.get(f"group_rename_{group_id}", "")
            try:
                exercises.rename_muscle_group(user_id, group_id, new_name)
            except ValueError as e:
                set_dialog_message(GROUP_MESSAGE, "rename", "error", str(e))
            else:
                set_dialog_message(GROUP_MESSAGE, "rename", "success", f'Renamed to "{new_name.strip()}".')

        def remove_clicked(group_id: int) -> None:
            """
            Remove the chosen group, or store why it couldn't be removed.

            Parameters
            ----------
            group_id : int
                The group being removed.
            """
            name = own_names[group_id]
            try:
                exercises.remove_muscle_group(user_id, group_id)
            except ValueError as e:
                set_dialog_message(GROUP_MESSAGE, "remove", "error", str(e))
            else:
                set_dialog_message(GROUP_MESSAGE, "remove", "success", f'Removed "{name}".')
                st.session_state.pop("group_choice", None)
                st.session_state.pop(f"group_confirm_remove_{group_id}", None)

        if choice is not None:
            # A key per group, so the box starts with that group's name
            with st.container(horizontal=True, vertical_alignment="bottom"):
                st.text_input(
                    "New name",
                    value=own_names[choice],
                    max_chars=exercises.MUSCLE_GROUP_NAME_MAX,
                    key=f"group_rename_{choice}",
                )
                st.button("Rename", icon=":material/edit:", on_click=rename_clicked, args=(choice,), key="group_rename")
            show_dialog_message(GROUP_MESSAGE, "rename")
            with st.container(horizontal=True, vertical_alignment="center"):
                confirm = st.checkbox("Yes, remove this muscle group", key=f"group_confirm_remove_{choice}")
                st.button(
                    "Remove muscle group",
                    icon=":material/delete:",
                    disabled=not confirm,
                    on_click=remove_clicked,
                    args=(choice,),
                    key="group_remove",
                )
            st.caption("A muscle group can only be removed once no active exercises use it.")
    show_dialog_message(GROUP_MESSAGE, "remove")

    st.divider()
    if st.button("Done", type="primary", key="group_done"):
        close_group_dialog()
        st.rerun()


# ---- Library tab ---------------------------------------------------------


def has_any(group_ids: list[int], chosen: list[int]) -> bool:
    """
    Check whether an exercise is tagged with at least one of the chosen groups.

    Parameters
    ----------
    group_ids : list[int]
        The exercise's primary (or secondary) muscle group ids.
    chosen : list[int]
        The groups picked in the filter.

    Returns
    -------
    bool
        True if the two lists share a group.
    """
    return bool(set(group_ids) & set(chosen))


def exercise_details(exercise_id: int, row: pd.Series) -> None:
    """
    Show one exercise's details in a bordered panel below the table.

    The text (type, equipment, muscle groups and instructions) is on the
    left and the picture on the right. The two columns stack on a narrow
    screen. The Edit button opens the Edit exercise pop-up.

    Parameters
    ----------
    exercise_id : int
        The exercise to show.
    row : pd.Series
        Its row from ``exercises.get_exercises``.
    """
    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.subheader(row["exercise_name"])
            st.button(
                "Edit",
                icon=":material/edit:",
                on_click=open_exercise_dialog,
                args=(exercise_id,),
                key="exercise_detail_edit",
            )
        text_column, picture_column = st.columns([3, 2])
        with text_column:
            st.markdown(f":blue-badge[{row['type_name']}] :gray-badge[{row['equipment_name']}]")
            if row["exercise_type"] == exercises.STRENGTH:
                st.markdown(f"**Primary:** {', '.join(row['primary_names']) or 'None'}")
                st.markdown(f"**Secondary:** {', '.join(row['secondary_names']) or 'None'}")
            if row["instructions"]:
                st.markdown(row["instructions"])
            else:
                st.caption("No instructions yet.")
        with picture_column:
            # Only ask the database for a picture when there is one
            image = exercises.get_exercise_image(user_id, exercise_id) if row["has_image"] else None
            if image is None:
                st.caption("No picture.")
            else:
                st.image(image["image_data"], alt=f"Picture for {row['exercise_name']}")


if library_tab.open:
    with library_tab:
        library = exercises.get_exercises(user_id)
        types = exercises.get_exercise_types()
        equipment = exercises.get_equipment()
        groups = exercises.get_muscle_groups(user_id)
        group_names = dict(zip(groups["muscle_group_id"].tolist(), groups["muscle_group_name"]))

        with st.container(horizontal=True):
            st.button(
                "Add exercise",
                type="primary",
                icon=":material/add:",
                on_click=open_exercise_dialog,
                args=(None,),
            )
            st.button("Manage muscle groups", icon=":material/category:", on_click=open_group_dialog)

        # A group removed since the last run is no longer on offer, so it is
        # dropped from the filters (before the boxes are drawn)
        for filter_key in ["exercise_filter_primary", "exercise_filter_secondary"]:
            if filter_key in st.session_state:
                st.session_state[filter_key] = [g for g in st.session_state[filter_key] if g in group_names]

        with st.container(horizontal=True, vertical_alignment="bottom"):
            search = st.text_input("Search", placeholder="e.g. press", key="exercise_filter_search")
            chosen_types = st.segmented_control(
                "Type", list(types), selection_mode="multi", format_func=types.get, key="exercise_filter_type"
            )
            chosen_equipment = st.multiselect(
                "Equipment", list(equipment), format_func=equipment.get, placeholder="Any", key="exercise_filter_equipment"
            )
        with st.container(horizontal=True):
            chosen_primary = st.multiselect(
                "Primary muscle groups",
                list(group_names),
                format_func=group_names.get,
                placeholder="Any",
                key="exercise_filter_primary",
            )
            chosen_secondary = st.multiselect(
                "Secondary muscle groups",
                list(group_names),
                format_func=group_names.get,
                placeholder="Any",
                key="exercise_filter_secondary",
            )

        # Each filter left empty lets everything through. Filters combine
        # with AND; within a muscle filter, any one of the picked groups matches.
        view = library
        if search.strip():
            view = view[view["exercise_name"].str.contains(search.strip(), case=False, regex=False)]
        if chosen_types:
            view = view[view["exercise_type"].isin(chosen_types)]
        if chosen_equipment:
            view = view[view["equipment"].isin(chosen_equipment)]
        if chosen_primary:
            view = view[view["primary_ids"].map(lambda ids: has_any(ids, chosen_primary))]
        if chosen_secondary:
            view = view[view["secondary_ids"].map(lambda ids: has_any(ids, chosen_secondary))]

        # Only the shown columns are sent to the browser
        table = pd.DataFrame(
            {
                "exercise_name": view["exercise_name"],
                "type_name": view["type_name"],
                "equipment_name": view["equipment_name"],
                "primary": view["primary_names"].map(", ".join),
                "secondary": view["secondary_names"].map(", ".join),
                "has_image": view["has_image"],
            },
            index=view.index,
        )

        def remember_selection() -> None:
            """
            Remember which exercise was selected in the table, by its id.

            This is the table's ``on_select`` callback. It runs at the start
            of the next run, so ``table`` is still the table that was
            clicked. The selection only holds a row position (0, 1, 2...),
            which changes when the filters or the sort order change, so it is
            turned into an exercise id straight away.
            """
            rows = st.session_state[TABLE_KEY].selection.rows
            st.session_state[SELECTED_EXERCISE] = int(table.index[rows[0]]) if rows else None

        # Forget an exercise that is no longer shown (filtered out or
        # removed). Otherwise point the table's selection at the row where
        # that exercise is now, so the highlight never lands on another row.
        # A selection can be set this way, before the table is drawn.
        selected_id = st.session_state.get(SELECTED_EXERCISE)
        if selected_id not in table.index:
            selected_id = None
            st.session_state[SELECTED_EXERCISE] = None
        selected_rows = [] if selected_id is None else [table.index.get_loc(selected_id)]
        st.session_state[TABLE_KEY] = {"selection": {"rows": selected_rows}}

        st.caption(f"Showing {len(table)} of {len(library)} exercises.")
        if table.empty:
            st.info("No exercises match these filters.")
        else:
            st.dataframe(
                table,
                hide_index=True,
                alt="Your exercises",
                key=TABLE_KEY,
                on_select=remember_selection,
                selection_mode="single-row",
                column_config={
                    "exercise_name": st.column_config.TextColumn("Exercise", width="medium"),
                    "type_name": st.column_config.TextColumn("Type", width="small"),
                    "equipment_name": st.column_config.TextColumn("Equipment", width="small"),
                    "primary": st.column_config.TextColumn("Primary", width="medium"),
                    "secondary": st.column_config.TextColumn("Secondary", width="medium"),
                    "has_image": st.column_config.CheckboxColumn("Picture", width="small"),
                },
            )

        if selected_id is None:
            st.caption("Select an exercise to see its instructions and picture.")
        else:
            exercise_details(selected_id, library.loc[selected_id])


# ---- Draw the open pop-up ------------------------------------------------
# Only one pop-up can be open per run. An exercise removed since the pop-up
# opened (e.g. in another browser tab) just closes it.
if EDITING_EXERCISE in st.session_state:
    editing_id = st.session_state[EDITING_EXERCISE]
    if editing_id is None:
        add_exercise_dialog(None)
    elif editing_id in exercises.get_exercises(user_id).index:
        edit_exercise_dialog(editing_id)
    else:
        close_exercise_dialog()
elif MANAGING_GROUPS in st.session_state:
    group_dialog()
