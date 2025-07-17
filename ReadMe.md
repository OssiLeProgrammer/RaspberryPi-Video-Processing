# Raspberry Pi Camera Shader Stream

This project is designed for anyone using a **Raspberry Pi** with an additional camera module.  
It enables real-time shader processing and streaming via a Python module built with C++ and OpenGL.

---

## Building the Project

From the project root directory, run the following commands to configure and build the project:

cmake -S . -B build
cmake --build build --config Release

After the build completes, locate the generated Python module file (with extension .pyd or .so) inside the build directory and rename it to:

- myshader.pyd

## Installing Python Dependencies
Install the necessary Python packages listed in the import.txt file by running:


- pip install -r import.txt

## Running the Application
On your host machine, run:

- python Server.py

# Notes
Ensure your Raspberry Pi camera module is properly connected and configured.

- The Raspberry Pi-specific variant is located in the raspi_stuff folder.

- Make sure you have system-wide Python enabled.

- If you encounter issues, verify that all dependencies are installed and that the camera is working.

- FFmpeg must be installed for all related functionality.