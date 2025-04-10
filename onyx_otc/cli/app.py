import logging

import click
import dotenv

import onyx_otc

from .stream import stream

dotenv.load_dotenv()


@click.group()
@click.version_option(onyx_otc.__version__)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging",
)
def cli(debug: bool) -> None:
    """Command line interface for onyx-otc."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")


cli.add_command(stream)


if __name__ == "__main__":
    cli()
