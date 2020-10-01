from io import BytesIO



cpdef bytes  returnByte():
    cpdef bytes buffer
    b = BytesIO(b"Hellow")
    buffer = b.read(1)
    return buffer

cdef class speedMeUp:
    cdef int a
    cdef int b
    def __init__(self,int a,int b):
        self.a = a
        self.b = b


