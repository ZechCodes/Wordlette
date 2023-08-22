# Wordlette 0.1.0-alpha.3

> ⚠️ This is alpha software. It is not currently intended for production use.

Simple and easy content management system that anyone can use.

## Usage

At this time `wordlette.core` is the only thing that is functional. It requires a bit of setup to get working. There is
a [demo](demos/core) that provides a very basic working example. Clone this repo and install the dependencies using
poetry:

```bash
poetry install
```

Then run the demo:

```bash
uvicorn demos.core.app:app
```

It should be accessible at [localhost:8000](http://localhost:8000).