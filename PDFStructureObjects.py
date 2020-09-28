from dataclasses import dataclass
import io





@dataclass
class PDFStream:
    def __init__(self,stream_dict:dict,startAdress):
        self.stream_dict = stream_dict
        self.startAddress = startAdress
        self.length = stream_dict["/Length"]

    def read_stream(self,file:io.BytesIO):
        pass


    def __str__(self):
        return
