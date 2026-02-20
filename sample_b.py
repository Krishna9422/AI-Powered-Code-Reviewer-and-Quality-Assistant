"""Sample_b.py module."""

# sample_b.py

def generator_example(n):
    """Generator example.

    Args:
        n: Description of n.

    Returns:
        Description of the return value.
    """
    for i in range(n):
        yield i


def raises_example(x):
    """Raises example.

    Args:
        x: Input value.

    Returns:
        Double of x.
    """
    if x < 0:
        raise ValueError("negative")
    return x * 2


def multiply(a, b):
    """Multiply.

    Args:
        a: Description of a.
        b: Description of b.

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
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def get_current_date():
    """Get current date.


    Returns:
        Description of the return value.
    """
    import datetime
    return datetime.datetime.now()
