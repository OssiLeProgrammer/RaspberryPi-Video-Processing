import socket
import myshader
import numpy as np
import sys # For sys.exit()

class Server:
    def __init__(self, host: str, port: int, width: int, height: int, title: str = "Shader Server"):
        self.width = width
        self.height = height
        self.host = host
        self.port = port
        self.listening_socket = None # Renamed for clarity: this is the main listening socket
        self.fb = None # Initialize framebuffer later for cleaner error handling if socket fails

        self.expected_frame_size = self.width * self.height * 3 # RGB, 1 byte per channel

    def start(self, backlog: int = 5):
        """Initializes and starts the server listening."""
        try:
            self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Good practice
            self.listening_socket.bind((self.host, self.port))
            self.listening_socket.listen(backlog)
            print(f"Server listening on {self.host}:{self.port} for {self.width}x{self.height} frames.")

            # Initialize framebuffer after socket setup is successful
            self.fb = myshader.FrameBuffer(self.width, self.height, self.title)
            return True
        except socket.error as e:
            print(f"Error starting server: {e}")
            self.close() # Ensure sockets are closed on startup failure
            return False
        except Exception as e:
            print(f"Error initializing framebuffer: {e}")
            self.close()
            return False

    def run_forever(self):
        """Continuously accepts one client and displays received frames."""
        if not self.listening_socket or not self.fb:
            print("Server not started or framebuffer not initialized. Call .start() first.")
            return

        while True: # Loop to accept new clients after the previous one disconnects
            if self.fb.should_close():
                print("Display window closed. Server exiting.")
                break # Exit the server loop if the window is closed

            try:
                print("Waiting for a client connection...")
                # Accept a new client connection (this blocks)
                conn, addr = self.listening_socket.accept()
                print(f"Connected with {addr}")

                with conn: # Use 'with' statement for the connection socket
                    while not self.fb.should_close(): # Keep displaying while window is open
                        # --- Receive ALL expected bytes for the frame ---
                        received_bytes = bytearray()
                        bytes_left = self.expected_frame_size
                        while bytes_left > 0:
                            # Attempt to receive remaining bytes in chunks
                            chunk = conn.recv(min(bytes_left, 4096)) # Receive in chunks, e.g., 4KB
                            if not chunk: # Client disconnected or no more data
                                print(f"Client {addr} disconnected unexpectedly or no more data.")
                                break # Exit inner loop, try accepting a new client

                            received_bytes.extend(chunk)
                            bytes_left -= len(chunk)

                        if bytes_left > 0: # If we didn't get all bytes, something went wrong
                            print(f"Warning: Did not receive full frame from {addr}. Expected {self.expected_frame_size}, got {len(received_bytes)}.")
                            continue # Try receiving the next frame

                        # Convert received bytes to numpy array and reshape
                        try:
                            # Use np.frombuffer for efficiency with bytearray
                            frame_data = np.frombuffer(received_bytes, dtype=np.uint8).reshape((self.height, self.width, 3))
                            myshader.set_array(self.fb, frame_data) # Use the correct function name
                            self.fb.display() # Display the updated framebuffer
                        except ValueError as e:
                            print(f"Error processing frame from {addr}: {e}")
                            print(f"Received data length: {len(received_bytes)}")
                            # Continue to try receiving next frame if this one was corrupt
                            continue
                        except Exception as e:
                            print(f"Unexpected error during display update: {e}")
                            break # Critical error, break out of inner loop

                    # If the inner loop broke because the window closed
                    if self.fb.should_close():
                        print("Display window closed while client was connected. Exiting server.")
                        break # Exit the main server loop as well

            except socket.timeout: # Only if a timeout is set on self.listening_socket
                print("Server accept operation timed out. Still listening...")
                # Continue the loop to try accepting again
            except KeyboardInterrupt:
                print("\nServer interrupted by user (Ctrl+C). Exiting.")
                break # Exit the server loop gracefully
            except socket.error as e:
                print(f"Socket error accepting connection: {e}")
                # For critical socket errors, it's often best to stop the server
                break
            except Exception as e:
                print(f"An unexpected error occurred in the main server loop: {e}")
                break # Catch any other unhandled exceptions

    def close(self):
        """Closes the listening socket and framebuffer."""
        if self.listening_socket:
            print("Closing server listening socket.")
            self.listening_socket.close()
            self.listening_socket = None
        if self.fb:
            print("Closing framebuffer.")
