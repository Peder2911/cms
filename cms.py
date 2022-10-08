"""Bad Ideas CMS

This is a CRUD WSGI application for managing content. Content is saved in files and served as JSON.
"""
import urllib
import os
import datetime
import json
from wsgiref.simple_server import make_server

CONTENT_FOLDER = os.getenv("CMS_CONTENT_FOLDER","content") 
PAGESIZE = 5
ISOSTRFTIME = "%Y-%m-%dT%H:%M:%S%z"

if not os.path.exists(CONTENT_FOLDER):
    os.mkdir(CONTENT_FOLDER)

def list_content(folder: str, page: int):
    filenames = os.listdir(folder)
    creation_times = [datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(folder,f))) for f in filenames]

    entries = list(zip(filenames, creation_times))
    entries.sort(key = lambda e: e[1])j

    entries = entries[page*PAGESIZE:(1+page)*PAGESIZE]

    return {"entries": [{"title":f,"created":t.strftime(ISOSTRFTIME)} for f,t in entries]}

def read_content(folder: str,name: str):
    with open(os.path.join(folder,name)) as f:
        content = f.read() 
        return {"content": content, "title": name}

def write_content(folder,name,content):
    with open(os.path.join(folder,name), "w") as f:
        f.write(content)

def delete_content(folder,name):
    content = read_content(folder,name)
    os.unlink(os.path.join(folder,name))
    return content

def cms(env, start_response):
    status = "200 OK"
    data = None 
    query_parameters = urllib.parse.parse_qs(env["QUERY_STRING"])

    if env["REQUEST_METHOD"] == "POST":
        try:
            data = json.loads(env["wsgi.input"].read(int(env["CONTENT_LENGTH"])))
            write_content(CONTENT_FOLDER, data["title"], data["content"])
        except (json.JSONDecodeError, KeyError):
            status = "400 BAD REQUEST"
            data = {"message": "Bad data posted POSTed"}

    elif env["REQUEST_METHOD"] == "PUT":
        try:
            destination = env["PATH_INFO"]
            data = json.loads(env["wsgi.input"].read(int(env["CONTENT_LENGTH"])))
            write_content(CONTENT_FOLDER, destination, data["content"])
        except (json.JSONDecodeError, KeyError):
            status = "400 BAD REQUEST"
            data = {"message": "Bad data posted POSTed"}

    elif env["REQUEST_METHOD"] == "GET":
        requested_resource = env["PATH_INFO"][1:]
        try:
            page = int(query_parameters.get("page", 0)[0])
        except (ValueError,TypeError):
            page = 0

        if requested_resource == "":
            data = list_content(CONTENT_FOLDER, page)
        else:
            try:
                data = read_content(CONTENT_FOLDER, requested_resource)
            except FileNotFoundError:
                status = "404 NOT FOUND"
                data = {"error":"Not found"}

    elif env["REQUEST_METHOD"] == "DELETE":
        requested_resource = env["PATH_INFO"][1:]
        if requested_resource == "":
            status = "400 BAD REQUEST"
            data = {"message": "Cannot delete root"}
        else:
            try:
                data = delete_content(CONTENT_FOLDER, requested_resource)
            except FileNotFoundError:
                status = "404 NOT FOUND"
                data = {"error":"Not found"}

    else:
        status = "405 METHOD NOT ALLOWED"


    start_response(status, [("Content-Type", "application/json")])
    return [json.dumps(data).encode()]

with make_server("", 8000, cms) as httpd:
    httpd.serve_forever()
