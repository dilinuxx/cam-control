# cython: boundscheck=False, wraparound=False, nonecheck=False

from libc.math cimport exp
import numpy as np
#cimport numpy as np

cpdef img_thermal(unsigned short[:, :] img_in, float[:, :] img_out, float[:] temp_scale):

    cdef int rows = img_in.shape[0]
    cdef int cols = img_in.shape[1]

    cdef int i, j

    for i in range(rows):
        for j in range(cols):
            img_out[i, j] = temp_scale[img_in[i, j]]
    
    return img_out

cpdef img_colormap(unsigned short[:, :] img_in, char[:, :, :] img_out, char[:, :] color_scale):

    cdef int rows = img_in.shape[0]
    cdef int cols = img_in.shape[1]

    cdef int i, j

    for i in range(rows):
        for j in range(cols):
            img_out[i,j,0] = color_scale[img_in[i, j]][0]
            img_out[i,j,1] = color_scale[img_in[i, j]][1]
            img_out[i,j,2] = color_scale[img_in[i, j]][2]

    return img_out

cpdef img_iter2(unsigned short[:, :] img_in, float[:, :] img_out, float[:] temp_scale):

    cdef int rows = img_in.shape[0]
    cdef int cols = img_in.shape[1]

    cdef int i, j
    
    for i in range(rows):
        for j in range(cols):
            img_out[i, j] = temp_scale[img_in[i, j]]

    return img_out

