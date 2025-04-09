import click
import dotenv

dotenv.load_dotenv()  # isort skip

from .stream import stream  # noqa: E402


@click.group()
def cli() -> None:
    """Onyx OTC CLI."""
    pass


cli.add_command(stream)


if __name__ == "__main__":
    cli()
