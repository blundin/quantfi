"""CLI interface for data sync and validation.

Commands:
    sync --from <date> --to <date>  Incremental sync by time window
    status                          Show sync status and last update times
    validate                        Run data validation checks
"""

import click


@click.group()
def cli():
    """QuantFi CLI - Portfolio tracking and data sync."""
    pass


@cli.command()
@click.option("--from", "from_date", help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", help="End date (YYYY-MM-DD)")
def sync(from_date, to_date):
    """Incremental sync by time window."""
    click.echo("Sync command - not yet implemented")


@cli.command()
def status():
    """Show sync status and last update times."""
    click.echo("Status command - not yet implemented")


@cli.command()
def validate():
    """Run data validation checks."""
    click.echo("Validate command - not yet implemented")


if __name__ == "__main__":
    cli()

