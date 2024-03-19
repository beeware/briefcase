class PartialMatchString(str):
    def __eq__(self, other):
        return self in other


class NoMatchString(str):
    def __eq__(self, other):
        return self not in other
