#version 330 core
layout (location = 0) in vec3 aPOS;
layout (location = 1) in vec2 texUV;

out vec2 UV;

void main() {
	UV = texUV;
	gl_Position = vec4(aPOS, 1.0f);
}