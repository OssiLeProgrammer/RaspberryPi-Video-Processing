import socket
import sys
sys.path.append("build/Release")
import myshader
import numpy as np
import time
import av
import struct

class Server:
    def __init__(self, host: str, port: int, width: int, height: int, title: str = "Shader Server"):
        self.width = width
        self.height = height
        self.title = title
        self.host = host
        self.port = port
        self.listening_socket = None
        self.fb = myshader.FrameBuffer(self.width, self.height, self.title)

        self.running = False

    def start(self, backlog: int = 5):
        """
        Starts the server, binds it to the specified host and port, and listens for connections.
        """
        try:
            self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listening_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.listening_socket.bind((self.host, self.port))
            self.listening_socket.listen(backlog)
            print(f"Server listening on {self.host}:{self.port} for JPEG video stream.")
            self.running = True
            return True
        except Exception as e:
            print(f"Error starting server: {e}")
            self.close()
            return False

    def _recv_all(self, sock, n_bytes):
        """
        Helper function to ensure all n_bytes are received from the socket.
        """
        data = b''
        while len(data) < n_bytes:
            packet = sock.recv(n_bytes - len(data))
            if not packet:
                # Client disconnected or error occurred
                return None
            data += packet
        return data

    def run_forever(self):
        print("Waiting for a client connection...")
        try:
            conn, addr = self.listening_socket.accept()
            print(f"Connected to {addr}")
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            codec = av.CodecContext.create("mjpeg", "r")

            while self.running and not self.fb.should_close():
                # Internal checks
                self.fb.prepare()

                # 1. Read 4-byte size prefix
                size_prefix = self._recv_all(conn, struct.calcsize('!I'))
                if size_prefix is None:
                    print("Client disconnected while reading size prefix.")
                    break  # Client disconnected

                try:
                    # Unpack size of incoming JPEG data
                    jpeg_payload_size = struct.unpack('!I', size_prefix)[0]
                except struct.error as e:
                    print(f"Error unpacking size prefix: {e}. Corrupted data received.")
                    break  # Corrupted data, disconnect

                # 2. Read the exact number of bytes for the JPEG payload
                jpeg_data = self._recv_all(conn, jpeg_payload_size)
                if jpeg_data is None:
                    print("Client disconnected while reading JPEG data.")
                    break  # Client disconnected

                # Create an AvPacket from received JPEG data
                # For MJPEG, each received chunk is a full JPEG frame (packet).
                packet = av.Packet(jpeg_data)

                # Decode packet. For MJPEG, one packet usually yields one frame.
                frames = codec.decode(packet)

                for frame in frames:
                    # Convert decoded frame to a NumPy array in RGB24 format
                    rgb_image = frame.to_ndarray(format="rgb24")

                    # Ensure dimensions match before setting the array
                    if rgb_image.shape[0] == self.height and rgb_image.shape[1] == self.width:
                        myshader.set_array(self.fb, rgb_image)
                        self.fb.display()
                    else:
                        print(f"Warning: Received frame dimensions {rgb_image.shape[1]}x{rgb_image.shape[0]} do not match expected {self.width}x{self.height}. Skipping display.")

                    # Small delay to avoid overloading display/CPU, adjust if needed
                    time.sleep(0.01)

        except ConnectionResetError:
            print("Client forcibly closed the connection.")
        except Exception as e:
            print(f"Error in run_forever loop: {e}")
        finally:
            if 'conn' in locals() and conn:
                print("Closing client connection.")
                conn.close()
            self.close()  # Ensure server resources are cleaned up

    def close(self):
        """
        Closes the server's listening socket and the framebuffer.
        """
        self.running = False
        if self.listening_socket:
            print("Closing server listening socket.")
            # The shutdown call was removed because it is often unnecessary for listening sockets
            # and can cause errors if the socket is already in an invalid state.
            # socket.close() is sufficient to release resources.
            self.listening_socket.close()
            self.listening_socket = None

        if self.fb:
            print("Closing framebuffer.")
            # Additional framebuffer cleanup can be done here if myshader.FrameBuffer has a close/destroy method
            # self.fb.close() # Example if such a method exists

if __name__ == "__main__":
    SERVER_IP = '0.0.0.0'  # Listen on all available network interfaces
    SERVER_PORT = 8080
    FRAME_WIDTH = 800      # Must match the FRAME_WIDTH of the sender
    FRAME_HEIGHT = 600     # Must match the FRAME_HEIGHT of the sender
    TITLE = "Shader Server"

    server = Server(SERVER_IP, SERVER_PORT, FRAME_WIDTH, FRAME_HEIGHT, TITLE)
    if server.start():
        server.run_forever()

    print("Server stopped.")
    sys.exit(0)
