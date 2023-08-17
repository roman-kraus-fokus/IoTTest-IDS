
class Stats:
    def __init__(self):
        self.values = []
    
    def add_value(self, value):
        self.values.append(value)

    def get_max(self):
        return max(value for value in self.values)

    def get_min(self):
        return min(value for value in self.values)

    def get_average(self):
        return sum(value for value in self.values) / len(self.values)
