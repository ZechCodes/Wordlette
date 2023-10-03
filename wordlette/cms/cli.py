from wordlette.users.auth_security_levels import AuthSecurityLevel


def run():
    import sys

    match (*map(str.casefold, sys.argv),):
        case (_, "serve", *args):
            settings = {}
            if "--debug" in args or "-d" in args:
                settings["debug"] = True

            if "--auth-security-level" in args:
                index = args.index("--auth-security-level")
                security_level = getattr(
                    AuthSecurityLevel, args[index + 1].upper(), None
                )
                if security_level is None:
                    raise RuntimeError("Invalid security level")

                settings["min_auth_security_level"] = security_level

            _start_server(**settings)

        case _:
            raise RuntimeError("Invalid command")


def _start_server(**settings):
    from wordlette.cms.app_bootstrap import create_app
    import uvicorn

    uvicorn.run(create_app(**settings), port=8000, log_level="info")
