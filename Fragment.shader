#version 330 core


in vec2 UV;
out vec4 aColor;

uniform sampler2D texUNI;

void main() {
	aColor = texture(texUNI, UV);	
}