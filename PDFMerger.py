from tqdm import tqdm

from PDFObjects import IndirectObjectRef
from PDFParser import PDFParser, XrefEntry, XRefTable


class PDFMerger:
    def __init__(self, pdf1: PDFParser, pdf2: PDFParser):
        self.pdf1 = pdf1
        self.pdf2 = pdf2

    def merge(self, out_path: str) -> None:
        """
        Merges the accumulated PDFFiles
        :param out_path: Path for the output file
        """
        self.pdf2.increment_references(self.pdf1.__len__())
        root1 = self.pdf1.get_page_root()
        root2 = self.pdf2.get_page_root()
        root2[b"/Parent"] = IndirectObjectRef(root1.object_number, root1.object_rev)
        root1[b"/Kids"].data.append(IndirectObjectRef(root2.object_number, root2.object_rev))
        root1[b"/Count"] = str(int(root1[b"/Count"]) + int(root2[b"/Count"])).encode("utf-8")
        self.pdf1.trailer[b"/Size"] = str(len(pdf1) + len(pdf2)).encode("utf-8")
        newXrefTable = [XrefEntry(0, 65535, "f")]
        with open("Merge3.pdf", "wb+")as f:
            f.write(b"%PDF-1.5\n")
            for object in tqdm(self.pdf1.pdfObjects.values(), "Writing Objects"):
                pos = str(f.tell())
                rev = str(object.object_rev)
                inuse = object.inuse
                newXrefTable.append(XrefEntry(pos, int(rev), str(inuse)))
                f.write(object.to_bytes(self.pdf1.file) + b"\n")
            for object in tqdm(self.pdf2.pdfObjects.values(), "Writing Objects"):
                pos = str(f.tell())
                rev = str(object.object_rev)
                inuse = object.inuse
                newXrefTable.append(XrefEntry(pos, int(rev), str(inuse)))
                f.write(object.to_bytes(self.pdf2.file) + b"\n")

            xrefpos = f.tell()
            newXrefTable = XRefTable(newXrefTable, True)
            f.write(newXrefTable.__str__().encode("utf-8"))
            f.write(b"trailer\n")
            # self.trailer.data.pop("/DocChecksum")
            f.write(self.pdf1.trailer.to_bytes())
            f.write(f"startxref\n{xrefpos}\n%%EOF\n".encode("utf-8"))


if __name__ == '__main__':
    pdf1 = PDFParser("test_pdfs/FuldaFinalProjectHighLevelDescriptionWS2020.pdf")
    pdf2 = PDFParser("test_pdfs/FuldaMilestone0WS2020.pdf")
    merger = PDFMerger(pdf2, pdf1)

    merger.merge()
