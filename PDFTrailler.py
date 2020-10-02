from PDFObjects import *


class PDFTrailer:

    def __init__(self, data, pdf_objects):
        self.size = int(data[b"Size"])
        self.root: IndirectObjectRef = data[b"Root"]
        self.info = data[b"Info"]
        self.pdf_objects = pdf_objects

    def _getobject(self, n: IndirectObjectRef):
        return self.pdf_objects[n.objectref + 1]

    def _resolveRefrences(self):
        self.root = self._getobject(self.root)
        self.info = self._getobject(self.info)


class DocumentCatalogue:
    pass