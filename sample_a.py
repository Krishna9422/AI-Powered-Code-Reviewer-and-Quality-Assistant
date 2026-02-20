"""Sample_a.py module."""


def calculate_average(numbers):
 
    total = 0
    for n in numbers:
        total += n
    if len(numbers) == 0:
        return 0
    return total / len(numbers)



def add(a: int, b: int) -> int:

    return a + b



class Processor:
    
    def process(self, data):
        """Process.

        Args:
            data: Description of data.

        Returns:
            Description of the return value.
        """
        for item in data:
            if item is None:
                continue
            print(item)