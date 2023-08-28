# Wordlette 0.1.0-alpha.8

> ⚠️ This is alpha software. It is not currently intended for production use.

Simple and easy content management system that anyone can use.

## Usage

Currently `wordlette.core` is all that is fully functional. It requires a bit of setup to get working. There is
a [demo](https://github.com/ZechCodes/Wordlette/tree/main/demos/core) that provides a very basic working example. Clone
this repo and install the dependencies using
poetry:

```bash
poetry install
```

Then run the demo:

```bash
uvicorn demos.core.app:app
```

It should be accessible at [localhost:8000](http://localhost:8000).

### Wordlette CMS

The Wordlette CMS has been started but has no functionality. If you'd like to launch it and see what is there you just
need to install wordlette and use its script entry point to start the server.

```bash
pip install wordlette[cms]
wordlette serve
```

That'll start a uvicorn server on [localhost:8000](HTTP://localhost:8000).

You can use the `--debug` (or `-d`) flag to enable debug mode. This currently only gives you stacktraces on 500 error
pages in the CMS.

```bash
