class IndirectObjectRef:
    def __init__(self, objectref):
        self.objectref = int(objectref)

    def __str__(self):
        return f"{self.objectref} 0 R"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.objectref == other.objectref

    def addOffset(self, offset):
        self.objectref += offset