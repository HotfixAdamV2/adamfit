/*
    Migration: 000026_seed_exercise_type (up)

    What:
        Inserts the exercise types: strength and cardio.

    Why:
        Every standard exercise (000033) and every user exercise needs a
        valid type.
*/

INSERT INTO exercise_type (
    type_code,
    type_name,
    sort_order
)
VALUES
    ('strength', 'Strength', 1),
    ('cardio', 'Cardio', 2);
