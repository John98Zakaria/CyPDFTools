import re
from collections import namedtuple
from dataclasses import dataclass

from tqdm import tqdm

from PDFObjects import PDFDict
from utils import Ibytable

XrefEntry = namedtuple("XrefEntry", ["address", "revision", "in_use_entry"])


@dataclass
class PDFStream(Ibytable):
    """
    Represents objects that contain a stream
    """

    def __init__(self, stream_dict: PDFDict, object_number, object_rev, start_address, inuse, file, pdfObjectsFunc):
        """
        :param stream_dict: PDFDict describing the stream
        :param object_number: Object Number
        :param object_rev: Object Number
        :param start_address: stream start address
        :param inuse: n for in use f for free
        :param file:  file object
        """
        self.stream_dict = stream_dict
        self.object_number = int(object_number)
        self.object_rev = int(object_rev)
        self.startAddress = int(start_address)
        self.length = self.stream_dict[b"/Length"]
        self.inuse = inuse
        self.file = file
        self.objectsDict = pdfObjectsFunc


    def read_stream(self) -> bytes:
        """
        Read stream from file

        :param file: file_reader
        :return: streamobject
        """
        self.file.seek(self.startAddress)
        try:
            length = int(self.length)
            return self.file.read(length)

        except TypeError:
            self.length = int(self.objectsDict(self.length.objectref).stream_dict)
            return self.file.read(self.length)

    def offset_references(self, offset: int) -> None:
        """
        Increments the reference objects inside the data structure

        :param offset: offset value
        """
        self.stream_dict.offset_references(offset)
        self.object_number += offset

    def __bytes__(self) -> bytes:
        """
        Converts the object and all the underlying objects to bytes

        :return: Byte representation of the file
        """
        byte_representation = f"{self.object_number} {self.object_rev} obj\n".encode("utf-8")
        byte_representation += bytes(self.stream_dict)
        byte_representation += b"\nstream\n"
        byte_representation += self.read_stream()
        byte_representation += "\nendsteam\nendobj\n".encode("utf-8")
        return byte_representation

    def __str__(self):
        return f"StreamObject {self.stream_dict}"

    def __getitem__(self, item):
        return self.stream_dict[item]

    def __setitem__(self, key, value):
        self.stream_dict[key] = value


class PDFObject(Ibytable):
    def __init__(self, stream_dict, object_number, object_rev, inuse):
        self.stream_dict = stream_dict
        self.object_number = int(object_number)
        self.object_rev = object_rev
        self.inuse = inuse


    def read_stream(self):  # is there just for the state design pattern
        return b""

    def offset_references(self, offset: int) -> None:
        """
        Increments the reference objects inside the data structure

        :param offset: offset value
        """
        self.object_number += offset
        try:
            self.stream_dict.offset_references(offset)
        except AttributeError:
            pass

    def __bytes__(self) -> bytes:
        """
        Converts the object and all the underlying objects to bytes

        :return: Byte representation of the file
        """
        byte_representation = f"{self.object_number} {self.object_rev} obj\n".encode("utf-8")
        byte_representation += bytes(self.stream_dict)
        byte_representation += "\nendobj\n".encode("utf-8")
        return byte_representation

    def __str__(self):
        return f"Object {self.stream_dict}"

    def __getitem__(self, item):
        return self.stream_dict[item]

    def __setitem__(self, key, value):
        self.stream_dict[key] = value


class XRefTable(Ibytable):
    """
    Represents the XRef table of a PDF file
    """

    def __init__(self, xref_table: list, parsed=False):
        self.table = self.parse_table(xref_table) if not parsed else xref_table

    def __add__(self, other):
        self.table = self.table + other.table

    def __getitem__(self, item):
        return self.table[item]

    @staticmethod
    def parse_table(table: list) -> list:
        """
        Parses list of XRef bytes

        :param table: A list containing XRef entries
        :return: list of XRef Entries
        """
        xref_regex = re.compile(br"(\d+) (\d+) (n|f)")

        def parse_entry(entry: bytes) -> XrefEntry:
            """
            Parses an XRefEntrie

            :param entry: An entry of the XRefTable
            :return: :class:`PDFStructureObjects.XrefEntry`
            """
            parsed_entry = xref_regex.search(entry)
            return XrefEntry(int(parsed_entry.group(1)), int(parsed_entry.group(2)),
                             str(parsed_entry.group(3), "utf-8"))

        i = 0
        for value in tqdm(table, "Parsing Xref"):
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
