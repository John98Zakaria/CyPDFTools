cdef class ObjectIter:
    cdef int length
    cdef dict __dict__
    cpdef bytes prev(self)
    cpdef void move_pointer(self,int n)
    cpdef bytes move_to(self,bytes item)
    cpdef bytes finish_number(self)
    cpdef bytes peek(self,int n=*)
    cpdef bytes reversePeek(self,int n=*)
