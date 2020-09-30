from PDFObjects import IndirectObjectRef
from PDFStructureObjects import *
import re
from objectsParser import parse_stream
from utills import ObjectIter
from tqdm import tqdm


class PDFParser:
    def __init__(self, filePath):
        self.file = open(filePath, "rb")
        self.filePath = filePath
        self.xRef: XRefTable = XRefTable
        self.trailer_end = 0
        self.xRefParser()
        self.trailer = self.trailer_parser()
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
        self.file.seek(self.xRef.address)
        self.file.readlines(len(self.xRef.table) * 20)
        self.file.seek(8, io.SEEK_CUR)
        trailerStart = self.file.tell()
        content = self.file.read(self.trailer_end - 10 - trailerStart)
        trailer_dict = parse_stream(ObjectIter(content))
        return trailer_dict

    def seek_object(self, number: int) -> int:
        address = self.xRef.table[number].address
        self.file.seek(address, io.SEEK_SET)
        return address

    def extract_object(self, number):
        self.seek_object(number)
        inuse = self.xRef.table[number].in_use_entry
        if(inuse=="f"):
            raise AssertionError("Free")
        current_char = self.file.read(1)
        assert (current_char.isdigit())
        object_number = current_char
        while current_char != bytes("j", "utf-8"):
            current_char = self.file.read(1)
            object_number += current_char
        numRev = re.match(br"(\d+) (\d+)", object_number)
        num,rev = numRev.group(1).decode("utf-8"),numRev.group(2).decode("utf-8")
        current_char = self.file.read(1)
        while current_char.isspace():
            current_char = self.file.read(1)
        self.file.seek(-1, io.SEEK_CUR)
        current_line = self.file.readline()
        object_stream = b""
        while True:
            if bytes("endobj", "utf-8") in current_line or bytes("stream", "utf-8") in current_line:
                break
            object_stream += current_line
            current_line = self.file.readline()


        isStream = current_line.find(bytes("stream", "utf-8"))
        endIndex = isStream if isStream+1 \
            else current_line.find(bytes("endobj", "utf-8"))
        object_stream += current_line[:endIndex]
        assert object_stream[-6:] != bytes("endobj", "utf-8")
        assert object_stream[-6:] != bytes("stream", "utf-8")
        thing = parse_stream(ObjectIter(object_stream))
        if isStream+1:
            ob =  (PDFStream(thing,num,rev,self.file.tell(),inuse),num)
            if(type(ob[0].length)==IndirectObjectRef):
                l = self.extract_object(int(ob[0].length))[0].stream_dict
                ob[0].length=int(l)
            return ob

        return (PDFObject(thing,num,rev,self.file.tell(),inuse),num)


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

    def clone(self):
        newXrefTable = ["0 65535 f"]
        with open("out.pdf","wb+")as f:
            f.write(b"%PDF-1.5\n")
            for object in tqdm(self.pdfObjects):
                pos = str(f.tell())
                rev = str(object[0].object_rev)
                inuse = object[0].inuse
                newXrefTable.append(f"{pos} {rev} {inuse}")
                f.write(object[0].to_bytes(pdf.file)+b"\n")
            xrefpos = f.tell()
            newXrefTable = XRefTable(xrefpos,newXrefTable)
            f.write(newXrefTable.__str__().encode("utf-8"))
            f.write(b"trailer\n")
            # self.trailer.data.pop("/DocChecksum")
            f.write(self.trailer.to_bytes())
            f.write(f"startxref\n{xrefpos}\n%%EOF\n".encode("utf-8"))



    def read_all_objects(self):
        objects = []

        for objectIndex in tqdm(range(1, self.xRef.__len__())):
            try:
                objects.append(self.extract_object(objectIndex))
            except  Exception as e:
                print(f"{objectIndex} has {e}" )
                continue

        objects.sort(key=lambda x:int(x[1]))
        return objects




if __name__ == '__main__':


    pdf = PDFParser("test_pdfs/220429a_Fehlerfortpflanzung.pdf")
    # pdf.extract_object(306)
    # pdf.clone()
    # pdf.trailer_parser()
    # pdf = PDFParser("out.pdf")
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
