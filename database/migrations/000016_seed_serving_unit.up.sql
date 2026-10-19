/*
    Migration: 000016_seed_serving_unit (up)

    What:
        Inserts the serving units: the eight from the old CHECK
        constraints, plus oz, fl oz, bar, bag, can and container.

    Why:
        Ounces are how most US labels state meat servings. The count units
        cover packaged foods (protein bars, chips, soup, shakes).

    Notes:
        - Conversion factors are exact US customary definitions.
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
    ('slice', 'slice', 'count', NULL, NULL, 9),
    ('serving', 'serving', 'count', NULL, NULL, 10),
    ('bar', 'bar', 'count', NULL, NULL, 11),
    ('bag', 'bag', 'count', NULL, NULL, 12),
    ('can', 'can', 'count', NULL, NULL, 13),
    ('container', 'container', 'count', NULL, NULL, 14);
