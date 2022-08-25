from wordlette.app import App
from wordlette.exceptions import (
    WordletteHostAndPortRequired,
    WordlettePortMustBeAnInteger,
    WordletteException,
)
import click


@click.command()
@click.option(
    "--extension",
    "-e",
    multiple=True,
    help="Extensions packages that should be imported & loaded at runtime.",
)
@click.argument("host_port")
def launch(extension: tuple[str], host_port: str):
    try:
        host, port = _split_host_port(host_port)
        _show_launch_settings(host, port, extension)
    except WordletteException as exception:
        _show_error_message(exception.args[0])
    else:
        App.start(host=host, port=port, extensions=extension)


def _show_error_message(message: str):
    click.echo(f"Something went wrong:\n")
    click.echo(
        click.wrap_text(
            message,
            60,
            initial_indent="  ",
            subsequent_indent="  ",
        )
    )


def _show_launch_settings(host: str, port: int, extensions: tuple[str, ...]):
    click.echo(f"Starting your a server\n    Host: {host}\n    Port: {port}")
    if extensions:
        click.echo(f"    Extensions:")
        for extension in extensions:
            click.echo(f"    - {extension}")


def _split_host_port(host_port: str) -> tuple[str, int]:
    split = host_port.rsplit(":", maxsplit=1)
    if len(split) != 2:
        raise WordletteHostAndPortRequired(
            "You must provide both a host & port that the server should listen on."
        )

    elif not split[1].isdigit():
        raise WordlettePortMustBeAnInteger(
            f"You must provide an integer port, got {split[1]!r}."
        )

    return split[0], int(split[1])
