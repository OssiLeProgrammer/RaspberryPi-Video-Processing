from Server import Server

tcpServer = Server("192.168.1.13", 8080, 800, 600, "myProgram")
tcpServer.start()
tcpServer.run_forever()