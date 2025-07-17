#version 330 core

in vec2 UV;
out vec4 aColor;

uniform sampler2D texUNI;

void main() {
    vec3 color = texture(texUNI, UV).rgb;

    // Apply gamma correction (linear → gamma space)
    color = pow(color, vec3(1.0 / 2.2));

    aColor = vec4(color, 1.0);
}
