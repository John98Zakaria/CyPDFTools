import io
from collections import namedtuple


class PDFFile:
    def __init__(self, filePath):
        self.file = open(filePath, "rb+")
        self.filePath = filePath
        self.xrefTableAddress = None
        self._xRefLength = 0
        self._xRefTable = []
        self._initXrefTable()

    def _initXrefTable(self):
        self.file.seek(-5, io.SEEK_END)
        count = 0;
        while count != 2:
            self.file.seek(-2, io.SEEK_CUR)
            char = self.file.read(1).decode("utf-8")
            count += char == "\n"
        self.xrefTableAddress = int(self.file.readline()[:-1])
        self.file.seek(self.xrefTableAddress, io.SEEK_SET)  # Seek to xRefTable
        self.file.readline()
        entries = self.file.readline().decode("UTF-8").split(" ")[1]  # get number of xrefItems
        print(entries)  # get number of xrefItems
        self._xRefLength = int(entries)
        self._readXrefTable()

    def seek_object(self, number: int) -> None:
        address = self._xRefTable[number].address
        self.file.seek(address, io.SEEK_SET)

    def _readXrefTable(self):
        table_entries = self.file.readlines(self._xRefLength * 20 - 1)

        self._xRefTable = list(map(self.parse_entry, table_entries))

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
               f"xRefAddress : {self.xrefTableAddress} \n" \
               f"xRefLength  : {self._xRefLength}"

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    pdf = PDFFile("Blatt03.pdf")
    print(pdf)
    table = pdf._xRefTable

    pdf.seek_object(3)
    print(pdf.file.readlines(50))
    pdf.close()
