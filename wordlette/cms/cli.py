def run():
    import sys

    match sys.argv:
        case [_, "serve"]:
            _start_server()

        case _:
            raise RuntimeError("Invalid command")


def _start_server():
    from wordlette.cms.app import app
    import uvicorn

    uvicorn.run(app, port=8000, log_level="info")
