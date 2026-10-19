"""Nutrition page: a daily food log, recipes, and the user's food list."""

from datetime import date, timedelta

import streamlit as st

from adamfit import auth, food_logs, foods, recipes
from adamfit.nutrition import MACROS
from adamfit.ui import entries_editor, flash, item_picker, show_flash

user = auth.current_user()
user_id = user["user_id"]
unit_system = user["unit_system"]

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
        Keyed ``"food:<id>"``, with ``label``, ``serving_size``,
        ``serving_unit`` and ``grams_per_unit`` for ``ui.item_picker``.
    """
    return {
        f"food:{food_id}": {
            "label": f"{row.food_name} · {row.serving_size:g} {row.serving_unit}",
            "serving_size": row.serving_size,
            "serving_unit": row.serving_unit,
            "grams_per_unit": row.grams_per_unit,
        }
        for food_id, row in food_list.iterrows()
    }


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

        def add_to_log(option_key: str, servings: float) -> None:
            """
            Log the food or recipe chosen in the picker.

            Parameters
            ----------
            option_key : str
                ``"food:<id>"`` or ``"recipe:<id>"``.
            servings : float
                Number of servings eaten.
            """
            kind, item_id = option_key.split(":")
            food_logs.add_entry(
                user_id,
                st.session_state["log_date"],
                servings,
                food_id=int(item_id) if kind == "food" else None,
                recipe_id=int(item_id) if kind == "recipe" else None,
            )

        recipe_list = recipes.get_recipes(user_id)
        options = {
            f"recipe:{recipe_id}": {
                "label": f"Recipe: {row.recipe_name} · 1 {row.serving_label}",
                "serving_size": 1.0,
                "serving_unit": row.serving_label,
                "grams_per_unit": None,
            }
            for recipe_id, row in recipe_list.iterrows()
        }
        options.update(food_options())
        item_picker(options, key="log_add", unit_system=unit_system, on_add=add_to_log)

        log = food_logs.get_log(user_id, log_date)
        if log.empty:
            st.info(f"Nothing logged for {log_date:%A, %b %d}. Pick a food or recipe above to start.")
        else:
            entries_editor(
                log,
                key="log_table",
                unit_system=unit_system,
                on_update=lambda entry_id, servings: food_logs.update_entry(user_id, entry_id, servings),
                on_delete=lambda entry_id: food_logs.delete_entry(user_id, entry_id),
                alt=f"Food log for {log_date:%b %d, %Y}",
            )
            st.caption("Change an amount to update the macros. Select rows and press Delete to remove them.")

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
            st.subheader(recipe["recipe_name"])
            st.caption(f"Makes {float(recipe['servings_per_recipe']):g} × {label}. Macros below are per {label}.")
            with st.container(horizontal=True):
                for column, macro_label in MACROS.items():
                    total = float(recipe[f"total_{column}"])
                    st.metric(
                        macro_label,
                        f"{float(recipe[column]):,.0f}" if column == "calories" else f"{float(recipe[column]):.1f}",
                        help=f"Whole recipe: {total:,.1f}",
                        border=True,
                    )

            st.markdown("**Ingredients**")
            item_picker(
                food_options(),
                key=f"recipe_add_{recipe_id}",
                unit_system=unit_system,
                on_add=lambda option_key, servings: recipes.add_ingredient(
                    user_id, recipe_id, int(option_key.split(":")[1]), servings
                ),
                label="Food",
            )
            ingredients = recipes.get_ingredients(user_id, recipe_id)
            if ingredients.empty:
                st.info("No ingredients yet. Add foods above and the macros are calculated for you.")
            else:
                entries_editor(
                    ingredients,
                    key=f"recipe_table_{recipe_id}",
                    unit_system=unit_system,
                    on_update=lambda ingredient_id, servings: recipes.update_ingredient(
                        user_id, ingredient_id, servings
                    ),
                    on_delete=lambda ingredient_id: recipes.delete_ingredient(user_id, ingredient_id),
                    alt=f"Ingredients in {recipe['recipe_name']}",
                )
                st.caption("Totals are for the whole recipe.")

            st.markdown("**Instructions**")
            if recipe["instructions"]:
                st.markdown(recipe["instructions"])
            else:
                st.caption("No instructions yet. Add them under Edit recipe details.")

            with st.expander("Edit recipe details", icon=":material/edit:"):
                with st.form(f"recipe_form_{recipe_id}", border=False):
                    name = st.text_input("Name", value=recipe["recipe_name"], max_chars=100)
                    col_servings, col_label = st.columns(2)
                    servings_per_recipe = col_servings.number_input(
                        "Makes how many servings?",
                        min_value=0.25,
                        value=float(recipe["servings_per_recipe"]),
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
                                    user_id, recipe_id, name, servings_per_recipe, serving_label, instructions
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
