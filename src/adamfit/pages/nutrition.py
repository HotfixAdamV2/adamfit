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
if food_tab.open:
    with food_tab:
        categories = foods.get_categories()
        category_labels = dict(zip(categories["category_id"], categories["label"]))
        unit_names = foods.get_serving_units()["unit_name"].to_dict()

        with st.container(horizontal=True, vertical_alignment="bottom"):
            parent = st.selectbox(
                "Category",
                ["All", *categories["parent_name"].unique()],
                key="food_filter_category",
            )
            search = st.text_input("Search", placeholder="e.g. chicken", key="food_filter_search")

        view = food_list
        if parent != "All":
            view = view[view["parent_name"] == parent]
        if search.strip():
            view = view[view["food_name"].str.contains(search.strip(), case=False, regex=False)]
        # The editor needs a plain 0, 1, 2... index to allow new rows, so the
        # food ids are kept in a list that lines up with the row positions
        ids = view.index.tolist()
        view = view[foods.FOOD_FIELDS].reset_index(drop=True)

        # Edits are matched to rows by position, so the key includes the
        # filters (a different filter is a different table) and a version
        # that is bumped after saving (to clear the saved edits)
        version = st.session_state.setdefault("foods_editor_version", 0)
        editor_key = f"foods_editor_{version}_{parent}_{search.strip().lower()}"
        with st.form("foods_form", border=False):
            st.data_editor(
                view,
                hide_index=True,
                num_rows="dynamic",
                key=editor_key,
                alt="Your foods",
                column_config={
                    "food_name": st.column_config.TextColumn("Food", width="large", required=True, max_chars=100),
                    "category_id": st.column_config.SelectboxColumn(
                        "Category",
                        options=list(category_labels),
                        format_func=category_labels.get,
                        required=True,
                        width="medium",
                    ),
                    "serving_size": st.column_config.NumberColumn(
                        "Serving", min_value=0.01, format="%g", required=True, width="small"
                    ),
                    "serving_unit": st.column_config.SelectboxColumn(
                        "Unit",
                        options=list(unit_names),
                        format_func=lambda code: f"{code} ({unit_names[code]})" if code != unit_names[code] else code,
                        required=True,
                        default="g",
                        width="small",
                    ),
                    **{
                        column: st.column_config.NumberColumn(
                            macro_label, min_value=0, default=0, format="%g", width="small"
                        )
                        for column, macro_label in MACROS.items()
                    },
                },
            )
            st.caption(
                "Macros are for one serving. Add a food in the empty row at the bottom. "
                "Select rows and press Delete to remove them. Removed foods stay in past logs and recipes."
            )
            if st.form_submit_button("Save changes", type="primary", icon=":material/save:"):
                changes = st.session_state[editor_key]
                updates = {
                    ids[position]: {**view.iloc[position].to_dict(), **edits}
                    for position, edits in changes["edited_rows"].items()
                    if position not in changes["deleted_rows"]
                }
                deletes = [ids[position] for position in changes["deleted_rows"]]
                try:
                    foods.save_food_changes(user_id, changes["added_rows"], updates, deletes)
                except ValueError as e:
                    st.error(str(e))
                else:
                    count = len(changes["added_rows"]) + len(updates) + len(deletes)
                    flash(f"Saved {count} change{'s' if count != 1 else ''} to your foods.")
                    st.session_state["foods_editor_version"] += 1
                    st.rerun()
