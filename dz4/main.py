import http.server
import socketserver
import threading
import json
import socket
import datetime

# HTTP Server Handler
class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/message':
            self.path = '/message.html'
        elif self.path == '/send':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Message sent successfully!")
            return
        try:
            with open(self.path[1:], 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            with open('error.html', 'rb') as file:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(file.read())

    def do_POST(self):
        if self.path == '/send':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            username = post_data.split('&')[0].split('=')[1]
            message = post_data.split('&')[1].split('=')[1]
            data = f"{username}|{message}"
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(data.encode(), ('localhost', 5000))
            sock.close()
            self.send_response(302)
            self.send_header('Location', '/send')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

# Socket Server
def socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', 5000))
    while True:
        data, addr = sock.recvfrom(1024)
        message_data = data.decode().split('|')
        timestamp = str(datetime.datetime.now())
        message_dict = {timestamp: {"username": message_data[0], "message": message_data[1]}}
        try:
            with open('storage/data.json', 'r') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {}
        existing_data.update(message_dict)
        with open('storage/data.json', 'w') as f:
            json.dump(existing_data, f, indent=2)

# Start servers in threads
httpd = socketserver.TCPServer(('', 3000), RequestHandler)
thread_http = threading.Thread(target=httpd.serve_forever)
thread_http.daemon = True
thread_http.start()

thread_socket = threading.Thread(target=socket_server)
thread_socket.daemon = True
thread_socket.start()

thread_http.join()
thread_socket.join()