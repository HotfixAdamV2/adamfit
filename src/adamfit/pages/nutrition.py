"""Nutrition page: a daily food log, recipes, and the user's food list."""

from datetime import date, timedelta

import streamlit as st

from adamfit import auth, food_logs, foods, recipes
from adamfit.nutrition import MACROS, scale_entries, totals_row
from adamfit.ui import (
    apply_changes,
    count_changes,
    entries_editor,
    flash,
    item_picker,
    pending_changes,
    save_bar,
    show_flash,
    stage_add,
    stage_delete,
    stage_update,
)

user = auth.current_user()
user_id = user["user_id"]

st.title("Nutrition")
show_flash()

# on_change="rerun" makes the tabs remember which one is open, and lets us
# run only the open tab's code
log_tab, recipe_tab, food_tab = st.tabs(
    ["Daily log", "Recipes", "Foods"], key="nutrition_tab", on_change="rerun"
)

food_list = foods.get_foods(user_id)


def food_options() -> dict[str, dict]:
    """
    Build picker options for every active food.

    Returns
    -------
    dict[str, dict]
        Keyed ``"food:<id>"``, with ``label``, ``category`` and
        ``sub_category`` for ``ui.item_picker``, plus ``item_name``,
        ``serving_size``, ``serving_unit`` and the per-serving macros for
        ``ui.apply_changes``.
    """
    return {
        f"food:{food_id}": {
            "label": f"{row.food_name} · {row.serving_size:g} {row.serving_unit}",
            "category": row.parent_name,
            "sub_category": row.sub_category_name,
            "item_name": row.food_name,
            "serving_size": row.serving_size,
            "serving_unit": row.serving_unit,
            **{column: row[column] for column in MACROS},
        }
        for food_id, row in food_list.iterrows()
    }


def saved_message(count: int, where: str) -> str:
    """
    Describe how many changes were just saved.

    Parameters
    ----------
    count : int
        Number of changes saved.
    where : str
        What was changed, e.g. ``"the log"``.

    Returns
    -------
    str
        For example ``"Saved 3 changes to the log."``.
    """
    return f"Saved {count} change{'s' if count != 1 else ''} to {where}."


# ---- Daily log ---------------------------------------------------------
if log_tab.open:
    with log_tab:

        def shift_day(days: int) -> None:
            """
            Move the selected log date forwards or backwards.

            Parameters
            ----------
            days : int
                Number of days to move (negative for earlier).
            """
            st.session_state["log_date"] += timedelta(days=days)

        st.session_state.setdefault("log_date", date.today())
        with st.container(horizontal=True, vertical_alignment="bottom"):
            st.button("", icon=":material/chevron_left:", help="Previous day", on_click=shift_day, args=(-1,))
            log_date = st.date_input("Date", key="log_date", width=180)
            st.button("", icon=":material/chevron_right:", help="Next day", on_click=shift_day, args=(1,))

        # Changes are staged per day, so moving to another day keeps them
        # (unsaved) and shows that day's own changes instead
        changes_key = f"log_changes_{log_date.isoformat()}"
        changes = pending_changes(changes_key)
        other_days = [
            date.fromisoformat(name.removeprefix("log_changes_"))
            for name, other in st.session_state.items()
            if name.startswith("log_changes_") and name != changes_key and count_changes(other)
        ]
        if other_days:
            days = ", ".join(f"{day:%a %b %d}" for day in sorted(other_days))
            st.warning(f"You also have unsaved changes on {days}.", icon=":material/warning:")

        recipe_list = recipes.get_recipes(user_id)
        options = {
            f"recipe:{recipe_id}": {
                "label": f"Recipe: {row.recipe_name} · 1 {row.serving_label}",
                # Recipes have no category in the database, so they get
                # their own entry in the Category filter
                "category": "Recipes",
                "sub_category": None,
                "item_name": row.recipe_name,
                "serving_size": 1.0,
                "serving_unit": row.serving_label,
                **{column: row[column] for column in MACROS},
            }
            for recipe_id, row in recipe_list.iterrows()
        }
        options.update(food_options())
        item_picker(
            options,
            key="log_add",
            on_add=lambda option_key, servings: stage_add(changes, option_key, servings),
        )

        log = apply_changes(food_logs.get_log(user_id, log_date), changes, options)
        if log.empty:
            st.info(f"Nothing logged for {log_date:%A, %b %d}. Pick a food or recipe above to start.")
        else:
            entries_editor(
                log,
                key="log_table",
                on_update=lambda entry_id, servings: stage_update(changes, entry_id, servings),
                on_delete=lambda entry_id: stage_delete(changes, entry_id),
                alt=f"Food log for {log_date:%b %d, %Y}",
                totals_as_tiles=True,
            )
            st.caption(
                "Change the servings to update the macros. Select rows and press Delete to remove them. "
                "Nothing is saved until you press Save changes."
            )

        if save_bar(changes_key):
            adds = []
            for add in changes["adds"].values():
                kind, item_id = add["option_key"].split(":")
                adds.append(
                    {
                        "food_id": int(item_id) if kind == "food" else None,
                        "recipe_id": int(item_id) if kind == "recipe" else None,
                        "servings": add["servings"],
                    }
                )
            try:
                food_logs.save_log_changes(user_id, log_date, adds, changes["updates"], changes["deletes"])
            except ValueError as e:
                st.error(str(e))
            else:
                flash(saved_message(count_changes(changes), "the log"))
                del st.session_state[changes_key]
                st.rerun()

# ---- Recipes -----------------------------------------------------------
if recipe_tab.open:
    with recipe_tab:
        recipe_list = recipes.get_recipes(user_id)

        # A widget's value can only be changed before it is drawn, so a recipe
        # created or deleted on the previous run is selected (or cleared) here
        if "pending_recipe_choice" in st.session_state:
            st.session_state["recipe_choice"] = st.session_state.pop("pending_recipe_choice")

        with st.container(horizontal=True, vertical_alignment="bottom"):
            recipe_id = st.selectbox(
                "Recipe",
                options=recipe_list.index.tolist(),
                format_func=lambda rid: recipe_list.loc[rid, "recipe_name"],
                index=None,
                placeholder="Choose a recipe" if not recipe_list.empty else "No recipes yet",
                key="recipe_choice",
            )
            with st.popover("New recipe", icon=":material/add:"):
                with st.form("new_recipe_form", border=False):
                    new_name = st.text_input("Name", max_chars=100, placeholder="Chicken and rice")
                    new_servings = st.number_input("Makes how many servings?", min_value=0.25, value=1.0, step=1.0)
                    new_label = st.text_input("What is one serving called?", value="serving", max_chars=30)
                    if st.form_submit_button("Create", type="primary"):
                        if not new_name.strip() or not new_label.strip():
                            st.error("Enter a name and a serving label.")
                        else:
                            try:
                                st.session_state["pending_recipe_choice"] = recipes.create_recipe(
                                    user_id, new_name, new_servings, new_label
                                )
                            except ValueError as e:
                                st.error(str(e))
                            else:
                                flash(f"Created {new_name.strip()}. Add its ingredients below.")
                                st.rerun()

        recipe = recipes.get_recipe(user_id, recipe_id) if recipe_id is not None else None
        if recipe is None:
            st.info("Choose a recipe, or create a new one, to see its ingredients and macros.")
        else:
            label = recipe["serving_label"]
            servings_per_recipe = float(recipe["servings_per_recipe"])
            options = food_options()

            # Ingredient changes are staged per recipe until Save changes
            changes_key = f"recipe_changes_{recipe_id}"
            changes = pending_changes(changes_key)
            ingredients = apply_changes(recipes.get_ingredients(user_id, recipe_id), changes, options)

            st.subheader(recipe["recipe_name"])
            st.caption(f"Makes {servings_per_recipe:g} × {label}. Macros below are per {label}.")
            # Worked out from the ingredients on screen (rather than read from
            # vw_recipe_nutrition) so unsaved changes show up here too
            totals = totals_row(scale_entries(ingredients)).iloc[0]
            with st.container(horizontal=True):
                for column, macro_label in MACROS.items():
                    total = float(totals[column])
                    per_serving = total / servings_per_recipe
                    st.metric(
                        macro_label,
                        f"{per_serving:,.0f}" if column == "calories" else f"{per_serving:.1f}",
                        help=f"Whole recipe: {total:,.1f}",
                        border=True,
                    )

            st.markdown("**Ingredients**")
            item_picker(
                options,
                key=f"recipe_add_{recipe_id}",
                on_add=lambda option_key, servings: stage_add(changes, option_key, servings),
                label="Food",
            )
            if ingredients.empty:
                st.info("No ingredients yet. Add foods above and the macros are calculated for you.")
            else:
                entries_editor(
                    ingredients,
                    key=f"recipe_table_{recipe_id}",
                    on_update=lambda ingredient_id, servings: stage_update(changes, ingredient_id, servings),
                    on_delete=lambda ingredient_id: stage_delete(changes, ingredient_id),
                    alt=f"Ingredients in {recipe['recipe_name']}",
                )
                st.caption(
                    "Change the servings to update the macros. Totals are for the whole recipe. "
                    "Nothing is saved until you press Save changes."
                )

            if save_bar(changes_key):
                adds = [
                    {"food_id": int(add["option_key"].split(":")[1]), "servings": add["servings"]}
                    for add in changes["adds"].values()
                ]
                try:
                    recipes.save_ingredient_changes(
                        user_id, recipe_id, adds, changes["updates"], changes["deletes"]
                    )
                except ValueError as e:
                    st.error(str(e))
                else:
                    flash(saved_message(count_changes(changes), "the recipe"))
                    del st.session_state[changes_key]
                    st.rerun()

            st.markdown("**Instructions**")
            if recipe["instructions"]:
                st.markdown(recipe["instructions"])
            else:
                st.caption("No instructions yet. Add them under Edit recipe details.")

            with st.expander("Edit recipe details", icon=":material/edit:"):
                with st.form(f"recipe_form_{recipe_id}", border=False):
                    name = st.text_input("Name", value=recipe["recipe_name"], max_chars=100)
                    col_servings, col_label = st.columns(2)
                    new_servings_per_recipe = col_servings.number_input(
                        "Makes how many servings?",
                        min_value=0.25,
                        value=servings_per_recipe,
                        step=1.0,
                    )
                    serving_label = col_label.text_input(
                        "What is one serving called?", value=label, max_chars=30
                    )
                    instructions = st.text_area(
                        "Instructions",
                        value=recipe["instructions"] or "",
                        height=200,
                        help="Markdown works here, e.g. numbered lists like `1. Preheat the oven`.",
                    )
                    if st.form_submit_button("Save details", type="primary"):
                        if not name.strip() or not serving_label.strip():
                            st.error("Enter a name and a serving label.")
                        else:
                            try:
                                recipes.update_recipe(
                                    user_id, recipe_id, name, new_servings_per_recipe, serving_label, instructions
                                )
                            except ValueError as e:
                                st.error(str(e))
                            else:
                                flash("Recipe saved.")
                                st.rerun()

                with st.popover("Delete recipe", icon=":material/delete:"):
                    st.write("Remove this recipe? Days you already logged it keep their numbers.")
                    if st.button("Yes, delete it", type="primary"):
                        recipes.delete_recipe(user_id, recipe_id)
                        st.session_state.pop(changes_key, None)
                        st.session_state["pending_recipe_choice"] = None
                        flash(f"Deleted {recipe['recipe_name']}.")
                        st.rerun()

# ---- Foods -------------------------------------------------------------
# A pop-up (st.dialog) closes as soon as a run doesn't draw it, and a button
# click is only True on the run right after it. So the page remembers in
# session state which pop-up is open, and draws it on every run until one of
# its buttons, or its X, closes it. Only one pop-up can be open at a time:
# - "editing_food" holds the id of the food being edited (None for a new one)
# - "managing_categories" is set while Manage categories is open
EDITING_FOOD = "editing_food"
MANAGING_CATEGORIES = "managing_categories"
# A message shown inside the Manage categories pop-up (see set_category_message)
CATEGORY_MESSAGE = "category_message"
# Extra choices offered next to the real category ids in the category boxes
NEW_CATEGORY = "new_category"
NEW_PARENT = "new_parent"


def open_food_dialog(food_id: int | None) -> None:
    """
    Open the food pop-up on the next run.

    Parameters
    ----------
    food_id : int | None
        The food to edit, or None to add a new one.
    """
    st.session_state.pop(MANAGING_CATEGORIES, None)
    st.session_state[EDITING_FOOD] = food_id


def close_food_dialog() -> None:
    """
    Forget which food the pop-up was open for, so the next run doesn't reopen it.
    """
    st.session_state.pop(EDITING_FOOD, None)


def open_category_dialog() -> None:
    """
    Open the Manage categories pop-up on the next run.
    """
    st.session_state.pop(EDITING_FOOD, None)
    st.session_state[MANAGING_CATEGORIES] = True


def close_category_dialog() -> None:
    """
    Close the Manage categories pop-up and forget its last message.
    """
    st.session_state.pop(MANAGING_CATEGORIES, None)
    st.session_state.pop(CATEGORY_MESSAGE, None)


def set_category_message(section: str, kind: str, text: str) -> None:
    """
    Store a message for one section of the Manage categories pop-up.

    The buttons there run callbacks, which happen before the pop-up is
    drawn, so the message is kept here and shown by ``show_category_message``.

    Parameters
    ----------
    section : str
        Where to show it: ``"add"``, ``"rename"`` or ``"remove"``.
    kind : str
        ``"success"`` or ``"error"``.
    text : str
        The message.
    """
    st.session_state[CATEGORY_MESSAGE] = {"section": section, "kind": kind, "text": text}


def show_category_message(section: str) -> None:
    """
    Show (once) the stored message if it belongs to this section.

    Parameters
    ----------
    section : str
        The section being drawn, e.g. ``"add"``.
    """
    message = st.session_state.get(CATEGORY_MESSAGE)
    if message is None or message["section"] != section:
        return
    del st.session_state[CATEGORY_MESSAGE]
    if message["kind"] == "error":
        st.error(message["text"])
    else:
        st.success(message["text"])


def new_category_fields(key: str) -> None:
    """
    Draw the boxes for a new sub-category: where it goes, and its name.

    "Put it under" offers every top-level category (built-in and your own)
    plus "+ New top-level category", which adds a box for that name. Read
    what was entered with ``new_category_values``.

    Parameters
    ----------
    key : str
        Prefix for the widget keys, e.g. ``"food_new_category"``.
    """
    parents = foods.get_parent_categories(user_id)
    names = {int(row.category_id): row.category_name for row in parents.itertuples()}
    own_ids = {int(row.category_id) for row in parents.itertuples() if row.is_own}

    def parent_label(choice: int | str) -> str:
        """
        Name a choice in the "Put it under" box.

        Parameters
        ----------
        choice : int | str
            A top-level category id, or ``NEW_PARENT``.

        Returns
        -------
        str
            The category's name (with "(yours)" for your own), or
            "+ New top-level category".
        """
        if choice == NEW_PARENT:
            return "+ New top-level category"
        return f"{names[choice]} (yours)" if choice in own_ids else names[choice]

    options = [*names, NEW_PARENT]
    # A widget's value can only be changed before it is drawn, so a choice
    # that no longer exists (e.g. just removed) is cleared here
    if st.session_state.get(f"{key}_parent") not in options:
        st.session_state.pop(f"{key}_parent", None)
    parent = st.selectbox(
        "Put it under",
        options,
        index=None,
        format_func=parent_label,
        placeholder="Choose a top-level category",
        key=f"{key}_parent",
    )
    if parent == NEW_PARENT:
        st.text_input(
            "New top-level category",
            max_chars=foods.CATEGORY_NAME_MAX,
            placeholder="e.g. Baking",
            key=f"{key}_parent_name",
        )
    st.text_input(
        "Sub-category name",
        max_chars=foods.CATEGORY_NAME_MAX,
        placeholder="e.g. Chocolate",
        key=f"{key}_name",
    )


def new_category_values(key: str) -> tuple[str, int | None, str | None]:
    """
    Read what was entered in the boxes drawn by ``new_category_fields``.

    Parameters
    ----------
    key : str
        The same prefix passed to ``new_category_fields``.

    Returns
    -------
    tuple[str, int | None, str | None]
        The sub-category name, the chosen parent's id (None for a new
        top-level category) and the new top-level category's name (None
        when an existing parent was chosen), ready for
        ``foods.add_category``.

    Raises
    ------
    ValueError
        If no parent was chosen.
    """
    parent = st.session_state.get(f"{key}_parent")
    if parent is None:
        raise ValueError("Choose where the new category goes.")
    name = st.session_state.get(f"{key}_name", "")
    if parent == NEW_PARENT:
        return name, None, st.session_state.get(f"{key}_parent_name", "")
    return name, parent, None


@st.dialog("Manage categories", width="medium", on_dismiss=close_category_dialog)
def category_dialog() -> None:
    """
    Show the Manage categories pop-up.

    It lists your own categories grouped by their top-level category
    (built-in top-levels are marked with a lock), the built-in categories
    in a closed expander, a form to add a category, and a box to rename or
    remove one of yours. The Add, Rename and Remove buttons do their work
    in callbacks, which run before the pop-up is drawn again, so the lists
    always show the latest categories and the boxes can be cleared after a
    success. Done (or the X) closes it and reruns the whole page.
    """
    # Read here, not once for the page: a pop-up reruns on its own when you
    # use it, so data read outside it would not show a change made inside
    subs = foods.get_categories(user_id)
    parents = foods.get_parent_categories(user_id)
    own_subs = subs[subs["is_own"]]

    # One group per top-level category that is yours or holds one of yours.
    # own_labels collects everything you can rename or remove, in the same order.
    groups = parents[parents["is_own"] | parents["category_id"].isin(own_subs["parent_category_id"])]
    own_labels = {}
    group_texts = []
    for parent in groups.itertuples():
        lines = [f"**{parent.category_name}**" + ("" if parent.is_own else " :gray[:material/lock: Built-in]")]
        if parent.is_own:
            own_labels[int(parent.category_id)] = f"{parent.category_name} (top level)"
        children = own_subs[own_subs["parent_category_id"] == parent.category_id]
        if children.empty:
            lines.append("- *No sub-categories yet*")
        for child in children.itertuples():
            lines.append(f"- {child.category_name}")
            own_labels[int(child.category_id)] = child.label
        group_texts.append("\n".join(lines))

    st.markdown("**Your categories**")
    if group_texts:
        # A blank line between groups, or Markdown would add the next heading
        # to the last bullet
        st.markdown("\n\n".join(group_texts))
    else:
        st.caption("You haven't made any categories yet. Add one below.")
    with st.expander("Built-in categories", icon=":material/lock:"):
        built_in = subs[~subs["is_own"]]
        for parent_name, group in built_in.groupby("parent_name", sort=False):
            st.markdown(f"**{parent_name}**: {', '.join(group['category_name'])}")
        st.caption("Built-in categories are shared by everyone and can't be renamed or removed.")

    st.divider()
    st.markdown("**Add a category**")
    st.caption("Foods go in sub-categories, so a new top-level category is created with its first sub-category.")
    new_category_fields("manage_new")

    def add_clicked() -> None:
        """
        Create the category from the Add boxes, then clear its name boxes.
        """
        try:
            name, parent_id, new_parent_name = new_category_values("manage_new")
            _, brought_back = foods.add_category(user_id, name, parent_id, new_parent_name)
        except ValueError as e:
            set_category_message("add", "error", str(e))
            return
        # Adding a name you removed earlier brings the old category back
        verb = "Brought back" if brought_back else "Added"
        set_category_message("add", "success", f'{verb} "{name.strip()}".')
        # Keep an existing parent chosen, to make adding several in a row easy
        to_clear = ["manage_new_name", "manage_new_parent_name"]
        if new_parent_name is not None:
            to_clear.append("manage_new_parent")
        for widget_key in to_clear:
            st.session_state.pop(widget_key, None)

    st.button("Add category", icon=":material/add:", on_click=add_clicked, key="manage_add")
    show_category_message("add")

    st.divider()
    st.markdown("**Rename or remove**")
    if not own_labels:
        st.caption("Only your own categories can be changed. Add one above first.")
    else:
        if st.session_state.get("manage_choice") not in own_labels:
            st.session_state.pop("manage_choice", None)
        choice = st.selectbox(
            "Your category",
            list(own_labels),
            index=None,
            format_func=own_labels.get,
            placeholder="Choose one of your categories",
            key="manage_choice",
        )

        def rename_clicked(category_id: int) -> None:
            """
            Save the name typed in the New name box.

            Parameters
            ----------
            category_id : int
                The category being renamed.
            """
            new_name = st.session_state.get(f"manage_rename_{category_id}", "")
            try:
                foods.rename_category(user_id, category_id, new_name)
            except ValueError as e:
                set_category_message("rename", "error", str(e))
            else:
                set_category_message("rename", "success", f'Renamed to "{new_name.strip()}".')

        def remove_clicked(category_id: int) -> None:
            """
            Remove the chosen category, or store why the database refused.

            Parameters
            ----------
            category_id : int
                The category being removed.
            """
            label = own_labels[category_id]
            try:
                foods.remove_category(user_id, category_id)
            except ValueError as e:
                set_category_message("remove", "error", str(e))
            else:
                set_category_message("remove", "success", f'Removed "{label}".')
                st.session_state.pop("manage_choice", None)
                st.session_state.pop(f"manage_confirm_remove_{category_id}", None)

        if choice is not None:
            current_name = own_labels[choice].split(" › ")[-1].removesuffix(" (top level)")
            with st.container(horizontal=True, vertical_alignment="bottom"):
                st.text_input(
                    "New name", value=current_name, max_chars=foods.CATEGORY_NAME_MAX, key=f"manage_rename_{choice}"
                )
                st.button(
                    "Rename", icon=":material/edit:", on_click=rename_clicked, args=(choice,), key="manage_rename"
                )
            show_category_message("rename")
            # A key per category, so the tick doesn't carry over to another one
            with st.container(horizontal=True, vertical_alignment="center"):
                confirm = st.checkbox("Yes, remove this category", key=f"manage_confirm_remove_{choice}")
                st.button(
                    "Remove category",
                    icon=":material/delete:",
                    disabled=not confirm,
                    on_click=remove_clicked,
                    args=(choice,),
                    key="manage_remove",
                )
            st.caption("A category can only be removed once no active foods or sub-categories use it.")
    show_category_message("remove")

    st.divider()
    if st.button("Done", type="primary", key="manage_done"):
        close_category_dialog()
        st.rerun()


if food_tab.open:
    with food_tab:
        categories = foods.get_categories(user_id)
        category_labels = {int(row.category_id): row.label for row in categories.itertuples()}
        unit_names = foods.get_serving_units()["unit_name"].to_dict()

        def unit_label(code: str) -> str:
            """
            Describe a serving unit, e.g. ``"oz (ounce)"``.

            Parameters
            ----------
            code : str
                The unit code, e.g. ``"oz"``.

            Returns
            -------
            str
                The code with its name in brackets, or just the code when the
                two are the same (e.g. ``"bar"``).
            """
            return f"{code} ({unit_names[code]})" if code != unit_names[code] else code

        def food_form(food_id: int | None) -> None:
            """
            Show the food form inside the Add food or Edit food pop-up.

            The fields start with the food's saved values, or with defaults
            for a new food (unit g, macros 0). The Category box lists
            sub-categories only, plus "+ New category", which shows boxes
            to create one (and its top-level category if needed). Save
            checks and writes the food (and the new category, in the same
            transaction), Cancel closes without saving, and Delete food
            (edit only, after ticking the confirm box) removes it. A
            validation error is shown in the pop-up and the pop-up stays open.

            This is not a ``st.form``: inside a form, choosing
            "+ New category" could not show the extra boxes until Save.

            Parameters
            ----------
            food_id : int | None
                The food to edit, or None to add a new one.
            """
            if food_id is None:
                values = {
                    "food_name": "",
                    "category_id": None,
                    "serving_size": None,
                    "serving_unit": "g",
                    **dict.fromkeys(MACROS, 0.0),
                }
            else:
                values = food_list.loc[food_id].to_dict()

            category_ids = [*category_labels, NEW_CATEGORY]
            unit_codes = list(unit_names)
            name = st.text_input(
                "Name", value=values["food_name"], max_chars=100, placeholder="e.g. Greek yogurt", key="food_name"
            )
            category_id = st.selectbox(
                "Category",
                category_ids,
                index=category_ids.index(values["category_id"]) if values["category_id"] in category_labels else None,
                format_func=lambda choice: "+ New category" if choice == NEW_CATEGORY else category_labels[choice],
                placeholder="Choose a category",
                key="food_category",
            )
            if category_id == NEW_CATEGORY:
                with st.container(border=True):
                    new_category_fields("food_new_category")
                    st.caption("The new category is saved together with the food.")
            with st.container(horizontal=True):
                serving_size = st.number_input(
                    "Serving size",
                    min_value=0.01,
                    value=values["serving_size"],
                    step=1.0,
                    placeholder="e.g. 100",
                    key="food_serving_size",
                )
                serving_unit = st.selectbox(
                    "Serving unit",
                    unit_codes,
                    index=unit_codes.index(values["serving_unit"]),
                    format_func=unit_label,
                    key="food_serving_unit",
                )
            st.caption("Macros are for one serving.")
            with st.container(horizontal=True):
                macros = {
                    column: st.number_input(
                        macro_label, min_value=0.0, value=float(values[column]), step=1.0, key=f"food_{column}"
                    )
                    for column, macro_label in MACROS.items()
                }
            with st.container(horizontal=True):
                save = st.button("Save", type="primary", icon=":material/save:", key="food_save")
                cancel = st.button("Cancel", key="food_cancel")

            if cancel:
                close_food_dialog()
                st.rerun()
            if save:
                new_values = {
                    "food_name": name,
                    "category_id": category_id,
                    "serving_size": serving_size,
                    "serving_unit": serving_unit,
                    **macros,
                }
                message = f"{'Added' if food_id is None else 'Saved'} {name.strip()}."
                # One food at a time, through the same function that saves
                # a batch: an add, or an update keyed by the food's id.
                # A new category is saved with the food in one transaction.
                try:
                    if category_id == NEW_CATEGORY:
                        category_name, parent_id, new_parent_name = new_category_values("food_new_category")
                        _, brought_back = foods.save_food_in_new_category(
                            user_id, food_id, new_values, category_name, parent_id, new_parent_name
                        )
                        verb = "Brought back" if brought_back else "Created"
                        message += f' {verb} the category "{category_name.strip()}".'
                    elif food_id is None:
                        foods.save_food_changes(user_id, [new_values], {}, [])
                    else:
                        foods.save_food_changes(user_id, [], {food_id: new_values}, [])
                except ValueError as e:
                    st.error(str(e))
                else:
                    close_food_dialog()
                    flash(message)
                    st.rerun()

            if food_id is not None:
                st.divider()
                with st.container(horizontal=True, vertical_alignment="center"):
                    confirm = st.checkbox("Yes, remove this food", key="food_confirm_delete")
                    if st.button("Delete food", icon=":material/delete:", disabled=not confirm, key="food_delete"):
                        foods.save_food_changes(user_id, [], {}, [food_id])
                        close_food_dialog()
                        flash(f"Removed {values['food_name']}.")
                        st.rerun()
                st.caption("Removed foods stay in past logs and recipes.")

        # st.dialog is a decorator. Applying it twice to the same function
        # gives two pop-ups with different titles that share one form.
        # on_dismiss runs close_food_dialog (then reruns the app) when the
        # pop-up is closed with its X, Esc or a click outside it.
        add_food_dialog = st.dialog("Add food", width="medium", on_dismiss=close_food_dialog)(food_form)
        edit_food_dialog = st.dialog("Edit food", width="medium", on_dismiss=close_food_dialog)(food_form)

        # A category renamed or removed since the last run is no longer on
        # offer, so the filter goes back to All (before the box is drawn)
        parent_options = ["All", *categories["parent_name"].unique()]
        if st.session_state.get("food_filter_category") not in parent_options:
            st.session_state["food_filter_category"] = "All"
        with st.container(horizontal=True, vertical_alignment="bottom"):
            parent = st.selectbox("Category", parent_options, key="food_filter_category")
            search = st.text_input("Search", placeholder="e.g. chicken", key="food_filter_search")
            st.button(
                "Add food",
                type="primary",
                icon=":material/add:",
                on_click=open_food_dialog,
                args=(None,),
            )
            st.button("Manage categories", icon=":material/category:", on_click=open_category_dialog)

        view = food_list
        if parent != "All":
            view = view[view["parent_name"] == parent]
        if search.strip():
            view = view[view["food_name"].str.contains(search.strip(), case=False, regex=False)]
        # The text in the "edit" column is the label of each row's button
        view = view.assign(unit_label=view["serving_unit"].map(unit_label), edit=":material/edit: Edit")

        def open_clicked_food() -> None:
            """
            Open the Edit food pop-up for the row whose Edit button was pressed.

            This is the Edit column's ``on_click`` callback. It runs at the
            start of the next run, so ``view`` is still the table that was
            clicked. The click's ``row`` is a position (0, 1, 2...) in that
            table, and its index holds the food ids.
            """
            click = st.session_state["food_edit_click"]
            open_food_dialog(int(view.index[click.row]))

        if view.empty:
            st.info("No foods match these filters.")
        else:
            st.dataframe(
                view,
                hide_index=True,
                alt="Your foods",
                column_order=["edit", "food_name", "category_label", "serving_size", "unit_label", *MACROS],
                column_config={
                    "edit": st.column_config.ButtonColumn(
                        "Edit", type="tertiary", on_click=open_clicked_food, key="food_edit_click"
                    ),
                    "food_name": st.column_config.TextColumn("Food", width="large"),
                    "category_label": st.column_config.TextColumn("Category", width="medium"),
                    "serving_size": st.column_config.NumberColumn("Serving", format="%g", width="small"),
                    "unit_label": st.column_config.TextColumn("Unit", width="small"),
                    **{
                        column: st.column_config.NumberColumn(macro_label, format="%g", width="small")
                        for column, macro_label in MACROS.items()
                    },
                },
            )
            st.caption("Press Edit on a row to change it. Macros are for one serving.")

        # Only one pop-up can be open per run. A food removed since the
        # pop-up opened (e.g. in another browser tab) just closes it.
        if EDITING_FOOD in st.session_state:
            food_id = st.session_state[EDITING_FOOD]
            if food_id is None:
                add_food_dialog(None)
            elif food_id in food_list.index:
                edit_food_dialog(food_id)
            else:
                close_food_dialog()
        elif MANAGING_CATEGORIES in st.session_state:
            category_dialog()
