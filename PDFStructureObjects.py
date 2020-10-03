from collections import namedtuple
from dataclasses import dataclass
from utills import Ibytable
import io
import re
from tqdm import tqdm

from PDFObjects import PDFDict

XrefEntry = namedtuple("XrefEntry", ["address", "revision", "in_use_entry"])


@dataclass
class PDFStream(Ibytable):
    def __init__(self, stream_dict: PDFDict, object_number, object_rev, startAdress, inuse):
        self.stream_dict = stream_dict
        self.object_number = int(object_number)
        self.object_rev = int(object_rev)
        self.length = stream_dict[b"/Length"]
        self.startAddress = int(startAdress)

        self.inuse = inuse

    def read_stream(self, file: io.BytesIO) -> bytes:
        file.seek(self.startAddress)
        return file.read(int(self.length))

    def offset_references(self, offset: int) -> None:
        """
        Increments the reference objects inside the data structure
        :param offset: offset value
        """
        self.stream_dict.offset_references(offset)
        self.object_number+=offset



    def to_bytes(self, file: io.BytesIO) -> bytes:
        byte_representation = f"{self.object_number} {self.object_rev} obj\n".encode("utf-8")
        byte_representation += self.itemToByte(self.stream_dict)
        byte_representation += b"\nstream\n"
        byte_representation += self.read_stream(file)
        byte_representation += "\nendsteam\nendobj\n".encode("utf-8")
        return byte_representation

    def __str__(self):
        return f"StreamObject {self.stream_dict}"

    def __getitem__(self, item):
        return self.stream_dict[item]
    def __setitem__(self, key, value):
        self.stream_dict[key] = value


class PDFObject(Ibytable):
    def __init__(self, stream_dict, object_number, object_rev, startAdress, inuse):
        self.stream_dict = stream_dict
        self.startAddress = startAdress
        self.object_number = int(object_number)
        self.object_rev = object_rev
        self.inuse = inuse

    def read_stream(self, file: io.BytesIO):
        return b""

    def offset_references(self, offset: int) -> None:
        """
        Increments the reference objects inside the data structure
        :param offset: offset value
        """
        self.object_number+=offset
        try:
            self.stream_dict.offset_references(offset)
        except AttributeError:
            pass

    def to_bytes(self, file: io.BytesIO) -> bytes:
        byte_representation = f"{self.object_number} {self.object_rev} obj\n".encode("utf-8")
        byte_representation += self.itemToByte(self.stream_dict)
        byte_representation += "\nendobj\n".encode("utf-8")
        return byte_representation

    def __str__(self):
        return f"Object {self.stream_dict}"

    def __getitem__(self, item):
        return self.stream_dict[item]

    def __setitem__(self, key, value):
        self.stream_dict[key] = value

class XRefTable(Ibytable):
    def __init__(self, xref_table: list,parsed= False):
        self.table = self.parse_table(xref_table) if not parsed else xref_table

    def __add__(self, other):
        self.table = self.table + other.table

    def __getitem__(self, item):
        return self.table[item]



    @staticmethod
    def parse_table(table):
        xref_regex = re.compile(b"(\d+) (\d+) (n|f)")

        def parse_entry(entry: bytes) -> tuple:
            parsed_entry = xref_regex.search(entry)
            return XrefEntry(int(parsed_entry.group(1)), int(parsed_entry.group(2)), str(parsed_entry.group(3),"utf-8"))

        i = 0
        for value in tqdm(table,"Parsing Xref"):
            v = parse_entry(value)
            table[i] = v
            i += 1
        return table



    def __len__(self):
        return len(self.table)

    def __str__(self):
        out_string = f"xref\n0 {len(self)}\n"
        for entry in self.table:
            out_string += f"{str(entry.address).zfill(10)} {str(entry.revision).zfill(5)} {entry.in_use_entry} \n"
        return out_string

    def __repr__(self):
        return self.__str__()
