from os import listdir
from os.path import isfile, join

from PDFFile import PDFFile


def test_parsing():
    path = "../test_pdfs"
    onlyfiles = [f for f in listdir("../test_pdfs") if isfile(join(path, f))]
    for file in onlyfiles:
        pdf = PDFFile(join(path, file))
        pdf.save(join("../test_pdfs/clones",file))
        pdf.close()

