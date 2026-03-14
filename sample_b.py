"""Sample b.py."""

from datetime import datetime


def generator_example(n):
    """Generate example.

    Args:
        n: Description of n.

    Yields:
        Description of yielded values.
    """
    for i in range(n):
        yield i


def raises_example(x):
    """Raise example.

    Args:
        x: Description of x.

    Returns:
        Description of the return value.

    Raises:
        Exception: Description of when this exception is raised.
    """
    if x < 0:
        raise ValueError("negative")
    return x * 2


def multiply(a, b):
    """Multiply.

    Args:
        a: Description of a.
        b: Description of b

    Returns:
        Description of the return value.
    """
    return a * b


def check_prime(n):
    """Check prime.

    Args:
        n: Description of n.

    Returns:
        Description of the return value.
    """
    if n < 2:
        return False
    for value in range(2, int(n**0.5) + 1):
        if n % value == 0:
            return False
    return True


def current_datetime():
    """
    Return the current local date and time.

    Returns:
        datetime.datetime: The current local date and time as a ``datetime`` object.
    """
    return datetime.now()
  