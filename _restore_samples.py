"""Restores sample_a.py and sample_b.py to their original undocumented baselines."""

sample_a = """\
# sample_a.py

def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    if len(numbers) == 0:
        return 0
    return total / len(numbers)


def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        Sum of a and b.
    \"\"\"
    return a + b


def find_max(numbers):
    if not numbers:
        return None
    max_num = numbers[0]
    for n in numbers:
        if n > max_num:
            max_num = n
    return max_num


def is_even(n):
    return n % 2 == 0


class Processor:
    def process(self, data):
        for item in data:
            if item is None:
                continue
            print(item)
"""

sample_b = """\
# sample_b.py

def generator_example(n):
    for i in range(n):
        yield i


def raises_example(x):
    \"\"\"Raises example.

    Args:
        x: Input value.

    Returns:
        Double of x.
    \"\"\"
    if x < 0:
        raise ValueError("negative")
    return x * 2


def multiply(a, b):
    return a * b


def check_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def get_current_date():
    import datetime
    return datetime.datetime.now()
"""

with open("sample_a.py", "w", encoding="utf-8") as f:
    f.write(sample_a)

with open("sample_b.py", "w", encoding="utf-8") as f:
    f.write(sample_b)

print("sample_a.py and sample_b.py restored to original undocumented baselines.")

# Quick verification
import doc_steward

for fname in ["sample_a.py", "sample_b.py"]:
    entities = doc_steward.get_entity_list(fname)
    funcs = [e for e in entities if e["Type"] in ("Function", "Method")]
    total = len(funcs)
    documented = sum(1 for e in funcs if e["Has Docstring"])
    coverage = round(documented / total * 100, 1) if total > 0 else 0.0
    print(f"{fname}: {documented}/{total} documented => {coverage}% coverage")
