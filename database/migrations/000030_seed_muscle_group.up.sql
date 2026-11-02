/*
    Migration: 000030_seed_muscle_group (up)

    What:
        Inserts the 20 built-in (shared, user_id NULL) muscle groups.

    Why:
        Standard exercises (000033) are tagged with these, and every user
        can tag their own exercises with them. Users can add their own
        groups on top.

    Notes:
        - The list is ordered roughly top to bottom of the body. There is
          no sort_order column; the app sorts by name or by
          muscle_group_id, which follows this order.
*/

INSERT INTO muscle_group (
    muscle_group_name
)
VALUES
    ('Chest'),
    ('Lats'),
    ('Upper Back'),
    ('Lower Back'),
    ('Traps'),
    ('Front Delts'),
    ('Side Delts'),
    ('Rear Delts'),
    ('Biceps'),
    ('Triceps'),
    ('Forearms'),
    ('Abs'),
    ('Obliques'),
    ('Quads'),
    ('Hamstrings'),
    ('Glutes'),
    ('Calves'),
    ('Adductors'),
    ('Abductors'),
    ('Hip Flexors');
