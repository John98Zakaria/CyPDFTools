from dataclasses import dataclass

from utils import Ibytable


class IndirectObjectRef(Ibytable):
    """
    Represents indirect object references
    7.3.10 PDF 32000-1:2008
    """

    def __init__(self, objectref, generation_number):
        self.objectref = int(objectref)
        self.generationNum = int(generation_number)

    def __str__(self):
        return f"IndirectObjectRef({self.objectref},{self.generationNum})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.objectref == other.objectref and self.generationNum == other.generationNum

    def offset_references(self, offset: int) -> None:
        """
        Increments the reference objects inside the data structure

        :param offset: offset value
        """
        self.add_offset(offset)

    def add_offset(self, offset: int):
        self.objectref += offset

    def __bytes__(self) -> bytes:
        """
        Converts Indirect Reference to bytes

        :return: bytes representation of the indirect reference
        """
        return f"{self.objectref} {self.generationNum} R".encode("utf-8")


@dataclass
class PDFArray(Ibytable):
    """
    A Wrapper for PDF Arrays
    7.3.6 PDF 32000-1:2008
    """

    def __init__(self, data: list):
        self.data = data

    def __str__(self):
        return f"PDFArray([{','.join(map(str, self.data))}])"

    def __eq__(self, other):
        return self.data == other.data

    def __repr__(self):
        return self.__str__()

    def __contains__(self, item):
        return item in self.data

    def __getitem__(self, item):
        return self.data[item]

    def remove(self,item):
        self.data.remove(item)

    def offset_references(self, offset: int):
        """
        Increments the reference objects inside the data structure

        :param offset: offset value
        """
        for index, value in enumerate(self.data):
            if issubclass(type(value), Ibytable):
                value.offset_references(offset)

    def __bytes__(self) -> bytes:
        """
        Converts the object to bytes

        :return: Bytes representation of the object
        """
        bytes_representation = b"["
        for item in self.data:
            bytes_representation += bytes(item) + b" "
        bytes_representation += b"]"
        return bytes_representation


@dataclass
class PDFDict(Ibytable):
    """
    A wrapper for PDF Dictionaries
    7.3.8 PDF 32000-1:2008
    """

    def __init__(self, data: dict):
        self.data = data

    def offset_references(self, offset: int) -> None:
        """
        Increments the reference objects inside the data structure

        :param offset: offset value
        """
        for key, value in zip(self.data.keys(), self.data.values()):
            if issubclass(type(value), Ibytable):
                value.offset_references(offset)

    def update(self, other):
        self.data.update(other.data)

    def __contains__(self, item):
        return item in self.data

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __str__(self):

        return f"PDFDict({str(self.data)})"

    def __eq__(self, other):
        return self.data == other.data

    def __repr__(self):
        return self.__str__()

    def __bytes__(self) -> bytes:
        """
        Converts the object to bytes

        :return: Bytes representation of the object
        """
        out_string = b"<<\n"
        for key, value in zip(self.data.keys(), self.data.values()):
            value = bytes(value)
            out_string += key + b" " + value + b"\n"
        out_string = out_string + b">>"
        return out_string


if __name__ == '__main__':
    p = PDFArray(["1", "2", "3"])
    print(p)
    print(p.__repr__())
    print(issubclass(type(p), Ibytable))
