from dataclasses import dataclass


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

@dataclass
class PDFArray:
    def __init__(self, data: list):
        self.data = data

    def increment_references(self, offset):
        for index, value in enumerate(self.data):
            if type(value) == IndirectObjectRef:
                self.data[index] = value.addOffset(offset)

    def __str__(self):
        return "["+" ".join(map(str,self.data)) + "]"

    def __repr__(self):
        return self.__str__()

@dataclass
class PDFDict:
    def __init__(self,data:dict):
        self.data = data

    def increment_references(self, offset):
        for key, value in zip(self.data.keys(),self.data.values()):
            if type(value) == IndirectObjectRef:
                self.data[key] = value.addOffset(offset)

    def __str__(self):
        out_string = ""
        for key, value in zip(self.data.keys(), self.data.values()):
            out_string+=f"{key} {value}\n"
        out_string = "<<\n" + out_string + "\n>>"
        return out_string

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    p = PDFArray(["1","2","3"])
    print(p)
    print(p.__repr__())