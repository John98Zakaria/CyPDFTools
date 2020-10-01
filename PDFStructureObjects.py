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

    def to_bytes(self, file: io.BytesIO) -> bytes:
        byte_representation = f"{self.object_number} {self.object_rev} obj\n".encode("utf-8")
        byte_representation += self.itemToByte(self.stream_dict)
        byte_representation += b"\nstream\n"
        byte_representation += self.read_stream(file)
        byte_representation += "\nendsteam\nendobj\n".encode("utf-8")
        return byte_representation

    def __str__(self):
        return f"StreamObject {self.stream_dict}"


class PDFObject(Ibytable):
    def __init__(self, stream_dict, object_number, object_rev, startAdress, inuse):
        self.stream_dict = stream_dict
        self.startAddress = startAdress
        self.object_number = object_number
        self.object_rev = object_rev
        self.inuse = inuse

    def read_stream(self, file: io.BytesIO):
        return b""

    def to_bytes(self, file: io.BytesIO) -> bytes:
        byte_representation = f"{self.object_number} {self.object_rev} obj\n".encode("utf-8")
        byte_representation += self.itemToByte(self.stream_dict)
        byte_representation += "\nendobj\n".encode("utf-8")
        return byte_representation

    def __str__(self):
        return f"Object {self.stream_dict}"


class XRefTable(Ibytable):
    def __init__(self, xref_address: int, xref_table: list,parsed= False):
        self.address = xref_address
        self.table = self.parse_table(xref_table) if not parsed else xref_table

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
