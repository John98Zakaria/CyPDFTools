from dataclasses import dataclass
from utills import Ibytable


class IndirectObjectRef(Ibytable):
    """
    Represents indirect object references
    7.3.10 PDF 32000-1:2008
    """

    def __init__(self, objectref ,generationNum):
        self.objectref = int(objectref)
        self.generationNum = int(generationNum)


    def __str__(self):
        return f"{self.objectref} {self.generationNum} R"

    def __repr__(self):
        return self.__str__()

    def __int__(self):
        return self.objectref

    def __eq__(self, other):
        return self.objectref == other.objectref



    def offset_references(self, offset: int) -> None:
        """
        Increments the reference objects inside the data structure
        :param offset: offset value
        """
        self.add_offset()

    def add_offset(self, offset: int):
        self.objectref += offset

    def to_bytes(self) -> bytes:
        """
        Converts Indirect Reference to bytes
        :return: bytes representation of the indirect reference
        """
        return self.__str__().encode("utf-8")


@dataclass
class PDFArray(Ibytable):
    """
    A Wrapper for PDF Arrays
    7.3.6 PDF 32000-1:2008
    """

    def __init__(self, data: list):
        self.data = data

    def __str__(self):
        return "[" + ",".join(map(str, self.data)) + "]"

    def __eq__(self, other):
        return self.data == other.data

    def __repr__(self):
        return self.__str__()

    def offset_references(self, offset: int):
        """
        Increments the reference objects inside the data structure
        :param offset: offset value
        """
        for index, value in enumerate(self.data):
            if type(value) == Ibytable:
                self.data[index] = value.offset_references(offset)

    def to_bytes(self)->bytes:
        bytes_representation = b"["
        for item in self.data:
            bytes_representation+=self.itemToByte(item) + b" "
        bytes_representation +=b"]"
        return bytes_representation


@dataclass
class PDFDict(Ibytable):
    """
    A wrapper for PDF Dictionaries
    7.3.8 PDF 32000-1:2008
    """

    def __init__(self, data: dict):
        self.data = data

    def increment_references(self, offset: int) -> None:
        """
        Increments the reference objects inside the data structure
        :param offset: offset value
        """
        for key, value in zip(self.data.keys(), self.data.values()):
            if type(value) == Ibytable:
                self.data[key] = value.offset_references(offset)

    def __getitem__(self, item):
        return self.data[item]

    def __str__(self):

        return str(self.data)

    def __eq__(self, other):
        self.data = other.data

    def __repr__(self):
        return self.__str__()

    def to_bytes(self)->bytes:
        out_string = b"<<\n"
        for key, value in zip(self.data.keys(), self.data.values()):
            if issubclass(type(value), Ibytable):
                value = value.to_bytes()
            out_string += key + b" " + value + b"\n"
        out_string = out_string + b">>"
        return out_string


if __name__ == '__main__':
    p = PDFArray(["1", "2", "3"])
    print(p)
    print(p.__repr__())
    print(issubclass(type(p), Ibytable))
