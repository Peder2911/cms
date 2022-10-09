
# CMS

This is a very simple "CMS" application that serves content you post.

## Run

```
CMS_SERVER_TOKEN=mysecret python3.10 cms.py
```

## Try

Use `httpie`:

```
>>> http :8000
{"entries":[]}
```

```
>>> http -j :8000?token=mysecret content="My new blog post" title="A post"
{"title":"A post", "content": "My new blog post"}
```

```
>>> http :8000
{"entries":[{"title":"A post", "created":"..."}]}
```

```
>>> http ":8000/A post"
{"title":"A post", "content": "My new blog post"}
```

## Serve

Serve the www/html, www/css and www/js folders. If using Nginx, use the provided default.conf file.
