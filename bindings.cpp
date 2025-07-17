#include "bindings.h"
#include <stdexcept>
#include <glad/glad.h> // Make sure glad is included for OpenGL functions

void set_array(FrameBuffer& fb, py::array_t<unsigned char> np_array) {
    py::buffer_info info = np_array.request();
    size_t height = info.shape[0];
    size_t width  = info.shape[1];
    // Use a preprocessor directive for debug output
#ifdef DEBUG_GRAPHICS // You can define your own debug macro name
    std::cout << "DEBUG_GRAPHICS: set_array called with array dimensions: "
              << info.shape[0] << " (height) x "
              << info.shape[1] << " (width) x "
              << info.shape[2] << " (channels)" << std::endl;
    std::cout << "DEBUG_GRAPHICS: Framebuffer dimensions: "
              << fb.height << " (height) x "
              << fb.width << " (width)" << std::endl;
    if (info.ndim != 3 || info.shape[2] != 3) {
        throw std::runtime_error("Expected numpy array of shape (height, width, 3) with dtype=uint8");
    }

    if (width != fb.width || height != fb.height) {
        throw std::runtime_error("Array dimensions must match framebuffer dimensions");
    }
    if (fb.array.size() != width * height * 3) {
        throw std::runtime_error("fb.array size doesn't match expected framebuffer pixel count (width * height * 3)");
    }

#endif
    auto* ptr = static_cast<unsigned char*>(info.ptr);
    std::memcpy(&fb.array[0], &ptr[0], width * height * 3);
    glBindTexture(GL_TEXTURE_2D, fb.texID);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, fb.width, fb.height, 0, GL_RGB, GL_UNSIGNED_BYTE, fb.array.data());
}

PYBIND11_MODULE(myshader, m) {
    py::class_<FrameBuffer>(m, "FrameBuffer")
        .def(py::init<size_t, size_t, std::string>())
        .def("prepare", &FrameBuffer::prepare)
        .def("display", &FrameBuffer::display)
        .def("should_close", &FrameBuffer::shouldClose);

    m.def("set_array", &set_array, "Set framebuffer pixel data from a numpy array");
}
