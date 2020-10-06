import time

from PDFParser import *

class PDFMerger:
    def __init__(self, pdfs):
        self.pdfFiles = pdfs
        self.objectCount = sum(len(pdf) for pdf in pdfs)


    def new_page_root(self):
        self.objectCount += 1
        root_ref = IndirectObjectRef(self.objectCount, 0)
        page_count = 0
        kids = []
        for pdf in self.pdfFiles:
            root = pdf.get_page_root()
            page_count += int(root[b"/Count"])
            kids += root[b"/Kids"].data
            root[b"/Parent"] = root_ref

        rootDict = PDFDict({b"/Type": b"/Pages",
                            b"/Kids": PDFArray(kids),
                            b"/Count": str(page_count).encode("utf-8")})

        self.pdfFiles[0].trailer[b"/Size"] = str(self.objectCount).encode("utf-8")
        self.pdfFiles[0].get_document_catalog()[b"/Pages"] = root_ref

        return PDFObject(rootDict, self.objectCount, 0, "n")

    def merge(self, out_path: str) -> None:
        """
        Merges the accumulated PDFFiles

        :param out_path: Path for the output file
        """
        accumulated_offset = len(self.pdfFiles[0])
        for pdf in self.pdfFiles[1:]:
            pdf.increment_references(accumulated_offset)
            accumulated_offset += len(pdf)

        self.pdfFiles[0].pdfObjects[self.objectCount] = (self.new_page_root())

        newXrefTable = [XrefEntry(0, 65535, "f")]
        with open(out_path, "wb+")as f:
            f.write(b"%PDF-1.5\n")
            for index, pdf in enumerate(self.pdfFiles):
                for object in tqdm(pdf.pdfObjects.values(), f"Writing Objects for {index}. pdf"):
                    pos = str(f.tell())
                    rev = str(object.object_rev)
                    inuse = object.inuse
                    newXrefTable.append(XrefEntry(pos, int(rev), str(inuse)))
                    f.write(bytes(object))
            xrefpos = f.tell()
            newXrefTable = XRefTable(newXrefTable, True)
            f.write(newXrefTable.__str__().encode("utf-8"))
            f.write(b"trailer\n")
            # self.trailer.data.pop("/DocChecksum")
            f.write(bytes(self.pdfFiles[0].trailer))
            f.write(f"startxref\n{xrefpos}\n%%EOF\n".encode("utf-8"))


if __name__ == '__main__':
    start = time.time()
    pdf1 = PDFParser("/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_01_Einführung.pdf")
    pdf2 = PDFParser(
        "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_02_Mathematische_Grundlagen_Anmerkungen.pdf")
    pdf3 = PDFParser(
        "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_03_Formale_Sprachen_und_Grammatiken_Anmerkungen.pdf")
    pdf4 = PDFParser(
        "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_04_Reguläre_Sprachen_Endliche_Automaten_Anmerkungen.pdf")
    # pdf5 = PDFParser("/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_05_Weitere_Charakterisierungen_Regulärer_Sprachen_Anmerkungen.pdf")

    merger = PDFMerger([pdf1, pdf2, pdf3,pdf4])

    merger.merge("BlattMerger.pdf")
    print(time.time() - start)
