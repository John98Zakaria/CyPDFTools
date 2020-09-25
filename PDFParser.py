import io
from collections import namedtuple
from XRefTable import *
import zlib
import re

class PDFParser:
    def __init__(self, filePath):
        self.file = open(filePath, "rb+")
        self.filePath = filePath
        self.xRef:XRefTable = XRefTable
        # self.xRefParser()


    def xRefParser(self):
        self.file.seek(-5, io.SEEK_END)
        count = 0;
        while count != 2:
            self.file.seek(-2, io.SEEK_CUR)
            char = self.file.read(1).decode("utf-8")
            count += char == "\n"
        xrefAddress = int(self.file.readline()[:-1])
        self.file.seek(xrefAddress, io.SEEK_SET)  # Seek to xRefTable
        self.file.readline()
        entries = self.file.readline().decode("UTF-8").split(" ")[1]  # get number of xrefItems
        print(entries)  # get number of xrefItems
        xrefLength = int(entries)
        xRefTable = self.file.readlines(xrefLength*20 - 1)
        self.xRef = XRefTable(xrefAddress, xRefTable)

    def seek_object(self, number: int) -> None:
        address = self.xRef.table[number].address
        self.file.seek(address, io.SEEK_SET)



    @classmethod
    def parse_entry(cls, entry: bytes) -> tuple:
        if (type(entry) == bytes):
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
    pdf = PDFParser("test_pdfs/ex01.pdf")
    print(pdf)
    # pdf.seek_object(53)
    pdf.file.seek(139448)
    print(pdf.file.readline())
    print(pdf.file.readline())
    print(pdf.file.readline())
    print(pdf.file.readline())
    print(pdf.file.readline())
    print(pdf.file.readline())
    print(pdf.file.readline())
    print(pdf.file.readline())
    print(pdf.file.readline())



    # stream = re.compile(b'stream(.*?)endstream', re.S)
    st = pdf.file.read(2786)
    s = st.strip(b'\r\n')
    try:
        print(zlib.decompress(s).decode('UTF-8'))
        print("")
    except:
        pass
    pdf.close()
