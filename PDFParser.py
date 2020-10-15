import io
from PDFObjectsParser import classify_steam, PDFArray
from PDFStructureObjects import *
from utils import ObjectIter
import zlib


class PDFParser:
    def __init__(self, filePath):
        self.file = open(filePath, "rb")
        self.filePath = filePath
        self.trailer_end = 0
        self.trailerStart = 0
        self.skippedFree = 0
        self.offset = 0
        self.xRefAddress = self._extractXrefAddress()
        self.compressed_objects = []
        self.xRef = XRefTable([], True)
        self.xRefExtractor(self.xRefAddress)
        # self.trailer = self.trailer_parser()
        self.pdfObjects = self.read_all_objects()

    def _extractXrefAddress(self):
        self.file.seek(-3, io.SEEK_END)
        letter = self.file.read(1)
        while not letter.isdigit():  # Looking for the first number in
            self.file.seek(-2, io.SEEK_CUR)
            letter = self.file.read(1)

        xrefAddress = b""
        while True:
            if not letter.isdigit():
                break
            xrefAddress += letter
            self.file.seek(-2, io.SEEK_CUR)
            letter = self.file.read(1)

        self.trailer_end = self.file.tell()
        xrefAddress = int(xrefAddress[::-1])
        return xrefAddress

    def xRefExtractor(self, xrefAddress):
        len_re = re.compile(br"(\d+) (\d+)")
        self.file.seek(xrefAddress, io.SEEK_SET)  # Seek to x_ref_table
        xref_type = self.file.read(1)
        if xref_type == b"x":  # Xref is explicitly written in file
            self.file.readline()
            entries = len_re.search(self.file.readline())  # get number of xrefItems
            x_ref_table = []
            while entries:
                xrefLength = int(entries.group(2))
                x_ref_table += self.file.readlines(xrefLength * 20 - 1)
                entries = len_re.search(self.file.readline())  # get number of xrefItems

            self.xRef + XRefTable(x_ref_table)
            self.trailerStart = self.file.tell()
        if xref_type.isdigit():  # Xref is stored in a stream PDF1.5+
            self.file.seek(-1, io.SEEK_CUR)  # unconsume the letter that was just read
            self.xRef.table.append(XrefEntry(self.xRefAddress, 0, "n"))
            XRefDict = self.extract_object(0)  # Xref address is the first object
            # in the table (Optimisation is the root of all evil branchless programming)
            self.xRef.table.pop(0)  # delete XrefObject
            if XRefDict[b"/Type"] != b"/XRef":
                raise AssertionError("XRef dict has to have XRef as type")
            if XRefDict[b"/Filter"] != b"/FlateDecode":
                raise AssertionError("Only FlateDecode is supported")
            W = XRefDict[b"/W"]
            W = [int(i) for i in W.data]  # Convert W array to int array to be used
            trailer_stream = XRefDict.read_stream()
            decompressed_trailer = zlib.decompress(trailer_stream)
            decompressed_trailer = io.BytesIO(decompressed_trailer)
            ExtractedXRef = XRefTable([], True)
            decompressed_trailer.seek(0, io.SEEK_END)
            size = decompressed_trailer.tell()
            decompressed_trailer.seek(0)
            compressed_objects = []
            while decompressed_trailer.tell() != size:
                field_1 = int.from_bytes(decompressed_trailer.read(W[0]), "big")
                field_2 = int.from_bytes(decompressed_trailer.read(W[1]), "big")
                field_3 = int.from_bytes(decompressed_trailer.read(W[2]), "big")
                if field_1 == 0:
                    ExtractedXRef.table.append(XrefEntry(field_2, field_3, "f"))
                if field_1 == 1:
                    ExtractedXRef.table.append(XrefEntry(field_2, field_3, "n"))
                if field_1 == 2:
                    compressed_objects.append((field_2, field_3))

            self.xRef+ ExtractedXRef
            self.compressed_objects = compressed_objects
            # TODO Trailer Extraction from dict


    def trailer_parser(self):
        self.trailerStart = self.file.tell()
        content = self.file.read(self.trailer_end - 10 - self.trailerStart)
        trailer_dict = classify_steam(ObjectIter(content))
        if b"/Prev" in trailer_dict:
            prevXref = int(trailer_dict[b"/Prev"])
            self.xRefExtractor(prevXref)
            self.trailer_parser()

        return trailer_dict

    def seek_object(self, number: int) -> int:
        address = self.xRef.table[number].address
        self.file.seek(address, io.SEEK_SET)
        self._findObjectStart()
        return address

    def _findObjectStart(self) -> None:
        """
        Moves the pointer to the start of the object number
        """
        currentChar = self.file.read(1)
        if currentChar.isdigit():
            self.file.seek(-2, io.SEEK_CUR)
            return
        else:
            while not currentChar.isdigit():
                currentChar = self.file.read(1)
            self.file.seek(-1, io.SEEK_CUR)

    def extract_object(self, number):
        self.seek_object(number)
        inuse = self.xRef.table[number].in_use_entry
        if inuse == "f":
            self.skippedFree += 1
            raise AssertionError("Skipping free object Reference")
        inuse = "n"
        current_char = self.file.read(1)
        object_number = current_char
        while current_char != bytes("j", "utf-8"):
            current_char = self.file.read(1)
            object_number += current_char
        numRev = re.search(br"(\d+) (\d+)", object_number)
        num, rev = numRev.group(1).decode("utf-8"), numRev.group(2).decode("utf-8")
        current_char = self.file.read(1)
        while current_char.isspace():
            current_char = self.file.read(1)
        self.file.seek(-1, io.SEEK_CUR)
        current_line = self.file.readline()
        object_stream = b""
        while True:
            if bytes("endobj", "utf-8") in current_line or bytes("stream\n", "utf-8") in current_line \
                    or bytes("stream\r", "utf-8") in current_line:
                break
            object_stream += current_line
            current_line = self.file.readline()

        is_obj = current_line.find(bytes("endobj", "utf-8"))
        endIndex = is_obj if is_obj + 1 \
            else current_line.find(bytes("stream", "utf-8"))
        object_stream += current_line[:endIndex]
        thing = classify_steam(ObjectIter(object_stream))
        if not (is_obj + 1):
            ob = PDFStream(thing, num, rev, self.file.tell(), inuse, self.file, self.getFromPDFDict)
            return ob

        return PDFObject(thing, num, rev, inuse)

    def getFromPDFDict(self, key: int):
        return self.pdfObjects[key - self.offset]

    def get_document_catalog(self):
        document_catalog_address = self.trailer[b"/Root"].objectref - self.offset
        return self.pdfObjects[document_catalog_address]

    def get_pages(self):
        def getChildrenPages(pages: PDFArray):
            pages_arr = []
            for page_ref in pages.data:
                page = self.pdfObjects[page_ref.objectref]
                if page[b"/Type"] == b"/Pages":
                    pages_arr += getChildrenPages(page[b"/Kids"])
                else:
                    pages_arr.append(page_ref)
            return pages_arr

        pageroot = self.get_page_root()
        return getChildrenPages(pageroot[b"/Kids"])

    def get_page_root(self):
        page_root_address = self.get_document_catalog()[b"/Pages"].objectref - self.offset
        page_root = self.pdfObjects[page_root_address]
        return page_root

    def close(self):
        self.file.close()

    def __str__(self):
        return f"FilePath : {self.filePath}\n" \
               f"{self.xRef}"

    def __len__(self):
        return len(self.xRef)

    def __repr__(self):
        return self.__str__()

    def clone(self):
        newXrefTable = [XrefEntry(0, 65535, "f")]
        with open("out.pdf", "wb+")as f:
            f.write(b"%PDF-1.5\n")
            for pdfobject in tqdm(self.pdfObjects.values(), "Writing Objects"):
                pos = str(f.tell())
                rev = str(pdfobject.object_rev)
                inuse = pdfobject.inuse
                newXrefTable.append(XrefEntry(pos, int(rev), str(inuse)))
                f.write(bytes(pdfobject) + b"\n")
            xrefpos = f.tell()
            newXrefTable = XRefTable(newXrefTable, True)
            f.write(newXrefTable.__str__().encode("utf-8"))
            f.write(b"trailer\n")
            # self.trailer.data.pop("/DocChecksum")
            f.write(bytes(self.trailer))
            f.write(f"startxref\n{xrefpos}\n%%EOF\n".encode("utf-8"))

    def read_all_objects(self):
        object_store = {}

        for objectIndex in tqdm(range(1, self.xRef.__len__()), "Reading Objects"):
            try:
                item = self.extract_object(objectIndex)
                object_number = item.object_number
                object_store[object_number] = item
            except Exception as e:
                print(f"{objectIndex} has {e}")

        return object_store

    def increment_references(self, n: int):
        for pdfobject in tqdm(self.pdfObjects.values(), "Incrementing References"):
            pdfobject.offset_references(n)
        self.trailer.offset_references(n)
        self.offset += n


if __name__ == '__main__':
    pdf = PDFParser("test_pdfs/uebungsblatt1.pdf")
    Object_stream = pdf.pdfObjects[14]
    print(Object_stream)

    # with open("test_pdfs/Python for Data Analysis, 2nd Edition.pdf","rb") as r:
    #     with open("Refrased.pdf","wb+") as w:
    #         file = r.read()
    #         file = file.replace(b"\r",b"\n")
    #         w.write(file)

    # pdf.file = ""
    # with open("SpecificationDump","rb") as f:
    #     # pickle.dump(pdf,f)
    #     pdf:PDFParser = pickle.load(f)
    # pdf.increment_refrences(10)
    # pdf.get_page_root()
    # pdf.file = open("test_pdfs/PDF-Specifications.pdf","rb")
    # pdf.extract_object(2)

    # pdf.clone()

    # pdf.file.seek(2441891)
    # print(pdf.file.readline())
    # print(pdf.file.readline())

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
