import socket
from re import match
from time import strftime, localtime
import os


class SimpleHttpServer:
    def __init__(self, static_dir, host, port):
        self.static_dir = static_dir
        self.host = host
        self.port = port

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            print("Http server starts on port {0}. Root dir is {1}.".format(self.port,
                os.path.join(os.path.dirname(os.path.abspath(__file__)), self.static_dir)))
            print("Please press Ctrl+C to shut down the server and exit.")
            self._wait_for_connections()
        except socket.error as e:
            print(str(e))
            self.shutdown()

    def shutdown(self):
        try:
            print("Shutting down the server.")
            self.socket.close()
        except Exception as e:
            print("Warning: could not close the socket.", e)

    def _wait_for_connections(self):
        while True:
            self.socket.listen(1)
            conn, addr = self.socket.accept()
            print("There is established connection with host. Address: {0}".format(addr[0]))
            request_data = b""
            while True:
                data_part = conn.recv(1024)
                request_data += data_part
                if request_data.endswith(b"\r\n\r\n") or request_data.endswith(b"\n\n"):
                    break
            response = self._match_response(request_data)
            conn.send(response.encode())
            conn.close()

    def _match_response(self, request_data):
        headers = []
        response_body = ""
        request_line_parts = self._get_request_line_parts(bytes.decode(request_data))
        if request_line_parts == None:
            message = "Bad Request"
            status_code = 400
        else:
            method, resource_addr = request_line_parts
            print("Request method: " + method)
            print("Requested resource: /" + resource_addr)
            if method != "GET":
                message = "Not Implemented"
                status_code = 501
            else:
                if resource_addr == "":
                    resource_addr = "index.html"
                try:
                    with open(os.path.join(self.static_dir, resource_addr)) as f:
                        response_body = f.read()
                        status_code = 200
                        message = "OK"
                except FileNotFoundError:
                    message = "Not Found"
                    status_code = 404
                    with open(os.path.join(self.static_dir, "404.html")) as f:
                        response_body = f.read()
                headers.append(("Content-Type", "text/html;charset=utf-8"))
                headers.append(("Content-Language", "en"))
                headers.append(("Content-Length", len(response_body)))
        local_date = strftime("%a, %d %b %Y %H:%M:%S", localtime())
        headers.append(("Date", local_date))
        headers.append(("Server", "Simple-Python-HTTP-Server"))
        headers.append(("Connection", "close"))
        print("Response line: " + "HTTP/1.1 " + str(status_code) + " " + message)
        return self._make_response(headers, message, status_code, response_body)

    def _get_request_line_parts(self, data):
        matches = match("(\S+?)\s+/(\S*?)\s+HTTP", data.strip())
        if matches == None:
            return None
        return matches.group(1, 2)

    def _make_response(self, headers, message, status_code, data):
        response = "HTTP/1.1 " + str(status_code) + " " + message + "\r\n"
        response += "\r\n".join("%s: %s" % header for header in headers)
        if data != "":
            response += "\r\n\r\n"
            response += data
        response += "\r\n"
        return response


if __name__ == "__main__":
    server = SimpleHttpServer('static', '', 8000)
    try:
        server.start()
    except KeyboardInterrupt:
        server.shutdown()