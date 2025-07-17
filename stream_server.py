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
        Startet den Server, bindet ihn an den angegebenen Host und Port und lauscht auf Verbindungen.
        """
        try:
            self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listening_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.listening_socket.bind((self.host, self.port))
            self.listening_socket.listen(backlog)
            print(f"Server lauscht auf {self.host}:{self.port} für JPEG-Videostrom.")
            self.running = True
            return True
        except Exception as e:
            print(f"Fehler beim Starten des Servers: {e}")
            self.close()
            return False

    def _recv_all(self, sock, n_bytes):
        """
        Hilfsfunktion, um sicherzustellen, dass alle n_bytes vom Socket empfangen werden.
        """
        data = b''
        while len(data) < n_bytes:
            packet = sock.recv(n_bytes - len(data))
            if not packet:
                # Client getrennt oder Fehler
                return None
            data += packet
        return data

    def run_forever(self):
        print("Warte auf eine Client-Verbindung...")
        try:
            conn, addr = self.listening_socket.accept()
            print(f"Verbunden mit {addr}")
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


            codec = av.CodecContext.create("mjpeg", "r")

            while self.running and not self.fb.should_close():
                # 1. 4-Byte-Größenpräfix lesen
                size_prefix = self._recv_all(conn, struct.calcsize('!I'))
                if size_prefix is None:
                    print("Client während des Lesens des Größenpräfixes getrennt.")
                    break # Client getrennt

                try:
                    # Größe der eingehenden JPEG-Daten entpacken
                    jpeg_payload_size = struct.unpack('!I', size_prefix)[0]
                except struct.error as e:
                    print(f"Fehler beim Entpacken des Größenpräfixes: {e}. Beschädigte Daten empfangen.")
                    break # Beschädigte Daten, Verbindung trennen

                # 2. Genaue Anzahl der Bytes für die JPEG-Nutzlast lesen
                jpeg_data = self._recv_all(conn, jpeg_payload_size)
                if jpeg_data is None:
                    print("Client während des Lesens der JPEG-Daten getrennt.")
                    break # Client getrennt

                # Ein AvPacket aus den empfangenen JPEG-Daten erstellen
                # Für MJPEG ist jeder empfangene Chunk ein vollständiges JPEG-Bild (Paket).
                packet = av.Packet(jpeg_data)
                
                # Paket dekodieren. Für MJPEG liefert ein Paket normalerweise einen Frame.
                frames = codec.decode(packet)

                for frame in frames:
                    # Den dekodierten Frame in ein NumPy-Array im RGB24-Format konvertieren
                    rgb_image = frame.to_ndarray(format="rgb24")
                    
                    # Sicherstellen, dass die Dimensionen übereinstimmen, bevor das Array gesetzt wird
                    if rgb_image.shape[0] == self.height and rgb_image.shape[1] == self.width:
                        myshader.set_array(self.fb, rgb_image)
                        self.fb.display()
                    else:
                        print(f"Warnung: Empfangene Frame-Dimensionen {rgb_image.shape[1]}x{rgb_image.shape[0]} stimmen nicht mit den erwarteten {self.width}x{self.height} überein. Anzeige übersprungen.")
                    
                    # Kleine Verzögerung, um eine Überlastung des Displays/der CPU zu vermeiden, bei Bedarf anpassen
                    time.sleep(0.01) 

        except ConnectionResetError:
            print("Client hat die Verbindung zwangsweise geschlossen.")
        except Exception as e:
            print(f"Fehler in der run_forever-Schleife: {e}")
        finally:
            if 'conn' in locals() and conn:
                print("Client-Verbindung wird geschlossen.")
                conn.close()
            self.close() # Sicherstellen, dass Server-Ressourcen bereinigt werden

    def close(self):
        """
        Schließt den lauschenden Socket des Servers und den Framebuffer.
        """
        self.running = False
        if self.listening_socket:
            print("Lauschender Socket des Servers wird geschlossen.")
            # Der shutdown-Aufruf wurde entfernt, da er für lauschende Sockets oft nicht notwendig ist
            # und zu Fehlern führen kann, wenn der Socket bereits in einem ungültigen Zustand ist.
            # socket.close() ist ausreichend, um die Ressourcen freizugeben.
            self.listening_socket.close()
            self.listening_socket = None

        if self.fb:
            print("Framebuffer wird geschlossen.")
            # Hier können zusätzliche Framebuffer-Bereinigungen vorgenommen werden, falls myshader.FrameBuffer eine close/destroy-Methode hat
            # self.fb.close() # Beispiel, falls eine solche Methode existiert

if __name__ == "__main__":
    SERVER_IP = '0.0.0.0' # Auf allen verfügbaren Netzwerkschnittstellen lauschen
    SERVER_PORT = 8080
    FRAME_WIDTH = 800     # Muss mit der FRAME_WIDTH des Senders übereinstimmen
    FRAME_HEIGHT = 600    # Muss mit der FRAME_HEIGHT des Senders übereinstimmen
    TITLE = "Shader Server"

    server = Server(SERVER_IP, SERVER_PORT, FRAME_WIDTH, FRAME_HEIGHT, TITLE)
    if server.start():
        server.run_forever()
    
    print("Server beendet.")
    sys.exit(0)
