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
        self.running = False # Steuerflag für die Streamingschleife

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
            print(f"Kamera konfiguriert: {self.width}x{self.height} @ {self.framerate} FPS")
            return True
        except Exception as e:
            print(f"Kamera-Initialisierungsfehler: {e}")
            self.cleanup()
            return False

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"Verbinde mit {self.server_host}:{self.server_port}...")
            self.client_socket.connect((self.server_host, self.server_port))
            print("Verbunden mit Server!")
            return True
        except Exception as e:
            print(f"Socket-Verbindungsfehler: {e}")
            self.cleanup()
            return False

    def stream_frames(self):
        """
        Erfasst kontinuierlich Frames von der Kamera, kodiert sie als JPEG
        und sendet sie über den verbundenen Socket.
        """
        if not self.camera or not self.client_socket:
            print("Kamera oder Socket nicht initialisiert. Abbruch.")
            return

        self.running = True
        try:
            while self.running:
                frame_np = self.camera.capture_array()
                video_frame = av.VideoFrame.from_ndarray(frame_np, format='rgb24')
                
                output_buffer = io.BytesIO()
                # Verwenden Sie MJPEG als Format für den Container, da jeder Frame ein separates JPEG ist.
                container = av.open(output_buffer, mode='w', format='mjpeg')
                
                # Fügen Sie einen Videostream hinzu. Die Rate ist wichtig, um die Zeitstempel zu setzen.
                stream = container.add_stream('mjpeg', rate=self.framerate)
                stream.width = self.width
                stream.height = self.height
                stream.pix_fmt = 'yuvj420p' # YUVJ420P ist ein häufiges Pixelformat für JPEGs

                # Kodieren Sie den Frame. Der Encoder kann mehrere Pakete für einen Frame zurückgeben.
                for packet in stream.encode(video_frame):
                    container.mux(packet)
                
                # Schließen Sie den Container, um sicherzustellen, dass alle gepufferten Daten
                # (z.B. Stream-Header, letztes Paket) in den output_buffer geschrieben werden.
                # Wichtig: Für kontinuierliches Streaming sollte der Container nicht bei jedem Frame geschlossen werden,
                # aber für einzelne JPEGs pro Übertragung ist dies der Weg, um ein vollständiges JPEG zu erhalten.
                # Alternativ könnte man den Encoder direkt verwenden und die Pakete sammeln.
                # Hier wird der Container geschlossen, um einen vollständigen JPEG-Stream pro Frame zu erhalten.
                container.close() 
                
                jpeg_bytes = output_buffer.getvalue()
                message_size = len(jpeg_bytes)
                size_prefix = struct.pack('!I', message_size) # 4-Byte-Präfix für die Größe

                self.client_socket.sendall(size_prefix + jpeg_bytes)
                print(f"JPEG-Frame gesendet ({message_size} Bytes).")

                # Eine kleine Verzögerung, um die Bildrate zu steuern (optional, da Picamera2 bereits eine Framerate hat)
                # time.sleep(1 / self.framerate) 

        except ConnectionResetError:
            print("Server hat die Verbindung zwangsweise geschlossen.")
        except Exception as e:
            print(f"Fehler beim Streamen: {e}")
        finally:
            self.cleanup() # Bereinigung nach Beendigung der Schleife oder bei Fehler

    def cleanup(self):
        """
        Bereinigt Kamera- und Socket-Ressourcen.
        """
        if self.camera:
            print("Kamera wird gestoppt.")
            self.camera.stop()
            self.camera = None
        if self.client_socket:
            print("Socket wird geschlossen.")
            self.client_socket.close()
            self.client_socket = None
        self.running = False # Sicherstellen, dass das Flag auf False gesetzt ist

if __name__ == "__main__":
    SERVER_IP = '192.168.1.13' # Ersetzen Sie dies durch die IP-Adresse Ihres Servers
    SERVER_PORT = 8080
    FRAME_WIDTH = 800
    FRAME_HEIGHT = 600
    FRAME_RATE = 30

    sender = PiCameraSender(SERVER_IP, SERVER_PORT, FRAME_WIDTH, FRAME_HEIGHT, FRAME_RATE)
    if sender.initialize_camera():
        if sender.connect_to_server():
            sender.stream_frames() # Aufruf der neuen Methode zum Streamen von Frames

    print("Sender beendet.")
    sys.exit(0)
