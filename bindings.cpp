#include "bindings.h"
#include <stdexcept>
#include <glad/glad.h> // Make sure glad is included for OpenGL functions

void set_array(FrameBuffer& fb, py::array_t<unsigned char> np_array) {
    py::buffer_info info = np_array.request();

    if (info.ndim != 3 || info.shape[2] != 3) {
        throw std::runtime_error("Expected numpy array of shape (height, width, 3) with dtype=uint8");
    }

    size_t height = info.shape[0];
    size_t width  = info.shape[1];

    if (width != fb.width || height != fb.height) {
        throw std::runtime_error("Array dimensions must match framebuffer dimensions");
    }

    if (fb.array.size() != width * height) {
        throw std::runtime_error("fb.array size doesn't match expected framebuffer pixel count");
    }

    auto* ptr = static_cast<unsigned char*>(info.ptr);
    std::memcpy(&fb.array[0], &ptr[0], width*height*3);

    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, fb.texID);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, fb.width, fb.height, 0, GL_RGB, GL_UNSIGNED_BYTE, fb.array.data());
    glGenerateMipmap(GL_TEXTURE_2D);
}

PYBIND11_MODULE(myshader, m) {
    py::class_<FrameBuffer>(m, "FrameBuffer")
        .def(py::init<size_t, size_t, std::string>())
        .def("display", &FrameBuffer::display)
        .def("should_close", &FrameBuffer::shouldClose);

    m.def("set_array", &set_array, "Set framebuffer pixel data from a numpy array");
}
