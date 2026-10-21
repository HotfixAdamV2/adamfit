/*
    Migration: 000007_create_serving_unit (up)

    What:
        Creates the serving_unit lookup table: every unit a food's serving
        can be measured in (g, oz, cup, piece, ...).

    Why:
        standard_food and food (000009, 000011) reference this table with
        a foreign key, so adding a unit is one INSERT rather than a change
        to CHECK constraints on two tables. The table also says how to
        convert weights, so the app can show a 4 oz serving in grams (or
        100 g in ounces).

    Notes:
        - unit_code is a natural primary key (no sequence). It is the value
          stored in standard_food.serving_unit and food.serving_unit, so
          foods stay readable without a join.
        - unit_type is 'mass', 'volume' or 'count'. Mass units have
          grams_per_unit, volume units have ml_per_unit, count units
          (piece, bar, ...) have neither.
*/

-- Create the table
CREATE TABLE serving_unit (
    -- Fields
    unit_code VARCHAR(20) NOT NULL,
    unit_name VARCHAR(30) NOT NULL,
    unit_type VARCHAR(10) NOT NULL,
    grams_per_unit NUMERIC(12, 6),
    ml_per_unit NUMERIC(12, 6),
    sort_order SMALLINT NOT NULL DEFAULT 0,
    -- Constraints
    CONSTRAINT pk_serving_unit_unit_code PRIMARY KEY (unit_code),
    CONSTRAINT unq_serving_unit_unit_name UNIQUE (unit_name),
    CONSTRAINT chk_serving_unit_unit_type CHECK (unit_type IN ('mass', 'volume', 'count')),
    CONSTRAINT chk_serving_unit_grams_per_unit CHECK (
        (unit_type = 'mass' AND grams_per_unit > 0)
        OR (unit_type <> 'mass' AND grams_per_unit IS NULL)
    ),
    CONSTRAINT chk_serving_unit_ml_per_unit CHECK (
        (unit_type = 'volume' AND ml_per_unit > 0)
        OR (unit_type <> 'volume' AND ml_per_unit IS NULL)
    )
);

-- Give grants
-- None needed: the master role owns the table.
