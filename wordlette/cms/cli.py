def run():
    import sys

    match (*map(str.casefold, sys.argv),):
        case (_, "serve", *args):
            _start_server(debug="--debug" in args or "-d" in args)

        case _:
            raise RuntimeError("Invalid command")


def _start_server(**settings):
    from wordlette.cms.app_bootstrap import create_app
    import uvicorn

    uvicorn.run(create_app(**settings), port=8000, log_level="info")
