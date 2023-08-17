class Histogram:
    def __init__(self):
        self._counts = {}
        self._size = 0
        self._unique_elements = 0

    def add(self, element, count=1):
        if count < 1:
            raise ValueError(f"Invalid count {count}. Must be >= 1.")
        if element not in self._counts:
            self._counts[element] = 0
            self._unique_elements += 1
        self._counts[element] = self._counts[element] + count
        self._size += count

    def get_count(self, element):
        if element in self._counts:
            return self._counts[element]
        else:
            return 0
    def unique_elements(self):
        return self._unique_elements

    def max_count(self):
        return max(self._counts.values())

    def keys(self):
        return self._counts.keys()

    def values(self):
        return self._counts.values()

    def __iter__(self):
        return iter(self._counts.items())

    def __contains__(self, item):
        return item in self._counts and self._counts[item] > 0

    def __str__(self):
        return self._counts.__str__()

    def __len__(self):
        return self._size