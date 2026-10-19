"""Conversions between metric and imperial units.

The database always stores kilograms and centimetres. These helpers convert
to and from what the user wants to see.
"""

LB_PER_KG = 2.20462262185
CM_PER_INCH = 2.54
INCHES_PER_FOOT = 12
GRAMS_PER_OZ = 28.349523125


def kg_to_lb(kg: float) -> float:
    """
    Convert kilograms to pounds.

    Parameters
    ----------
    kg : float
        Weight in kilograms.

    Returns
    -------
    float
        Weight in pounds.
    """
    return kg * LB_PER_KG


def lb_to_kg(lb: float) -> float:
    """
    Convert pounds to kilograms.

    Parameters
    ----------
    lb : float
        Weight in pounds.

    Returns
    -------
    float
        Weight in kilograms.
    """
    return lb / LB_PER_KG


def cm_to_ft_in(cm: float) -> tuple[int, float]:
    """
    Convert centimetres to feet and inches.

    Parameters
    ----------
    cm : float
        Height in centimetres.

    Returns
    -------
    tuple[int, float]
        Whole feet and the remaining inches (rounded to one decimal).
    """
    total_inches = round(cm / CM_PER_INCH, 1)
    feet = int(total_inches // INCHES_PER_FOOT)
    return feet, round(total_inches - feet * INCHES_PER_FOOT, 1)


def ft_in_to_cm(feet: int, inches: float) -> float:
    """
    Convert feet and inches to centimetres.

    Parameters
    ----------
    feet : int
        Whole feet.
    inches : float
        Additional inches.

    Returns
    -------
    float
        Height in centimetres.
    """
    return (feet * INCHES_PER_FOOT + inches) * CM_PER_INCH


def weight_label(unit_system: str) -> str:
    """
    Return the weight unit abbreviation for a unit system.

    Parameters
    ----------
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.

    Returns
    -------
    str
        ``"lb"`` for imperial, ``"kg"`` for metric.
    """
    return "lb" if unit_system == "imperial" else "kg"


def to_display_weight(kg: float, unit_system: str) -> float:
    """
    Convert a stored kilogram value to the user's preferred unit.

    Parameters
    ----------
    kg : float
        Weight in kilograms, as stored in the database.
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.

    Returns
    -------
    float
        Weight in pounds (imperial) or kilograms (metric).
    """
    return kg_to_lb(kg) if unit_system == "imperial" else kg


def from_display_weight(value: float, unit_system: str) -> float:
    """
    Convert a weight the user entered into kilograms for storage.

    Parameters
    ----------
    value : float
        Weight in the user's preferred unit.
    unit_system : str
        Either ``"imperial"`` or ``"metric"``.

    Returns
    -------
    float
        Weight in kilograms.
    """
    return lb_to_kg(value) if unit_system == "imperial" else value
