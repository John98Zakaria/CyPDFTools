import io
from collections import namedtuple

from PDFStructureObjects import *
import re
from objectsParser import parse_stream
from utills import ObjectIter


class PDFParser:
    def __init__(self, filePath):
        self.file = open(filePath, "rb+")
        self.filePath = filePath
        self.xRef: XRefTable = XRefTable
        self.trailer_end = 0
        self.xRefParser()
        self.pdfObjects = self.read_all_objects()


    def xRefParser(self):
        self.file.seek(-5, io.SEEK_END)
        count = 0;
        while count != 2:
            self.file.seek(-2, io.SEEK_CUR)
            char = self.file.read(1).decode("utf-8")
            count += char == "\n"
        print(f"{self.file.tell()} In parse")
        self.trailer_end = self.file.tell()
        xrefAddress = int(self.file.readline()[:-1])
        self.file.seek(xrefAddress, io.SEEK_SET)  # Seek to xRefTable
        self.file.readline()
        entries = self.file.readline().decode("UTF-8").split(" ")[1]  # get number of xrefItems
        print(entries)  # get number of xrefItems
        xrefLength = int(entries)
        xRefTable = self.file.readlines(xrefLength * 20 - 1)
        self.xRef = XRefTable(xrefAddress, xRefTable)

    def trailer_parser(self):
        pdf.file.seek(self.xRef.address)
        pdf.file.readlines(len(self.xRef.table) * 20)
        pdf.file.seek(8, io.SEEK_CUR)
        trailerStart = pdf.file.tell()
        content = pdf.file.read(self.trailer_end - 10 - trailerStart)
        print(content)
        trailer_dict = parse_stream(ObjectIter(content.decode("utf-8")))
        print(trailer_dict)
        pass

    def seek_object(self, number: int) -> None:
        address = self.xRef.table[number].address
        print(f"The adress of object {number} is {address}")
        self.file.seek(address, io.SEEK_SET)

    def extract_object(self, number):
        self.seek_object(number)
        inuse = self.xRef.table[number].in_use_entry
        current_char = self.file.read(1)
        assert (current_char.isdigit())
        object_number = current_char
        while current_char != bytes("j", "utf-8"):
            current_char = self.file.read(1)
            object_number += current_char
        numRev = re.match(br"(\d+) (\d+)", object_number)
        num,rev = numRev.group(0),numRev.group(1)
        current_char = self.file.read(1)
        while current_char.isspace():
            current_char = self.file.read(1)
        self.file.seek(-1, io.SEEK_CUR)
        current_line = self.file.readline()
        object_stream = b""
        while True:
            try:
                if bytes("endobj", "utf-8") in current_line or bytes("stream", "utf-8") in current_line:
                    break
                object_stream += current_line
                current_line = self.file.readline()

            except UnicodeDecodeError:
                break
        isStream = current_line.find(bytes("stream", "utf-8"))
        endIndex = isStream if isStream+1 \
            else current_line.find(bytes("endobj", "utf-8"))
        object_stream += current_line[:endIndex]
        assert object_stream[-6:] != bytes("endobj", "utf-8")
        assert object_stream[-6:] != bytes("stream", "utf-8")
        thing = parse_stream(ObjectIter(object_stream.decode("utf-8")))
        if(isStream+1):
            return (PDFStream(thing,0,inuse),num)

        return (PDFObject(thing,0,inuse),num)

    def read_all_objects(self):
        objects = []

        for objectIndex in range(1, self.xRef.__len__()):
            objects.append(self.extract_object(objectIndex))
        objects.sort(key=lambda x:x[1])
        return objects

    @classmethod
    def parse_xRefentry(cls, entry: bytes) -> tuple:
        if type(entry) == bytes:
            entry = entry.decode("utf-8")
        entry = entry.split(" ")[:-1]
        entry[0] = int(entry[0])
        entry[1] = int(entry[1])
        tup = namedtuple("XrefEntry", ["address", "revision", "in_use_entry"])
        return tup(*entry)

    def close(self):
        self.file.close()

    def __str__(self):
        return f"FilePath : {self.filePath}\n" \
               f"{self.xRef}"

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    pdf = PDFParser("test_pdfs/Blatt03.pdf")
    # pdf.trailer_parser()

    print(pdf.xRef)
    print(pdf)
    # print(pdf.extract_object(3)[0])
    # print(pdf.file.readline())
    # print(pdf.file.seek(6870))
    # print(pdf.file.readline())
    # print(pdf.file.readlines(14*20))
    # print(f"Current Trailler Start {pdf.file.tell()}")
    # print(pdf.file.readline())
    # pdf.file.seek(7160)
    # print(pdf.file.read(7342-10-7160))

    #
    # print(pdf.extractobject(8))
    # # obs = pdf.extractObjets()
    # print(pdf.file.seek(5773))
    # print(pdf.file.readline())
    # for o in obs:
    #     print(o)

    # # stream = re.compile(b'stream(.*?)endstream', re.S)
    # st = pdf.file.read(2786)
    # s = st.strip(b'\r\n')
    # try:
    #     print(zlib.decompress(s).decode('UTF-8'))
    #     print("")
    # except:
    #     pass
    # pdf.close()
