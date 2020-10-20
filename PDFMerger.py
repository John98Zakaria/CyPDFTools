import time
from concurrent import futures
from multiprocessing import cpu_count
from PDFObjects import *
from PDFStructureObjects import *
from PDFFile import PDFFile


class PDFMerger:
    def __init__(self, pdfs):
        self.pdfFiles: list[PDFFile] = pdfs
        self.process_pdfs((pdf for pdf in pdfs if type(pdf) != PDFFile))
        self.objectCount = sum(len(pdf) for pdf in self.pdfFiles)

    def process_pdfs(self, pdfs):
        finished_pdfs = []
        with futures.ProcessPoolExecutor(cpu_count() // 2) as pool:
            tasks = [pool.submit(PDFFile, pdf, True) for pdf in pdfs]
            for task in futures.as_completed(tasks):
                finished_pdfs.append(task.result())

        for pdf in finished_pdfs:
            pdf.reload_file()

        self.pdfFiles = finished_pdfs

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
        self.merge_outline()
        return PDFObject(rootDict, self.objectCount, 0, "n")

    def merge_outline(self):
        """
        Merges the pdf outline

        """
        pdfs_with_outline = [pdf for pdf in self.pdfFiles if pdf.has_outline()]
        if not pdfs_with_outline:
            return

        root_pdf = pdfs_with_outline[0]
        root_outline = root_pdf.get_outline()
        root_outlineRef = IndirectObjectRef(root_outline.object_number,root_outline.object_rev)
        self.pdfFiles[0].get_document_catalog()[b"/Outlines"] = root_outlineRef

        if len(pdfs_with_outline) == 1:
            return

        for pdf1, pdf2 in zip(self.pdfFiles[:-1], self.pdfFiles[1:]):
            outline1, outline2 = pdf1.get_lastOutlineItem(),pdf2.get_firstOutlineItem()
            outline1[b"/Parent"] = root_outlineRef
            outline1[b"/Next"] = outline2.get_address()
            outline2[b"/Prev"] = outline1.get_address()

        root_outline[b"/Last"] = pdfs_with_outline[-1].get_firstOutlineItem().get_address()

        return

    def merge(self, out_path: str) -> None:
        """
        Merges the accumulated PDFFiles

        :param out_path: Path for the output file
        """
        accumulated_offset = len(self.pdfFiles[0])
        for pdf in self.pdfFiles[1:]:
            pdf.increment_references(accumulated_offset)
            accumulated_offset += len(pdf)

        self.pdfFiles[0].pdfObjects[self.objectCount] = self.new_page_root()

        newXrefTable = [XrefEntry(0, 65535, "f")]
        with open(out_path, "wb+")as f:
            f.write(b"%PDF-1.7\n")
            for index, pdf in enumerate(self.pdfFiles, 1):
                for object in tqdm(pdf.pdfObjects.values(), f"Writing Objects for {index}. pdf"):
                    pos = f.tell()
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
    # pdf1 = PDFParser("/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_01_Einführung.pdf")
    # pdf2 = PDFParser(
    #     "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_02_Mathematische_Grundlagen_Anmerkungen.pdf")
    # pdf3 = PDFParser(
    #     "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_03_Formale_Sprachen_und_Grammatiken_Anmerkungen.pdf")
    # pdf4 = PDFParser(
    #     "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_04_Reguläre_Sprachen_Endliche_Automaten_Anmerkungen.pdf")
    # pdf5 = PDFParser(
    #     "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_05_Weitere_Charakterisierungen_Regulärer_Sprachen_Anmerkungen.pdf")
    # merger = PDFMerger([pdf1, pdf2, pdf3, pdf4, pdf5])
    # merger = PDFMerger(["/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_01_Einführung.pdf",
    #                     "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_02_Mathematische_Grundlagen_Anmerkungen.pdf",
    #                     "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_03_Formale_Sprachen_und_Grammatiken_Anmerkungen.pdf",
    #                     "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_04_Reguläre_Sprachen_Endliche_Automaten_Anmerkungen.pdf",
    #                     "/media/jn98zk/318476C83114A23B/Uni-Mainz/FormaleSprachen/FSB_05_Weitere_Charakterisierungen_Regulärer_Sprachen_Anmerkungen.pdf"
    #                     ])
    # huff1 = PDFParser("/home/jn98zk/Projects/CyPDFTools/test_pdfs/9783446457942.002.pdf")
    # huff2 = PDFParser("/home/jn98zk/Projects/CyPDFTools/test_pdfs/9783446457942.003.pdf")
    # merger = PDFMerger([huff1,huff2])
    merger = PDFMerger(["/home/jn98zk/Projects/CyPDFTools/test_pdfs/9783446457942.002.pdf",
                        "/home/jn98zk/Projects/CyPDFTools/test_pdfs/9783446457942.003.pdf",
                        "/home/jn98zk/Projects/CyPDFTools/test_pdfs/9783446457942.004.pdf",
                        "/home/jn98zk/Projects/CyPDFTools/test_pdfs/9783446457942.005.pdf",
                        ])
    #
    merger.merge("BlattMerger_Normal.pdf")
    print(time.time() - start)
