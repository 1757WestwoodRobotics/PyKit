def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp a value between a minimum and maximum value.

    Args:
        value (float): The value to clamp.
        min_value (float): The minimum value.
        max_value (float): The maximum value.

    Returns:
        float: The clamped value.
    """
    return max(min_value, min(value, max_value))


def sign(value: float) -> float:
    """Returns the sign of the value. If value > 0, 1, value < 0, -1, value = 0, 0

    Args:
        value (float): the value to get the sign of

    Returns:
        float: the sign of the value
    """
    return (value > 0) - (value < 0)


def deadband(value: float, threshold: float) -> float:
    """Applies a deadband to the value. If the absolute value of the value is less than the threshold, returns 0. Otherwise, returns the value.

    Args:
        value (float): the value to apply the deadband to
        threshold (float): the deadband threshold

    Returns:
        float: the value after applying the deadband
    """
    if abs(value) < threshold:
        return 0.0
    return value
