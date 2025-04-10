import click

token_option = click.option(
    "--token",
    help=(
        "API token - if not provided, will be read from "
        "ONYX_API_TOKEN environment variable and the .env file"
    ),
    type=str,
)


url_option = click.option(
    "--url",
    help=(
        "Websocket API url - if not provided, will be read from "
        "ONYX_WS_V2_URL environment variable and the .env file"
    ),
    type=str,
)
