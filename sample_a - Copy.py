"""Sample a.py."""

# sample_a.py

def calculate_average(numbers):
    """Calculate average.

    Args:
        numbers: Description of numbers.

    Returns:
        Description of the return value.
    """
    total = 0
    for n in numbers:
        total += n
    if len(numbers) == 0:
        return 0
    return total / len(numbers)


def add(a: int, b: int) -> int:
    """Add.

    Args:
        a: Description of a.
        b: Description of b.

    Returns:
        Description of the return value.
    """
    return a + b


def find_max(numbers):
    """Find max.

    Args:
        numbers: Description of numbers.

    Returns:
        Description of the return value.
    """
    if not numbers:
        return None
    max_num = numbers[0]
    for n in numbers:
        if n > max_num:
            max_num = n
    return max_num


def is_even(n):
    """
    Check if a number is even.

    :param n: The integer to evaluate
    :type n: int
    :returns: ``True`` if ``n`` is even, otherwise ``Fa
    :rtype: bool
    """
    return n % 2 == 0


