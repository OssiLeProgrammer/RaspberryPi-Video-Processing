import socket
import numpy as np
from picamera2 import Picamera2
import time
import sys
import av
import io
import struct

class PiCameraSender:
    def __init__(self, server_host, server_port, width, height, framerate=30):
        self.server_host = server_host
        self.server_port = server_port
        self.width = width
        self.height = height
        self.framerate = framerate
        self.camera = None
        self.client_socket = None
        self.running = False  # Control flag for the streaming loop

    def initialize_camera(self):
        try:
            self.camera = Picamera2()
            video_config = self.camera.create_video_configuration(
                main={"format": 'RGB888', "size": (self.width, self.height)},
                controls={"FrameRate": self.framerate}
            )
            self.camera.configure(video_config)
            self.camera.start()
            time.sleep(1)
            print(f"Camera configured: {self.width}x{self.height} @ {self.framerate} FPS")
            return True
        except Exception as e:
            print(f"Camera initialization error: {e}")
            self.cleanup()
            return False

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"Connecting to {self.server_host}:{self.server_port}...")
            self.client_socket.connect((self.server_host, self.server_port))
            print("Connected to server!")
            return True
        except Exception as e:
            print(f"Socket connection error: {e}")
            self.cleanup()
            return False

    def stream_frames(self):
        """
        Continuously captures frames from the camera, encodes them as JPEG,
        and sends them over the connected socket.
        """
        if not self.camera or not self.client_socket:
            print("Camera or socket not initialized. Aborting.")
            return

        self.running = True
        try:
            while self.running:
                frame_np = self.camera.capture_array()
                video_frame = av.VideoFrame.from_ndarray(frame_np, format='rgb24')

                output_buffer = io.BytesIO()
                # Use MJPEG as container format because each frame is a separate JPEG.
                container = av.open(output_buffer, mode='w', format='mjpeg')

                # Add a video stream. Rate is important to set timestamps.
                stream = container.add_stream('mjpeg', rate=self.framerate)
                stream.width = self.width
                stream.height = self.height
                stream.pix_fmt = 'yuvj420p'  # YUVJ420P is a common pixel format for JPEGs

                # Encode the frame. Encoder may return multiple packets per frame.
                for packet in stream.encode(video_frame):
                    container.mux(packet)

                # Close the container to ensure all buffered data
                # (e.g., stream headers, last packet) is written to output_buffer.
                # Note: For continuous streaming, you wouldn't close the container every frame,
                # but since we're sending individual JPEGs per transmission, this ensures
                # a complete JPEG image is obtained.
                # Alternatively, you could directly use the encoder and collect packets.
                container.close()

                jpeg_bytes = output_buffer.getvalue()
                message_size = len(jpeg_bytes)
                size_prefix = struct.pack('!I', message_size)  # 4-byte prefix for the size

                self.client_socket.sendall(size_prefix + jpeg_bytes)
                print(f"JPEG frame sent ({message_size} bytes).")

                # Small delay to control frame rate (optional, Picamera2 already sets framerate)
                # time.sleep(1 / self.framerate)

        except ConnectionResetError:
            print("Server forcibly closed the connection.")
        except Exception as e:
            print(f"Error during streaming: {e}")
        finally:
            self.cleanup()  # Cleanup after loop ends or on error

    def cleanup(self):
        """
        Cleans up camera and socket resources.
        """
        if self.camera:
            print("Stopping camera.")
            self.camera.stop()
            self.camera = None
        if self.client_socket:
            print("Closing socket.")
            self.client_socket.close()
            self.client_socket = None
        self.running = False  # Ensure the flag is set to False

if __name__ == "__main__":
    SERVER_IP = '192.168.1.13'  # Replace this with your server's IP address
    SERVER_PORT = 8080
    FRAME_WIDTH = 800
    FRAME_HEIGHT = 600
    FRAME_RATE = 30

    sender = PiCameraSender(SERVER_IP, SERVER_PORT, FRAME_WIDTH, FRAME_HEIGHT, FRAME_RATE)
    if sender.initialize_camera():
        if sender.connect_to_server():
            sender.stream_frames()  # Call the new method to stream frames

    print("Sender stopped.")
    sys.exit(0)
