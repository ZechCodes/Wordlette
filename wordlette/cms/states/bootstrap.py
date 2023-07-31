from bevy import dependency, inject
from starlette.responses import HTMLResponse

from wordlette.middlewares.state_router import RouteManager
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.state_machines import State


class BootstrapIndex(Route):
    path = "/"

    async def index(self, _: Request.Get):
        return HTMLResponse(
            """
            <doctype html>
            <html lang="en">
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                    <title>Hello from Wordlette!</title>
                    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic">
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.css">
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/milligram/1.4.1/milligram.css">
                    <style>
                    .header {
                        padding: 100pt 0 20pt 0;
                        background: rgb(115,0,255);
                        background: linear-gradient(90deg, rgba(115,0,255,1) 0%, rgba(81,0,221,1) 40%, rgba(80,0,179,1) 100%);
                        color: #fff;
                        margin-bottom: 40pt;
                    }
                    h1, h3 {
                        padding: 0 60pt;
                    }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div class="container">    
                            <div class="row">
                                <div class="column">
                                    <h1>Hello!</h1>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="container">
                        <div class="row">
                            <div class="column">
                                <h3>Please standby, <i>Wordlette</i> will be ready momentarily.</h3>
                            </div>
                        </div>
                    </div>
                </body>
            </html>
            """
        )


class BootstrapState(State):
    @inject
    async def enter_state(self, router: RouteManager = dependency()):
        router.add_route(BootstrapIndex)
        return self.cycle()
