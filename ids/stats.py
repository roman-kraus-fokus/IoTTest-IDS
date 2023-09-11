
class Stats:
    def __init__(self):
        self.values = []
    
    def add_value(self, value):
        self.values.append(value)

    def get_max(self):
        if len(self.values) == 0:
            return 0
        return max(value for value in self.values)

    def get_min(self):
        if len(self.values) == 0:
            return 0
        return min(value for value in self.values)

    def get_average(self):
        if len(self.values) == 0:
            return 0
        return sum(value for value in self.values) / len(self.values)
