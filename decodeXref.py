import re
import zlib
import io
from itertools import cycle
import time

pdf = open("test_pdfs/ex01.pdf", "rb").read()
stream = re.compile(b'.*?FlateDecode.*?stream(.*?)endstream', re.S)

for s in re.findall(stream,pdf):
    s = s.strip(b'\r\n')
    try:
        print(zlib.decompress(s).decode('UTF-8'))
        print("")
    except:
        pass

# bt = io.BytesIO(decom)

# W = [1, 3, 1]
# counter = 0
# for size in cycle(W):
#     bts = bt.read(size)
#     print(int.from_bytes(bts, "big"),end=" ")
#     counter+=1
#     if counter == 3:
#         print()
#         counter = 0
#
#     if len(bts) == 0:
#         break
