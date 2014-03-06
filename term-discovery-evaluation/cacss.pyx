import numpy as np
cimport numpy as np
cimport cython
ITYPE = np.int
ctypedef np.int_t ITYPE_t


def allcommonsubstrings(np.ndarray[ITYPE_t, ndim=1] XA,
                        np.ndarray[ITYPE_t, ndim=1] XB,
                        int minlength):
    cdef unsigned int mA, mB, i, j, mT
    mA = XA.shape[0]
    mB = XB.shape[0]
    # cdef ITYPE_t[:,:] m
    m = np.zeros((mA+1, mB+1), dtype=ITYPE)

    for i in xrange(1, mA+1):
        for j in xrange(1, mB+1):
            if XA[i-1] == XB[j-1]:
                m[i, j] = m[i-1, j-1] + 1
    # collect starter indices in raveled form
    # tmp = np.argsort(m,axis=None)
    # tmp = tmp[np.where(np.ravel(m)[tmp]>=minlength)]
    # mT = tmp.shape[0]
    # starters = np.empty((mT,), dtype=ITYPE)
    # for i in xrange(mT):
    #     starters[i] = tmp[mT-i-1]

    starters = sorted(zip(*np.nonzero(m >= minlength)),
                      key=lambda x: m[x],
                      reverse=True)
    if len(starters) == 0:
        return []
    alignments = []
    while True:
        s = starters[0]
        alignment = XA[s[0] - m[s]: s[0]]
        align_ids = [(s[0] - m[s] + n, s[1] - m[s] + n)
                     for n in xrange(1, m[s]+1)]
        _align_ids = zip(*align_ids)
        for start in xrange(len(alignment)):
            for end in xrange(start + minlength, len(alignment)+1):
                alignments.append((alignment[start:end],
                                   (_align_ids[0][start:end],
                                    _align_ids[1][start:end])))
        starters = [x for x in starters if x not in align_ids]
        if len(starters) == 0:
            break
    return alignments


# @cython.boundscheck(True)
# def allcommonsubstrings_old(np.ndarray[ITYPE_t, ndim=1] XA,
#                         np.ndarray[ITYPE_t, ndim=1] XB,
#                         int minlength):
#     """Find all common substrings between s1 and s2.

#     Arguments:
#     :param s1: iterable
#     :param s2: iterable
#     :param minlength: minimum length of return substrings [default=2]

#     Returns list of (substring, (indices in s1, indices in s2))
#     """
#     cdef unsigned int mA, mB, i, j, start, end, idxA, idxB, score
#     mA = XA.shape[0]
#     mB = XB.shape[0]
#     cdef ITYPE_t[:,:] m
#     cdef ITYPE_t[:] starters
#     # cdef ITYPE_t[:] tmp
#     cdef ITYPE_t[:] alignment
#     cdef ITYPE_t[:,:] align_idx

#     m = np.zeros([mA+1, mB+1], dtype=ITYPE)
#     # for i in xrange(mA+1):
#     #     m[i, 0] = 0
#     # for j in xrange(mB+1):
#     #     m[0, j] = 0
#     for i in xrange(1, mA+1):
#         for j in xrange(1, mB+1):
#             if XA[i-1] == XB[j-1]:
#                 m[i, j] = m[i-1, j-1] + 1
#     # for i in xrange(mA+1):
#     #     for j in xrange(mB+1):
#     #         print m[i,j], ' ',
#     #     print

#     # collect starter indices in raveled form
#     tmp = np.argsort(m,axis=None)
#     tmp = tmp[np.where(np.ravel(m)[tmp]>=minlength)]

#     j = tmp.shape[0]
#     print mA, mB
#     for i in xrange(j):
#         print tmp[i]
#     # reverse the array, since cython can't do negative slicing (as i understand it)
#     starters = np.empty((j,), dtype=ITYPE)
#     for i in xrange(j):
#         starters[i] = tmp[j-i-1]
#     for i in xrange(j):
#         print starters[j]

#     if len(starters) == 0:
#         return []
#     alignments = []
#     i = 0

#     while True:
#         idxA, idxB = np.unravel_index(starters[0], dims=(mA+1, mB+1))
#         score = m[idxA, idxB]

#         alignment = XA[idxA - score: idxA]

#         align_idx = np.empty((score, 2), dtype=ITYPE)
#         for j in xrange(1, score+1):
#             try:
#                 align_idx[j,0] = idxA - score + j
#                 align_idx[j,1] = idxB - score + j
#                 # align_idx[j,:] = np.array([idxA - score + j, idxB - score + j])
#             except TypeError as e:
#                 print j, idxA, idxB, score
#                 raise e
#         for start in xrange(score):
#             for end in xrange(start + minlength, score + 1):
#                 alignments.append((alignment[start:end],
#                                    (align_idx[0, start:end],
#                                     align_idx[1, start:end])))
#         starters = np.fromiter((x for x in starters
#                                 if not x in np.ravel_multi_index(align_idx.T,
#                                                                  dims=(mA+1,mB+1))),
#                                dtype=ITYPE)
#         i += 1
#         if starters.shape[0] == 0:
#             break
#     return alignments
