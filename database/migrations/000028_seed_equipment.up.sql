/*
    Migration: 000028_seed_equipment (up)

    What:
        Inserts the equipment types.

    Why:
        Every standard exercise (000033) and every user exercise needs a
        valid equipment code.

    Notes:
        - 'none' ('None / Other') is for exercises that need no gym kit or
          use something not listed, e.g. outdoor running or swimming.
          'bodyweight' is for strength exercises where the body is the
          load (push-up, pull-up).
*/

INSERT INTO equipment (
    equipment_code,
    equipment_name,
    sort_order
)
VALUES
    ('bodyweight', 'Bodyweight', 1),
    ('barbell', 'Barbell', 2),
    ('dumbbell', 'Dumbbell', 3),
    ('kettlebell', 'Kettlebell', 4),
    ('cable', 'Cable', 5),
    ('machine', 'Machine', 6),
    ('band', 'Band', 7),
    ('none', 'None / Other', 8);
