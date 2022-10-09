"""Bad Ideas CMS

This is a CRUD WSGI application for managing content. Content is saved in files, and rendered to HTML that can be served.
"""
import urllib
import os
import datetime
import json
from wsgiref.simple_server import make_server

SERVER_TOKEN = os.getenv("CMS_SERVER_TOKEN", "changeme")
PORT = int(os.getenv("CMS_PORT", 8000))
CONTENT_FOLDER = os.getenv("CMS_CONTENT_FOLDER","content") 
HTML_FOLDER = os.getenv("CMS_CONTENT_FOLDER","www/html") 
PAGESIZE = 5
ISOSTRFTIME = "%Y-%m-%dT%H:%M:%S%z"

if not os.path.exists(CONTENT_FOLDER):
    os.mkdir(CONTENT_FOLDER)

def list_content(folder: str, page: int):
    filenames = [fn for fn in os.listdir(folder) if not fn[0]=="."]
    creation_times = [datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(folder,f))) for f in filenames]

    entries = list(zip(filenames, creation_times))
    entries.sort(key = lambda e: e[1])

    entries = entries[page*PAGESIZE:(1+page)*PAGESIZE]

    return {"entries": [{"title":f,"created":t.strftime(ISOSTRFTIME)} for f,t in entries]}

def render_content(content, script=""):
    with open("templates/page.html") as f:
        return f.read().format(content=content, script=script)

def render_entry(content_folder, html_folder, name):
    raw_content = read_file(os.path.join(content_folder, name))
    write_file(os.path.join(html_folder,"entries",name), render_content(raw_content))

def write_entry(content_folder, html_folder, name, content):
    write_file(os.path.join(content_folder, name), content)
    write_file(os.path.join(html_folder, "entries", name), render_content(content))

def write_file(path ,content):
    with open(path, "w") as f:
        f.write(content)

def read_file(path):
    with open(path) as f:
        return f.read() 

def read_content(folder, name):
    return {
            "title": name,
            "content": read_file(os.path.join(folder, name))
        }

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
            auth = query_parameters.get("token")[0]
            assert auth == SERVER_TOKEN
        except (TypeError, AssertionError):
            start_response("403 ACCESS DENIED", [])
            return [b""]

        try:
            data = json.loads(env["wsgi.input"].read(int(env["CONTENT_LENGTH"])))
            write_entry(CONTENT_FOLDER, HTML_FOLDER, data["title"], data["content"])
        except (json.JSONDecodeError, KeyError, TypeError):
            status = "400 BAD REQUEST"
            data = {"message": "Bad data posted POSTed"}

    elif env["REQUEST_METHOD"] == "PUT":
        try:
            destination = env["PATH_INFO"]
            data = json.loads(env["wsgi.input"].read(int(env["CONTENT_LENGTH"])))
            write_entry(CONTENT_FOLDER, HTML_FOLDER, destination, data["content"])
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
        try:
            auth = query_parameters.get("token")[0]
            assert auth == SERVER_TOKEN
        except (TypeError, AssertionError):
            start_response("403 ACCESS DENIED", [])
            return [b""]

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

os.makedirs(os.path.join(HTML_FOLDER,"entries"), exist_ok=True)

with open(os.path.join(HTML_FOLDER,"index.html"),"w") as f:
    with open("js/home.js") as script_file:
        script = script_file.read()
    f.write(render_content("<ul id=\"posts\"></ul>",script))

for entry in os.listdir(CONTENT_FOLDER):
    render_entry(CONTENT_FOLDER, HTML_FOLDER, entry)

with make_server("", PORT, cms) as httpd:
    httpd.serve_forever()
