"""Initial schema

Revision ID: 1fecbf371e15
Revises:
Create Date: 2025-11-01 12:11:47.382527

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1fecbf371e15"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Table: accounts
    op.create_table(
        "accounts",
        sa.Column("id", sa.Text(), nullable=False, primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("base_currency", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint("base_currency = 'USD'", name="check_base_currency_usd"),
    )

    # Table: symbols
    op.create_table(
        "symbols",
        sa.Column(
            "id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True
        ),
        sa.Column("conid", sa.Integer(), nullable=False, unique=True),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("sec_type", sa.Text(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("exchange", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("multiplier", sa.REAL(), nullable=True),
        sa.Column("expiry", sa.Text(), nullable=True),
        sa.Column("strike", sa.REAL(), nullable=True),
        sa.Column("right", sa.Text(), nullable=True),
        sa.Column("underlying_conid", sa.Integer(), nullable=True),
        sa.Column("local_symbol", sa.Text(), nullable=True),
        sa.Column("primary_exchange", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint("currency = 'USD'", name="check_currency_usd"),
    )
    op.create_index("ix_symbols_symbol_sec_type", "symbols", ["symbol", "sec_type"])

    # Table: positions
    op.create_table(
        "positions",
        sa.Column(
            "id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True
        ),
        sa.Column("account_id", sa.Text(), nullable=False),
        sa.Column("symbol_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.REAL(), nullable=False),
        sa.Column("market_price", sa.Integer(), nullable=True),
        sa.Column("market_value", sa.Integer(), nullable=True),
        sa.Column("avg_cost", sa.Integer(), nullable=True),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("unrealized_pnl", sa.Integer(), nullable=True),
        sa.Column("realized_pnl", sa.Integer(), nullable=True),
        sa.Column("snapshot_ts", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("currency = 'USD'", name="check_positions_currency_usd"),
        sa.UniqueConstraint(
            "account_id",
            "symbol_id",
            "snapshot_ts",
            name="uq_positions_account_symbol_snapshot",
        ),
    )
    op.create_index(
        "ix_positions_account_snapshot", "positions", ["account_id", "snapshot_ts"]
    )
    op.create_index(
        "ix_positions_symbol_snapshot", "positions", ["symbol_id", "snapshot_ts"]
    )

    # Table: executions
    op.create_table(
        "executions",
        sa.Column(
            "id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True
        ),
        sa.Column("account_id", sa.Text(), nullable=False),
        sa.Column("symbol_id", sa.Integer(), nullable=False),
        sa.Column("exec_id", sa.Text(), nullable=False, unique=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("quantity", sa.REAL(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("commission_amount", sa.Integer(), nullable=True),
        sa.Column("commission_currency", sa.Text(), nullable=True),
        sa.Column("fee_amount", sa.Integer(), nullable=True),
        sa.Column("exchange", sa.Text(), nullable=True),
        sa.Column("liquidity", sa.Text(), nullable=True),
        sa.Column("order_ref", sa.Text(), nullable=True),
        sa.Column("execution_type", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.Text(), nullable=False),
        sa.Column("ingested_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("side IN ('BUY', 'SELL')", name="check_executions_side"),
        sa.CheckConstraint("currency = 'USD'", name="check_executions_currency_usd"),
    )
    op.create_index(
        "ix_executions_account_executed", "executions", ["account_id", "executed_at"]
    )
    op.create_index(
        "ix_executions_symbol_executed", "executions", ["symbol_id", "executed_at"]
    )

    # Table: cash_transactions
    op.create_table(
        "cash_transactions",
        sa.Column(
            "id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True
        ),
        sa.Column("account_id", sa.Text(), nullable=False),
        sa.Column("symbol_id", sa.Integer(), nullable=True),
        sa.Column("txn_date", sa.Text(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("fx_rate_used", sa.Integer(), nullable=True),
        sa.Column("base_amount", sa.Integer(), nullable=True),
        sa.Column("source_id", sa.Text(), nullable=True),
        sa.Column("ingested_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["symbol_id"], ["symbols.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "currency = 'USD'", name="check_cash_transactions_currency_usd"
        ),
    )
    # Create unique index using COALESCE to handle NULL source_id
    # This ensures deduplication at database level:
    # - When source_id IS provided: dedupe by (account_id, txn_date, amount, type, source_id)
    # - When source_id IS NULL: dedupe by (account_id, txn_date, amount, type) with empty string
    op.execute(
        """
        CREATE UNIQUE INDEX uq_cash_transactions_compound
        ON cash_transactions(account_id, txn_date, amount, type, COALESCE(source_id, ''))
        """
    )
    op.create_index(
        "ix_cash_transactions_account_date",
        "cash_transactions",
        ["account_id", "txn_date"],
    )
    op.create_index("ix_cash_transactions_type", "cash_transactions", ["type"])

    # Table: account_summaries
    op.create_table(
        "account_summaries",
        sa.Column(
            "id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True
        ),
        sa.Column("account_id", sa.Text(), nullable=False),
        sa.Column("net_liquidation", sa.Integer(), nullable=True),
        sa.Column("cash_balance", sa.Integer(), nullable=True),
        sa.Column("gross_position_value", sa.Integer(), nullable=True),
        sa.Column("maintenance_margin", sa.Integer(), nullable=True),
        sa.Column("initial_margin", sa.Integer(), nullable=True),
        sa.Column("excess_liquidity", sa.Integer(), nullable=True),
        sa.Column("buying_power", sa.Integer(), nullable=True),
        sa.Column("realized_pnl_period", sa.Integer(), nullable=True),
        sa.Column("unrealized_pnl_snapshot", sa.Integer(), nullable=True),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("snapshot_ts", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "currency = 'USD'", name="check_account_summaries_currency_usd"
        ),
        sa.UniqueConstraint(
            "account_id", "snapshot_ts", name="uq_account_summaries_account_snapshot"
        ),
    )
    op.create_index(
        "ix_account_summaries_account_snapshot",
        "account_summaries",
        ["account_id", "snapshot_ts"],
    )

    # Table: sync_log
    op.create_table(
        "sync_log",
        sa.Column(
            "id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True
        ),
        sa.Column("entity", sa.Text(), nullable=False),
        sa.Column("account_id", sa.Text(), nullable=True),
        sa.Column("cursor_from", sa.Text(), nullable=True),
        sa.Column("cursor_to", sa.Text(), nullable=True),
        sa.Column("overlap_sec", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("records_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.Text(), nullable=False),
        sa.Column("completed_at", sa.Text(), nullable=True),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('success', 'partial', 'failed')", name="check_sync_log_status"
        ),
    )
    op.create_index(
        "ix_sync_log_entity_account_started",
        "sync_log",
        ["entity", "account_id", "started_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_sync_log_entity_account_started", table_name="sync_log")
    op.drop_table("sync_log")
    op.drop_index(
        "ix_account_summaries_account_snapshot", table_name="account_summaries"
    )
    op.drop_table("account_summaries")
    op.drop_index("uq_cash_transactions_compound", table_name="cash_transactions")
    op.drop_index("ix_cash_transactions_type", table_name="cash_transactions")
    op.drop_index("ix_cash_transactions_account_date", table_name="cash_transactions")
    op.drop_table("cash_transactions")
    op.drop_index("ix_executions_symbol_executed", table_name="executions")
    op.drop_index("ix_executions_account_executed", table_name="executions")
    op.drop_table("executions")
    op.drop_index("ix_positions_symbol_snapshot", table_name="positions")
    op.drop_index("ix_positions_account_snapshot", table_name="positions")
    op.drop_table("positions")
    op.drop_index("ix_symbols_symbol_sec_type", table_name="symbols")
    op.drop_table("symbols")
    op.drop_table("accounts")
