from http.server import BaseHTTPRequestHandler, HTTPServer
log = "LOG"
class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        global log
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()

        message = log
        self.wfile.write(bytes(message, "utf8"))
        print(message)
    def do_POST(self):
        global log
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        log += str(self.rfile.read())
        #print(self.log)
        #message = "Hello, World! Here is a POST response"
        #self.wfile.write(bytes(message, "utf8"))

with HTTPServer(('', 8000), handler) as server:
    server.serve_forever()