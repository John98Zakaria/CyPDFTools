from collections import namedtuple


class XRefTable:
    def __init__(self, xref_address: int, xref_table: list):
        self.address = xref_address
        self.table = self.parse_table(xref_table)

    @staticmethod
    def parse_table(table):
        def parse_entry(entry: bytes) -> tuple:
            if (type(entry) == bytes):
                entry = entry.decode("utf-8")
            entry = entry.split(" ")[:3]
            entry[0] = int(entry[0])
            entry[1] = int(entry[1])
            tup = namedtuple("XrefEntry", ["address", "revision", "in_use_entry"])
            return tup(*entry)
        return list(map(parse_entry,table))


    def __len__(self):
        return len(self.table)

    def __str__(self):
        return f"xRefAddress : {self.address} \n" \
               f"xRefLength  : {self.__len__()}"

    def __repr__(self):
        return self.__str__()
