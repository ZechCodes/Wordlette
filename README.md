# Wordlette 0.1.0-alpha.11

> ⚠️ This is alpha software. It is not currently intended for production use.

Simple and easy content management system that anyone can use.

## Usage

Currently, there is only a simple setup process for the CMS. And a basic hello world landing page once it's all
configured.

To run it just follow these steps:

```bash
pip install wordlette[cms]
wordlette serve
```

That'll start a uvicorn server on [localhost:8000](HTTP://localhost:8000).

You can use the `--debug` (or `-d`) flag to enable debug mode. This currently only gives you stacktraces on error pages.
