#include "Shader.h"
#include <iostream>
#include <fstream>
#include <sstream>

Shader::Shader(std::string vertPath, std::string fragPath) : ID(0) {
    std::ifstream vpStream;
    std::ifstream fpStream;
    std::stringstream vStringStream;
    std::stringstream fStringStream;
    std::string vString;
    std::string fString;

    DEBUG_PRINT("Attempting to load shaders: " << vertPath << " and " << fragPath);

    try {
        vpStream.open(vertPath.c_str());
        if (!vpStream.is_open()) {
            std::cerr << "ERROR::SHADER::FILE_NOT_FOUND: Could not open vertex shader file: " << vertPath << std::endl;
            return;
        }
        vStringStream << vpStream.rdbuf();
        vpStream.close();
        vString = vStringStream.str();
        if (vString.empty()) {
            std::cerr << "ERROR::SHADER::FILE_EMPTY: Vertex shader file is empty: " << vertPath << std::endl;
            return;
        }
        DEBUG_PRINT("Successfully loaded vertex shader from: " << vertPath);

        fpStream.open(fragPath.c_str());
        if (!fpStream.is_open()) {
            std::cerr << "ERROR::SHADER::FILE_NOT_FOUND: Could not open fragment shader file: " << fragPath << std::endl;
            return;
        }
        fStringStream << fpStream.rdbuf();
        fpStream.close();
        fString = fStringStream.str();
        if (fString.empty()) {
            std::cerr << "ERROR::SHADER::FILE_EMPTY: Fragment shader file is empty: " << fragPath << std::endl;
            return;
        }
        DEBUG_PRINT("Successfully loaded fragment shader from: " << fragPath);
    }
    catch (const std::exception& e) {
        std::cerr << "ERROR::SHADER::FILE_READ_EXCEPTION: An unexpected error occurred while reading shader files: " << e.what() << std::endl;
        return;
    }

    ID = glCreateProgram();
    if (ID == 0) {
        std::cerr << "ERROR::SHADER::PROGRAM_CREATION_FAILED: Failed to create OpenGL shader program." << std::endl;
        return;
    }
    DEBUG_PRINT("OpenGL program created with ID: " << ID);

    unsigned int vertexShader = glCreateShader(GL_VERTEX_SHADER);
    unsigned int fragmentShader = glCreateShader(GL_FRAGMENT_SHADER);

    if (vertexShader == 0) {
        std::cerr << "ERROR::SHADER::VERTEX_SHADER_CREATION_FAILED: Failed to create vertex shader object." << std::endl;
        glDeleteProgram(ID); ID = 0; return;
    }
    if (fragmentShader == 0) {
        std::cerr << "ERROR::SHADER::FRAGMENT_SHADER_CREATION_FAILED: Failed to create fragment shader object." << std::endl;
        glDeleteProgram(ID); glDeleteShader(vertexShader); ID = 0; return;
    }

    const char* vPtr = vString.c_str();
    const char* fPtr = fString.c_str();

    glShaderSource(vertexShader, 1, &vPtr, NULL);
    glShaderSource(fragmentShader, 1, &fPtr, NULL);

    char infoLog[512];
    int shaderStatus;

    // Compile Vertex Shader
    DEBUG_PRINT("Compiling vertex shader...");
    glCompileShader(vertexShader);
    glGetShaderiv(vertexShader, GL_COMPILE_STATUS, &shaderStatus);
    if (!shaderStatus) {
        glGetShaderInfoLog(vertexShader, 512, NULL, infoLog);
        std::cerr << "ERROR::SHADER::VERTEX::COMPILATION_FAILED\n" << infoLog << std::endl;
        glDeleteShader(vertexShader);
        glDeleteShader(fragmentShader);
        glDeleteProgram(ID);
        ID = 0;
        return;
    }
    DEBUG_PRINT("Vertex shader compiled successfully.");

    // Compile Fragment Shader
    DEBUG_PRINT("Compiling fragment shader...");
    glCompileShader(fragmentShader);
    glGetShaderiv(fragmentShader, GL_COMPILE_STATUS, &shaderStatus);
    if (!shaderStatus) {
        glGetShaderInfoLog(fragmentShader, 512, NULL, infoLog);
        std::cerr << "ERROR::SHADER::FRAGMENT::COMPILATION_FAILED\n" << infoLog << std::endl;
        glDeleteShader(vertexShader);
        glDeleteShader(fragmentShader);
        glDeleteProgram(ID);
        ID = 0;
        return;
    }
    DEBUG_PRINT("Fragment shader compiled successfully.");

    // Link Program
    DEBUG_PRINT("Attaching shaders to program and linking...");
    glAttachShader(ID, vertexShader);
    glAttachShader(ID, fragmentShader);
    glLinkProgram(ID);
    glGetProgramiv(ID, GL_LINK_STATUS, &shaderStatus);
    if (!shaderStatus) {
        glGetProgramInfoLog(ID, 512, NULL, infoLog);
        std::cerr << "ERROR::SHADER::PROGRAM::LINKING_FAILED\n" << infoLog << std::endl;
        glDeleteShader(vertexShader);
        glDeleteShader(fragmentShader);
        glDeleteProgram(ID);
        ID = 0;
        return;
    }
    DEBUG_PRINT("Shader program linked successfully.");

    glDeleteShader(vertexShader);
    glDeleteShader(fragmentShader);
    DEBUG_PRINT("Shaders deleted after linking.");
}

void Shader::use() {
    if (ID != 0) {
        glUseProgram(ID);
    }
    else {
        std::cerr << "WARNING: Attempted to use uninitialized shader program." << std::endl;
    }
}

void Shader::setInt(std::string uniform, int val) {
#ifdef DEBUG
    if (ID == 0) {
        std::cerr << "WARNING: Attempted to set uniform on uninitialized shader program." << std::endl;
        return;
    }
    int loc = glGetUniformLocation(ID, uniform.c_str());
    if (loc == -1) {
        std::cerr << "WARNING: Uniform '" << uniform << "' not found in shader program (ID: " << ID << "). It might be optimized out or misspelled." << std::endl;
    }
    else {
        glUniform1i(loc, val);
    }
#else
        int loc = glGetUniformLocation(ID, uniform.c_str());
        glUniform1i(loc, val);
#endif

}

Shader::~Shader() {
    if (ID != 0) {
        glDeleteProgram(ID);
        DEBUG_PRINT("Shader program ID " << ID << " deleted.");
    }
}
