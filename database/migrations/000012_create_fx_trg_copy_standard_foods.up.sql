/*
    Migration: 000012_create_fx_trg_copy_standard_foods (up)

    What:
        Creates the trigger function fx_trg_copy_standard_foods and attaches
        it to app_user, so every new user gets a copy of standard_food in
        their own food list. Also copies the list to every existing user.

    Why:
        Each user owns an editable copy of the standard foods. Doing the
        copy in the database means it happens no matter how the user is
        created (the CLI today, maybe an API later).
*/

-- Trigger function
CREATE FUNCTION fx_trg_copy_standard_foods()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO food (
        user_id,
        food_name,
        category_id,
        serving_size,
        serving_unit,
        calories,
        protein_g,
        carbs_g,
        fat_g,
        fiber_g,
        standard_food_id
    )
    SELECT
        NEW.user_id,
        food_name,
        category_id,
        serving_size,
        serving_unit,
        calories,
        protein_g,
        carbs_g,
        fat_g,
        fiber_g,
        standard_food_id
    FROM standard_food;

    RETURN NEW;
END;
$$;

-- Trigger assignments
CREATE TRIGGER trg_app_user_copy_standard_foods
    AFTER INSERT ON app_user
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_copy_standard_foods();

-- Backfill users that already exist
INSERT INTO food (
    user_id,
    food_name,
    category_id,
    serving_size,
    serving_unit,
    calories,
    protein_g,
    carbs_g,
    fat_g,
    fiber_g,
    standard_food_id
)
SELECT
    au.user_id,
    sf.food_name,
    sf.category_id,
    sf.serving_size,
    sf.serving_unit,
    sf.calories,
    sf.protein_g,
    sf.carbs_g,
    sf.fat_g,
    sf.fiber_g,
    sf.standard_food_id
FROM app_user AS au
CROSS JOIN standard_food AS sf;
