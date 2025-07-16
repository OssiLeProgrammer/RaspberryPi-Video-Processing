#pragma once
#include <string>
#include <glad/glad.h>

#ifdef DEBUG_MODE
#include <iostream>
#define DEBUG_PRINT(x) std::cout << "DEBUG: " << x << std::endl
#else
#define DEBUG_PRINT(x)
#endif

class Shader {
public:
    unsigned int ID;

    Shader(std::string vertPath, std::string fragPath);
    void use();
    void setInt(std::string uniform, int val);
    ~Shader();
};
