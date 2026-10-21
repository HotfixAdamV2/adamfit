/*
    Migration: 000008_seed_serving_unit (up)

    What:
        Inserts the serving units: mass (g, oz), volume (ml, fl oz, cup,
        tbsp, tsp) and count units (piece, serving, slice, and packaged or
        naturally counted items such as bar, can, egg and tortilla).

    Why:
        Every standard food (000010) and every user food needs a valid
        unit. The list covers every unit used in data/food_list.csv, plus
        common household measures for foods users add themselves.

    Notes:
        - Conversion factors are exact US customary definitions.
        - Codes are short, lowercase and singular. The CSV's plural or
          long forms map onto them (grams -> g, ounces -> oz, slices ->
          slice, balls -> ball, donuts -> donut, second spray -> spray).
        - spray is a one-second spray of cooking oil.
        - sort_order lists mass, then volume, then the generic count units,
          then the specific count units alphabetically.
*/

INSERT INTO serving_unit (
    unit_code,
    unit_name,
    unit_type,
    grams_per_unit,
    ml_per_unit,
    sort_order
)
VALUES
    ('g', 'gram', 'mass', 1, NULL, 1),
    ('oz', 'ounce', 'mass', 28.349523, NULL, 2),
    ('ml', 'millilitre', 'volume', NULL, 1, 3),
    ('fl oz', 'fluid ounce', 'volume', NULL, 29.573530, 4),
    ('cup', 'cup', 'volume', NULL, 236.588237, 5),
    ('tbsp', 'tablespoon', 'volume', NULL, 14.786765, 6),
    ('tsp', 'teaspoon', 'volume', NULL, 4.928922, 7),
    ('piece', 'piece', 'count', NULL, NULL, 8),
    ('serving', 'serving', 'count', NULL, NULL, 9),
    ('slice', 'slice', 'count', NULL, NULL, 10),
    ('bag', 'bag', 'count', NULL, NULL, 11),
    ('ball', 'ball', 'count', NULL, NULL, 12),
    ('bar', 'bar', 'count', NULL, NULL, 13),
    ('cake', 'cake', 'count', NULL, NULL, 14),
    ('can', 'can', 'count', NULL, NULL, 15),
    ('carton', 'carton', 'count', NULL, NULL, 16),
    ('container', 'container', 'count', NULL, NULL, 17),
    ('donut', 'donut', 'count', NULL, NULL, 18),
    ('egg', 'egg', 'count', NULL, NULL, 19),
    ('packet', 'packet', 'count', NULL, NULL, 20),
    ('pita', 'pita', 'count', NULL, NULL, 21),
    ('shake', 'shake', 'count', NULL, NULL, 22),
    ('spray', 'one-second spray', 'count', NULL, NULL, 23),
    ('tortilla', 'tortilla', 'count', NULL, NULL, 24);
