# Wordlette 0.1.0-alpha.2

> ⚠️ This is alpha software. It is not currently intended for production use.

Simple and easy content management system that anyone can use.

## Usage

You can start a Wordlette server by using this command:
```shell
python -m wordlette localhost:8000
```
It will auto-import every `.py`, `.pyc`, and folder that has a `__init__.py` file that is found inside of the `pages` folder It will scan each module and package that is imported for classes that inherit from `wordlette.pages.Page`.

So you should have a file structure something like this
```
- root-folder
  - pages
    - index.py
    - blog.py
```
You'll run Wordlette from `root-folder` and it will auto-import `index.py` & `blog.py` from the `pages` folder. The `pages` folder will itself be treated as a package.

For each page that is needed you'll create a class that inherits from `wordlette.pages.Page`.
```python
from wordlette.pages import Page

class Blog(Page):
    path = "/blog"

    async def response(self) -> str:
        return "<h1>Blog</h1><p>Welcome to my blog!</p>"


class BlogPost(Page):
    path = "/blog/{post_id:int}"

    async def response(self, post_id: int) -> str:
        return f"<h1>Post {post_id}</h1><p>This is post {post_id}!</p>"
```
Errors can be handled by creating functions that follow the naming convention `on*_error*` where `*` is 0 or more characters. `on` must be followed by an underscore and `error` must be proceeded & followed by an underscore, unless there's nothing before/after it. So `on_error`, `on_error_response`, and `on_validation_error_response` would all be valid. Wordlette will check each error handler for a parameter named `error`, it will use its type annotation to determine what type of exceptions this handler can work with. This will even support union types.  
```python
from starlette.responses import HTMLResponse
from wordlette.pages import Page

class Blog(Page):
    path = "/blog"
    
    async def response(self) -> str:
        ...

    async def on_error(self, error: Exception) -> str:
        """Handle all exceptions."""
        return HTMLResponse(
            f"<h1>500 {type(error).__name__}</h1><p>{error.args[0]}</p>",
            status_code=500
        )
```