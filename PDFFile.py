import zlib
from collections import defaultdict
from io import BytesIO, SEEK_CUR, SEEK_SET, SEEK_END

from PDFObjectStreamParser import PDFObjectStreamParser
from PDFObjects import PDFArray
from PDFObjectsParser import classify_steam
from PDFStructureObjects import *
from png_algorithm import png_algorithmPipeline
from utils import ObjectIter


class PDFFile:
    """
    Loads the PDFFile to modify it
    """

    def __init__(self, filePath, to_pickle=False):
        self.file = open(filePath, "rb")
        self.filePath = filePath
        self.trailer_end = 0
        self.trailerStart = 0
        self.skippedFree = 0
        self.offset = 0
        self.pdfObjects = {}
        self.trailer = []
        self.compressed_objects = {}
        self.xRef = XRefTable([], True)
        self._xRefExtractor(self._extractXrefAddress())
        self.trailer = self._trailer_parser()
        self.pdfObjects = self._read_all_objects()
        self._unpack_compressed_objects()
        self.pages = []
        if to_pickle:
            self.file.close()
            self.file = BytesIO(b"")
            for item in filter(lambda x: type(x) == PDFStream, self.pdfObjects.values()):
                item.file = BytesIO(b"")

    def reload_file(self):
        self.file = open(self.filePath, "rb")
        for item in filter(lambda x: type(x) == PDFStream, self.pdfObjects.values()):
            item.file = self.file

    def _extractXrefAddress(self):
        self.file.seek(-3, SEEK_END)
        letter = self.file.read(1)
        while not letter.isdigit():  # Looking for the first number in
            self.file.seek(-2, SEEK_CUR)
            letter = self.file.read(1)

        xrefAddress = b""
        while True:
            if not letter.isdigit():
                break
            xrefAddress += letter
            self.file.seek(-2, SEEK_CUR)
            letter = self.file.read(1)

        self.trailer_end = self.file.tell()
        xrefAddress = int(xrefAddress[::-1])
        return xrefAddress

    def _xRefExtractor(self, xrefAddress) -> None:
        """
        Extracts XRef Table from the pdf

        :param xrefAddress: address of the XRefTable
        """
        len_re = re.compile(br"(\d+) (\d+)")
        self.file.seek(xrefAddress, SEEK_SET)  # Seek to x_ref_table
        xref_type = self.file.read(1)
        if xref_type == b"x":  # Xref is explicitly written in file
            line = self.file.readline()
            entries = len_re.search(self.file.readline())  # get number of xrefItems
            x_ref_table = []
            xrefLength = int(entries.group(2))
            while entries and xrefLength:
                xrefLength = int(entries.group(2))
                x_ref_table += self.file.readlines(xrefLength * 20 - 1)
                entries = len_re.search(self.file.readline())  # get number of xrefItems

            self.xRef = self.xRef + XRefTable(x_ref_table)
            self.trailerStart = self.file.tell()
        elif xref_type.isdigit():  # Xref is stored in a stream PDF1.5+
            self.file.seek(-1, SEEK_CUR)  # unconsume the letter that was just read
            self.xRef.table.append(XrefEntry(xrefAddress, 0, "n"))
            XRefDict = self.extract_object(0)  # Xref address is the first object
            # in the table (Optimisation is the root of all evil branchless programming)
            self.xRef.table.pop(0)  # delete XrefObject
            if XRefDict[b"/Type"] != b"/XRef":
                raise AssertionError("XRef dict has to have XRef as type")

            trailer_stream = XRefDict.read_stream()

            if b"/Filter" in XRefDict:
                if XRefDict[b"/Filter"] == b"/FlateDecode":
                    trailer_stream = zlib.decompress(trailer_stream)

                else:
                    raise AssertionError("Only FlateDecode is supported")

            W = XRefDict[b"/W"]
            W = [int(i) for i in W.data]  # Convert W array to int array to be used
            if b"/DecodeParms" in XRefDict:  # Table was compressed using a png compression algorithm
                number_of_columns = int(XRefDict[b"/DecodeParms"][b"/Columns"])
                predictor = int(XRefDict[b"/DecodeParms"][b"/Predictor"])
                if predictor >= 10:
                    trailer_stream = png_algorithmPipeline(trailer_stream, number_of_columns, predictor)

            trailer_stream = BytesIO(trailer_stream)
            ExtractedXRef = XRefTable([], True)
            size = trailer_stream.getbuffer().nbytes
            compressed_objects = defaultdict(list)
            while trailer_stream.tell() != size:
                field_1 = int.from_bytes(trailer_stream.read(W[0]), "big")
                field_2 = int.from_bytes(trailer_stream.read(W[1]), "big")
                field_3 = int.from_bytes(trailer_stream.read(W[2]), "big")
                if field_1 == 0:
                    ExtractedXRef.table.append(XrefEntry(field_2, field_3, "f"))
                if field_1 == 1:
                    ExtractedXRef.table.append(XrefEntry(field_2, field_3, "n"))
                if field_1 == 2:
                    compressed_objects[field_2].append(field_3)

            trailer = {b"/Size": str(len(ExtractedXRef)+compressed_objects.__len__()).encode("utf-8"),
                       b"/Root": XRefDict[b"/Root"]}
            self.trailer = PDFDict(trailer)

            if b"/Prev" in XRefDict:
                xref_address = int(XRefDict[b"/Prev"])
                self._xRefExtractor(xref_address)

            self.xRef = ExtractedXRef + self.xRef
            self.compressed_objects.update(compressed_objects)

    def _unpack_compressed_objects(self):
        """
        Extracts all pdf objects from all object streams found in the XRefTable

        """
        for key in self.compressed_objects:
            object_stream = self.pdfObjects[key]
            new_items = PDFObjectStreamParser(object_stream).extract()
            self.pdfObjects.update(new_items)
        self.trailer[b"/Size"] = bytes(str(len(self.pdfObjects.keys())), "utf-8")

    def _trailer_parser(self):
        """
        Parses trailer if necessary

        :return: PDF Trailer
        """
        if self.trailer:  # Trailer was parsed somewhere already
            return self.trailer
        self.trailerStart = self.file.tell()
        content = self.file.read(self.trailer_end - 10 - self.trailerStart)
        object_parser = ObjectIter(content)
        object_parser.move_to(b"<")
        trailer_dict = classify_steam(object_parser)
        if b"/Prev" in trailer_dict:
            prevXref = int(trailer_dict[b"/Prev"])
            print("Recursive")
            trailer_dict.data.pop(b"/Prev")  # Cleanup
            self._xRefExtractor(prevXref)
            self._trailer_parser()  # recursively parse the other trailer to update xref
            # trailer_dict = other_dict.update(trailer_dict)

        return trailer_dict

    def seek_object(self, number: int) -> None:
        """
        Moves the pointer to the nth object

        :param number: Object's index in XRefTable
        """
        address = self.xRef.table[number].address
        self.file.seek(address, SEEK_SET)
        self._findObjectStart()  # Some objects don't start exactly at the given address

    def _findObjectStart(self) -> None:
        """
        Moves the pointer to the start of the object number

        """
        currentChar = self.file.read(1)
        if currentChar == b"":
            raise Exception("NullObject")
        if currentChar.isdigit():
            self.file.seek(-2, SEEK_CUR)
        else:
            while not currentChar.isdigit():
                currentChar = self.file.read(1)
            self.file.seek(-1, SEEK_CUR)

    def extract_object(self, number):
        """
        Extracts object from the pdf file

        :param number: XrefIndex of object
        :return: PDF Object
        """
        inuse = self.xRef.table[number].in_use_entry
        if inuse == "f":
            self.skippedFree += 1
            raise AssertionError("Skipping free object Reference")
        self.seek_object(number)
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
        self.file.seek(-1, SEEK_CUR)
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
        """
        Get object from pdf

        :param key: object number
        :return: PDFObject
        """
        return self.pdfObjects[key - self.offset]

    def removeFromPDFDict(self, key: int):
        """
        Removes object from pdf

        :param key: object number
        """
        self.pdfObjects.pop(key - self.offset)

    def get_document_catalog(self):
        """
        Gets the document_catalog from the pdf

        :return: Document catalog
        """
        document_catalog_address = self.trailer[b"/Root"].objectref - self.offset
        return self.pdfObjects[document_catalog_address]

    def has_outline(self):
        """
        Checks if the document has an outline

        """
        return b"/Outlines" in self.get_document_catalog()

    def get_RootOutline(self) -> PDFObject:
        """
        Gets the root outline object

        :return: Outline PDFObject
        """
        outline_address = self.get_document_catalog()[b"/Outlines"]
        return self.getFromPDFDict(outline_address.objectref)

    def get_firstOutlineItem(self) -> PDFObject:
        """
        Get the first actual OutlineItem

        :return: First actual OutlineItem
        """
        first_outline_address = self.get_RootOutline()[b"/First"]
        first_outline = self.getFromPDFDict(first_outline_address.objectref)
        return first_outline

    def get_lastOutlineItem(self) -> PDFObject:
        """
        Get the last actual OutlineItem

        :return: Last actual OutlineItem
        """
        last_outline_address = self.get_RootOutline()[b"/Last"]
        last_outline = self.getFromPDFDict(last_outline_address.objectref)
        return last_outline

    def get_pages(self) -> list:
        """
        Gathers all pages

        :return: list of pages
        """
        if self.pages:
            return self.pages

        def getChildrenPages(pages: PDFArray):
            pages_arr = []
            for page_ref in pages.data:
                page = self.pdfObjects[page_ref.objectref]
                if page[b"/Type"] == b"/Pages":
                    pages_arr += getChildrenPages(page[b"/Kids"])
                else:
                    pages_arr.append(page_ref)
            return pages_arr

        page_root = self.get_page_root()
        return getChildrenPages(page_root[b"/Kids"])

    def rotate_page(self, index: int, rotation: int):
        """
        Rotates the given page

        :param index: Page index
        :param rotation: Degrees

        """
        page = pdf.getFromPDFDict(self.get_pages()[index - 1].objectref)
        if b"/Rotate" in page:
            page[b"/Rotate"] = str(int(page[b"/Rotate"]) + rotation).encode("utf-8")
        else:
            page[b"/Rotate"] = str(rotation).encode("utf-8")

    def rotate_all(self, rotation: int):
        """
        Rotates all pages

        :param rotation: Degrees
        """
        pages = self.get_pages()
        for index, _ in enumerate(pages, 1):
            self.rotate_page(index, rotation)

    def get_page_root(self):
        """
        Extracts the page root from the pdf

        :return: PDF Root
        """
        page_root_address = self.get_document_catalog()[b"/Pages"].objectref - self.offset
        page_root = self.pdfObjects[page_root_address]
        return page_root

    def close(self):
        self.file.close()

    def __str__(self):
        return f"FilePath : {self.filePath}\n" \
               f"PDFObjects :{self.pdfObjects}"

    def __len__(self):
        return len(self.pdfObjects.keys())

    def __repr__(self):
        return self.__str__()

    def save(self, path):
        """
        Writes the contents of the pdf to disk

        """
        newXrefTable = [XrefEntry(0, 65535, "f")]
        with open(path, "wb+")as f:
            f.write(b"%PDF-1.7\n")
            for pdfobject in tqdm(self.pdfObjects.values(), "Writing Objects"):
                pos = f.tell()
                rev = str(pdfobject.object_rev)
                inuse = pdfobject.inuse
                newXrefTable.append(XrefEntry(pos, int(rev), str(inuse)))
                f.write(bytes(pdfobject) + b"\n")
            xrefpos = f.tell()
            newXrefTable = XRefTable(newXrefTable, True)
            f.write(bytes(newXrefTable))
            f.write(b"trailer\n")
            # self.trailer.data.pop("/DocChecksum")
            f.write(bytes(self.trailer))
            f.write(f"startxref\n{xrefpos}\n%%EOF\n".encode("utf-8"))

    def _read_all_objects(self):
        object_store = {}

        for objectIndex in tqdm(range(0, self.xRef.__len__()), "Reading Objects"):
            try:
                item = self.extract_object(objectIndex)
                object_number = item.object_number
                object_store[object_number] = item
            except Exception as e:
                print(f"{objectIndex} has {e}")

        return object_store

    def increment_references(self, n: int) -> None:
        """
        Increments all Indirect Object references of the pdf

        :param n: offset
        """
        for pdfobject in tqdm(self.pdfObjects.values(), "Incrementing References"):
            pdfobject.offset_references(n)
        self.trailer.offset_references(n)
        self.offset += n


if __name__ == '__main__':
    pdf = PDFFile("/media/jn98zk/318476C83114A23B/Uni-Mainz/Statistik/Stochastik für Einsteiger Eine Einführung in die faszinierende Welt des Zufalls. Mit über 220 Übungsaufgaben und Lösungen, 8. Auflage by Norbert Henze (z-lib.org).pdf")
    pdf.get_pages()
    pdf.save("DigitalDesign.pdf")
    # pdf.has_outline()
    # pdf.increment_references(10)
    # pdf.save("out.pdf")
    # for i in indices:
    #     print(pdf.getFromPDFDict(i.objectref))

    pdf.close()
