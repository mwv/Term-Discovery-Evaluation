import numpy as np
cimport numpy as np
cimport cython
ITYPE = np.long
ctypedef np.long_t ITYPE_t

@cython.boundscheck(False)
def allcommonsubstrings(np.ndarray[ITYPE_t, ndim=1] XA,
                        np.ndarray[ITYPE_t, ndim=1] XB,
                        int minlength):
    cdef int mA, mB, i, j, mT, sA, sB, n, score, start, end
    mA = XA.shape[0]
    mB = XB.shape[0]
    cdef ITYPE_t[:] alignment
    cdef ITYPE_t[:,:] align_idx
    # cdef np.ndarray[ITYPE_t, ndim=2] align_idx = np.empty((2,2), dtype=ITYPE)
    cdef ITYPE_t[:] starters
    cdef ITYPE_t[:] chunk
    cdef ITYPE_t[:] idxA
    cdef ITYPE_t[:] idxB

    cdef np.ndarray[ITYPE_t, ndim=2] m = np.zeros((mA+1, mB+1), dtype=ITYPE)
    for i in xrange(1, mA+1):
        for j in xrange(1, mB+1):
            if XA[i-1] == XB[j-1]:
                m[i, j] = m[i-1, j-1] + 1

    # collect starter indices in raveled form
    cdef np.ndarray[ITYPE_t, ndim=1] tmp = np.argsort(m,axis=None)
    tmp = tmp[np.where(np.ravel(m)[tmp]>=minlength)]
    mT = tmp.shape[0]
    starters = np.empty((mT,), dtype=ITYPE)
    for i in xrange(mT):
        starters[i] = tmp[mT-i-1]


    if starters.shape[0] == 0:
        return []
    alignments = []
    while True:
        sA, sB = np.unravel_index(starters[0], dims=(mA+1, mB+1))
        score = m[sA, sB]
        alignment = XA[sA - score: sA]

        align_idx = np.empty((score, 2), dtype=ITYPE)
        for j in xrange(1, score+1):
            align_idx[j-1, 0] = sA - score + j
            align_idx[j-1, 1] = sB - score + j

        for start in xrange(score):
            for end in xrange(start + minlength, score+1):
                chunk = alignment[start:end]
                # idxA = align_idx[[start, end], 0]
                idxA = np.array([align_idx[start, 0], align_idx[end, 0]])
                # idxB = align_idx[[start, end], 0]
                idxB = np.array([align_idx[start, 1], align_idx[end, 1]])
                alignments.append((chunk, idxA, idxB))
                # alignments.append((alignment[start:end],
                #                    (align_idx[start:end, 0],
                #                     align_idx[start:end, 1])))
        starters = np.fromiter((x for x in starters
                                if not x in np.ravel_multi_index(align_idx.T,
                                                                 dims=(mA+1, mB+1))),
                               dtype=ITYPE)
        if starters.shape[0] == 0:
            break
    return alignments
