#pragma once
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "FrameBuffer.h"

namespace py = pybind11;

// Declare helper function
void set_array(FrameBuffer& fb, py::array_t<unsigned char> np_array);
