import io
from collections import namedtuple
from XRefTable import *
import zlib
import re
from objectsParser import objectIdentifier
from utills import ObjectIter

class PDFParser:
    def __init__(self, filePath):
        self.file = open(filePath, "rb+")
        self.filePath = filePath
        self.xRef:XRefTable = XRefTable
        self.pdfObjects = []
        self.xRefParser()


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
        print(f"The adress of object {number} is {address}")
        self.file.seek(address, io.SEEK_SET)

    def extractobject(self,number):
        self.seek_object(number)
        currentChar = self.file.read(1)
        assert (currentChar.isdigit())
        while currentChar!=bytes("j","utf-8"):
            currentChar = self.file.read(1)
        currentChar =  self.file.read(1)
        while currentChar.decode("utf-8").isspace():
            currentChar = self.file.read(1)
        self.file.seek(-1,io.SEEK_CUR)
        objectstream = ""
        while ("endobj" or "stream") not in objectstream:
            currentChar = self.file.read(1).decode("utf-8")
            objectstream+=currentChar


        return objectIdentifier(ObjectIter(objectstream))

    def extractObjets(self):
        objects = []
        for objectIndex in range(1,self.xRef.__len__()):
            objects.append(self.extractobject(objectIndex))

        return objects

    @classmethod
    def parse_xRefentry(cls, entry: bytes) -> tuple:
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
    pdf = PDFParser("test_pdfs/Blatt03.pdf")
    print(pdf)

    pdf.seek_object(64)

    print(pdf.file.readline())
    print(pdf.extractobject(2))
    print(pdf.extractObjets())

    # # stream = re.compile(b'stream(.*?)endstream', re.S)
    # st = pdf.file.read(2786)
    # s = st.strip(b'\r\n')
    # try:
    #     print(zlib.decompress(s).decode('UTF-8'))
    #     print("")
    # except:
    #     pass
    # pdf.close()
