from pathlib import Path

from bevy import inject, dependency, get_repository
from starlette.responses import HTMLResponse

from wordlette.configs.managers import ConfigManager
from wordlette.middlewares.state_router import RouteManager
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.state_machines import State


class ConfigNotFoundPage(Route):
    path = "/"

    @inject
    async def index(self, _: Request.Get, config: ConfigManager = dependency()):
        files = "\n".join(
            f"<li><code>{LoadingConfig.config_file_name}.{ext}</code></li>"
            for ext in sorted(config.valid_extensions)
        )
        return HTMLResponse(
            f"""
            <doctype html>
            <html lang="en">
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                    <title>Wordlette Config Not Found</title>
                    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic">
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.css">
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/milligram/1.4.1/milligram.css">
                    <style>
                    .header {{
                        padding: 100pt 0 20pt 0;
                        background: rgb(115,0,255);
                        background: linear-gradient(90deg, rgba(115,0,255,1) 0%, rgba(81,0,221,1) 40%, rgba(80,0,179,1) 100%);
                        color: #fff;
                        margin-bottom: 40pt;
                    }}
                    h1, h3, p, ul {{
                        padding: 0 60pt;
                    }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div class="container">    
                            <div class="row">
                                <div class="column">
                                    <h1>Config Not Found</h1>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="container">
                        <div class="row">
                            <div class="column">
                                <h3><i>Wordlette</i> could not find a valid config file.</h3>
                                <p>Please create a config file in the the working directory.</p>
                                <p>Working Directory: <code>{Path().cwd()}</code></p>
                                <p>Looking for any of these settings files:</p>
                                <ul>
                                    {files}
                                </ul>
                            </div>
                        </div>
                    </div>
                </body>
            </html>
            """
        )


class LoadingConfig(State):
    config_file_name = "wordlette.settings"

    @inject
    async def enter_state(self, config: ConfigManager = dependency()):
        if await self.config_found():
            config.load_config_file(self.config_file_name, Path())
            return self.cycle()

        get_repository().find(RouteManager).value.create_router(ConfigNotFoundPage)

    @classmethod
    @inject
    async def config_found(cls, config: ConfigManager = dependency()) -> bool:
        return config.find_config_file(cls.config_file_name, Path()) is not None
