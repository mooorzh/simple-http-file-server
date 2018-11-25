from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import mimetypes as memetypes
import shutil
import cgi
import hashlib
import random

import json
PORT_NUMBER = 80

STORE_PATH = "store/"

SITE_ROOT = "http://127.0.0.1" + ":" + str(PORT_NUMBER)

def create_filepath(filename):
    name, ext = os.path.splitext(filename)
    hashed_name = hashlib.sha1(name.encode("UTF-8")).hexdigest()
    dirpath = STORE_PATH + hashed_name[0:2]

    fpath =  dirpath + "/" + hashed_name + ext
    #directory = os.path.dirname(dirpath)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    while os.path.isfile(fpath):
        fpath = dirpath + "/" + hashed_name + str(random.randint(0,999)) + ext

    return fpath

def make_filepath(filename):
    return STORE_PATH + filename[0:2] + "/" + filename

class myHandler(BaseHTTPRequestHandler):

    def send_headers(self):
        path_elements = self.path[1:].split("/")
        if path_elements[0] == "upload":
            self.send_response(200)
            self.send_header("Content-Type", "text/json; charset=utf-8")
            self.end_headers()
        elif path_elements[0] == "download":
            reqfile = make_filepath(path_elements[1])
            if not os.path.isfile(reqfile) or not os.access(reqfile, os.R_OK):
                self.send_error(404, "file not found")
                return None
            content, encoding = memetypes.MimeTypes().guess_type(reqfile)
            if content is None:
                content = "application/octet-stream"
            info = os.stat(reqfile)
            self.send_response(200)
            self.send_header("Content-Type", content)
            self.send_header("Content-Encoding", encoding)
            self.send_header("Content-Length", info.st_size)
            self.end_headers()
        elif path_elements[0] == "delete":
            self.send_response(200)
            self.send_header("Content-Type", "text/json; charset=utf-8")
            self.end_headers()
        else:
            self.send_error(404,"Wrong URL!")
            return None
        return path_elements


    def do_HEAD(self):
        self.send_headers()

    def do_GET(self):
        path_elements = self.send_headers()

        if path_elements is None:
            return

        if path_elements[0] == "download":
            reqfile = make_filepath(path_elements[1])
            f = open(reqfile, 'rb')
            shutil.copyfileobj(f, self.wfile)
            f.close()
        elif path_elements[0] == "delete":
            reqfile = create_filepath(path_elements[1])
            if os.path.isfile(reqfile):
                os.remove(reqfile)
                result = {
                    "success": True,
                    "status": 200,
                    }
                self.wfile.write(json.dumps(result).encode())
            else:
                self.send_error(404, "File does not exist")
        else:
            self.send_error(404, "Wrong method!")


    def do_POST(self):
        elements = self.send_headers()
        if elements is None or elements[0] != "upload":
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE":   self.headers['Content-Type']
            })


        fpath = create_filepath(form["file"].filename)

        fdst = open(fpath, "wb")
        shutil.copyfileobj(form["file"].file, fdst)
        fdst.close()
        fname = fpath.split("/")[-1]
        result = {
            "data": { "url": SITE_ROOT + "/download/" + fname },
            "success": True,
            "status": 200,
            }
        self.wfile.write(json.dumps(result).encode())

import daemon


with daemon.DaemonContext():
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    print('Started httpserver on port ' , PORT_NUMBER)
    server.serve_forever()
