from PDFObjectsParser import classify_steam
from PDFStructureObjects import *
import zlib
import re
from io import BytesIO

from utils import ObjectIter


class PDFObjectStreamParser:

    def __init__(self, object_stream:PDFStream):
        if object_stream[b"/Type"] != b"/ObjStm":
            raise AssertionError("object_stream type has to be ObjStm")
        self.stream = BytesIO(object_stream.read_stream())
        self.number_of_objects = int(object_stream[b"/N"])
        self.stream_offset = int(object_stream[b"/First"])
        if b"/Filter" in object_stream:
            if object_stream[b"/Filter"] != b"/FlateDecode":
                raise AssertionError("Only FlateDecode is supported")
            self.stream = BytesIO(zlib.decompress(self.stream.read()))

    def extract(self):
        num_size = self._extractObjectNSize()
        return self._extract_objects(num_size)

    def _extractObjectNSize(self):
        num_offset_pair_stream = self.stream.read(self.stream_offset)
        num_offset_pairs = re.findall(br"(\d+) (\d+)", num_offset_pair_stream)
        if len(num_offset_pairs) != self.number_of_objects:
            raise AssertionError(f"Expected {self.number_of_objects} but got {len(num_offset_pairs)}")
        num_size = []
        num_offset_pairs = [(int(item[0]),int(item[1])) for item in num_offset_pairs]
        for object_1, object_2 in zip(num_offset_pairs[:-1], num_offset_pairs[1:]):
            number_size = (object_1[0], object_2[1] - object_1[1])
            num_size.append(number_size)

        last_object = (num_offset_pairs[-1][0], \
                       self.stream.getbuffer().nbytes - self.stream_offset - num_offset_pairs[-1][1])
        num_size.append(last_object)
        return num_size

    def _extract_objects(self, obj_num_size: list):
        self.stream.seek(self.stream_offset)
        objects = {}
        for num, size in obj_num_size:
            object_stream = self.stream.read(size)
            parsed_object = classify_steam(ObjectIter(object_stream))
            item = PDFObject(parsed_object, num, 0, "n")
            objects[num] = item

        return objects
