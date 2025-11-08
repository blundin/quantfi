"""CLI interface for data sync and validation.

Commands:
    sync [--account-id ACCOUNT_ID]  Sync positions from IBKR Web API
    status                          Show sync status and last update times
    validate                        Run data validation checks
"""

import os

import click
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv

from src.api_client import (
    APIError,
    AuthenticationError,
    IBKRAPIClient,
    NetworkError,
)
from src.database import Database
from src.sync import sync_positions

# Load environment variables
load_dotenv()


def ensure_database_initialized(db_path: str) -> None:
    """Ensure database schema is initialized using Alembic.

    Args:
        db_path: Path to database file
    """
    # Check if database exists and has tables
    if os.path.exists(db_path):
        try:
            from src.database import Database

            db = Database(db_path=db_path, encryption_key=None)
            with db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='accounts'"
                )
                if cursor.fetchone():
                    # Database already initialized
                    return
        except Exception:
            # Database exists but may not be initialized
            pass

    # Run Alembic migrations
    click.echo("Initializing database schema...")
    alembic_config = Config("alembic.ini")
    db_path_absolute = os.path.abspath(db_path)
    sqlalchemy_url = f"sqlite:///{db_path_absolute}"
    alembic_config.set_main_option("sqlalchemy.url", sqlalchemy_url)
    command.upgrade(alembic_config, "head")
    click.echo("✓ Database schema initialized")


@click.group()
def cli():
    """QuantFi CLI - Portfolio tracking and data sync."""
    pass


@cli.command()
@click.option(
    "--account-id",
    help="IB account ID (e.g., U1234567). "
    "If not provided, uses IBKR_ACCOUNT_ID from .env",
)
def sync(account_id: str | None):
    """Sync positions from IBKR Web API to database.

    Fetches current positions from the API and saves them to the database.
    Automatically creates Symbol records if they don't exist.
    """
    # Get account ID from parameter or environment
    if not account_id:
        account_id = os.getenv("IBKR_ACCOUNT_ID")
        if not account_id:
            click.echo(
                "Error: Account ID required. "
                "Provide --account-id or set IBKR_ACCOUNT_ID in .env",
                err=True,
            )
            return

    # Get database path and encryption key from environment
    db_path = os.getenv("DB_PATH", "data/portfolio.db")
    db_key = os.getenv("DB_ENCRYPTION_KEY")

    if not db_key:
        click.echo(
            "Warning: DB_ENCRYPTION_KEY not set. Using unencrypted database.",
            err=True,
        )

    try:
        # Ensure database is initialized
        ensure_database_initialized(db_path)

        # Initialize database
        database = Database(db_path=db_path, encryption_key=db_key)

        # Initialize API client
        api_client = IBKRAPIClient()

        # Check session with tickle
        click.echo("Checking gateway connection...")
        try:
            api_client.tickle()
            click.echo("✓ Gateway connected and session active")
        except (AuthenticationError, NetworkError) as e:
            click.echo(f"✗ Gateway error: {str(e)}", err=True)
            return

        # Sync positions
        click.echo(f"Syncing positions for account {account_id}...")
        result = sync_positions(database, account_id, api_client)

        # Display results
        if result["status"] == "success":
            click.echo(
                f"✓ Successfully synced {result['positions_saved']} positions"
            )
        elif result["status"] == "partial":
            click.echo(
                f"⚠ Partially synced: {result['positions_saved']}/"
                f"{result['positions_fetched']} positions saved"
            )
            if result["errors"]:
                click.echo("Errors:", err=True)
                for error in result["errors"]:
                    click.echo(f"  - {error}", err=True)
        else:
            click.echo("✗ Sync failed", err=True)
            if result["errors"]:
                for error in result["errors"]:
                    click.echo(f"  - {error}", err=True)

    except (AuthenticationError, NetworkError, APIError) as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        return
    except Exception as e:
        click.echo(f"✗ Unexpected error: {str(e)}", err=True)
        raise


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

