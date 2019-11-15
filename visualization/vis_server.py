#!/usr/bin/python3.6
# source: https://gist.github.com/sanketsudake/3732523
# modified to make it Python 3.6 friendly
#
# run script by python server.py
# open browser with http://127.0.0.1:8000/
# this will open index.html in current directory as default
#
#
import sys
from http.server import BaseHTTPRequestHandler as SimpleHTTPRequestHandler
from http.server import HTTPServer as BaseHTTPServer

HandlerClass = SimpleHTTPRequestHandler
ServerClass  = BaseHTTPServer
Protocol     = "HTTP/1.0"

if sys.argv[1:]:
    port = int(sys.argv[1])
else:
    port = 8000
server_address = ('127.0.0.1', port)

HandlerClass.protocol_version = Protocol
httpd = ServerClass(server_address, HandlerClass)

sa = httpd.socket.getsockname()
print("Serving HTTP on", sa[0], "port", sa[1], "...")
httpd.serve_forever()
