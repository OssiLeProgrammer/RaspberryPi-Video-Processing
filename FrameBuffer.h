#pragma once

#include <vector>
#include <string>
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "Shader.h"

struct Vec3 {
    unsigned char R, G, B;
};

// Declare global arrays as extern
extern float data[20];
extern unsigned int elements[6];

class FrameBuffer {
public:
    size_t width;
    size_t height;
    GLFWwindow* window;
    Shader* prog;
    std::vector<Vec3> array;
    unsigned int texID;

    FrameBuffer(size_t width, size_t height, std::string title);
    bool shouldClose();
    void set_buffer();
    void prepare();
    void display();

private:
    unsigned int ID;
    void genVertexArr();
    void genTex();
};
