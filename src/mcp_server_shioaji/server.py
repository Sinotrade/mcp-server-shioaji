"""MCP Server implementation for Shioaji API integration."""

import datetime
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

import polars as pl
import shioaji as sj
from dotenv import load_dotenv
from loguru import logger
from mcp.server.fastmcp import Context, FastMCP
# from shioaji.constant import ScannerType


@dataclass
class AppContext:
    """Application context holding initialized resources."""

    api: sj.Shioaji


def get_credentials() -> tuple[str, str]:
    """Get API credentials from environment variables."""
    # Load .env file if it exists
    load_dotenv()

    api_key = os.getenv("SHIOAJI_API_KEY")
    secret_key = os.getenv("SHIOAJI_SECRET_KEY")

    if not api_key or not secret_key:
        raise ValueError(
            "Shioaji API credentials not found. "
            "Set SHIOAJI_API_KEY and SHIOAJI_SECRET_KEY environment variables."
        )

    return api_key, secret_key


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage the Shioaji API lifecycle."""
    # Initialize API on startup
    api_key, secret_key = get_credentials()

    # Initialize Shioaji API
    api = sj.Shioaji()

    try:
        logger.info("Logging in to Shioaji API...")
        accounts = api.login(api_key, secret_key)
        logger.info("Successfully logged in to Shioaji API")

        # Yield the API instance in the context
        yield AppContext(api=api)
    except Exception as e:
        logger.error(f"Error initializing Shioaji API: {str(e)}")
        raise
    finally:
        # Clean up on shutdown
        try:
            logger.info("Logging out from Shioaji API...")
            api.logout()
            logger.info("Successfully logged out from Shioaji API")
        except Exception as e:
            logger.error(f"Error during Shioaji API logout: {str(e)}")


# Initialize MCP server with dependencies and lifespan
mcp = FastMCP(
    "Shioaji MCP Server",
    dependencies=["shioaji", "polars", "python-dotenv", "loguru"],
    lifespan=app_lifespan,
)


@mcp.tool(
    name="get_stock_price", description="Get the current price of a stock by its symbol"
)
async def get_stock_price(ctx: Context, symbols: str) -> List[Dict[str, Any]]:
    """
    Get the current price and related information for a stock.

    Args:
        ctx: The tool context containing the API instance
        symbols: The stock symbol separated by commas (e.g., 'TW.2330,TW.2317' for TSMC and HTC)

    Returns:
        Dictionary containing price information
    """

    # Get API from context
    api = ctx.request_context.lifespan_context.api  # type: ignore
    codes = [
        symbol.split(".")[1]
        for symbol in symbols.split(",")
        if symbol.startswith("TW.")
    ]

    contracts = [
        api.Contracts.Stocks[code] for code in codes if api.Contracts.Stocks[code]
    ]
    snapshots = api.snapshots(contracts)

    if not snapshots:
        raise ValueError(f"No data available for stock {codes}")

    df_snapshots = (
        pl.DataFrame([{**s} for s in snapshots])
        .with_columns(pl.from_epoch("ts", time_unit="ns").alias("datetime"))
        .select(pl.exclude("ts"))
    )

    return df_snapshots.to_dicts()


@mcp.tool(
    name="get_kbars", description="Fetch K-Bar data for a stock within a date range"
)
async def get_kbars(
    ctx: Context,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch K-Bar (candlestick) data for a stock within a date range.

    Args:
        ctx: The tool context containing the API instance
        symbol: The stock symbol (e.g., 'TW.2330' for TSMC)
        start_date: The start date in YYYY-MM-DD format (defaults to today)
        end_date: The end date in YYYY-MM-DD format (defaults to start_date if not provided)

    Returns:
        List of K-Bar data entries
    """

    # Get API from context
    api = ctx.request_context.lifespan_context.api  # type: ignore

    if not symbol.startswith("TW."):
        raise ValueError("Symbol only support start with TW.")

    code = symbol.split(".")[1]
    contract = api.Contracts.Stocks[code]

    if not start_date:
        start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # Set end_date to start_date if not provided
    if not end_date:
        end_date = start_date

    # Fetch K-Bar data
    kbars = api.kbars(contract, start=start_date, end=end_date)

    # Process the kbars - adapting to the actual structure returned by shioaji
    df_kbars = (
        pl.DataFrame({**kbars})
        .with_columns(pl.from_epoch("ts", time_unit="ns").alias("datetime"))
        .select(pl.exclude("ts"))
    )

    return df_kbars.to_dicts()


@mcp.tool(
    name="scan_stocks",
    description="根據 scanner_type 掃描股票，並且依照 ascending 排序，回傳前 limit 個股票。",
)
async def scan_stocks(
    ctx: Context,
    scanner_type: str, #ScannerType,
    ascending: bool = False,
    limit: int = 20,
) -> List[Dict[str, str]]:
    """
    根據 scanner_type 掃描股票，並且依照 ascending 排序，回傳前 limit 個股票。
    支援的 scanner_type 有：
    - VolumeRank 成交量排名
    - AmountRank 成交金額排名
    - TickCountRank 成交筆數排名
    - ChangePercentRank 漲幅排名
    - ChangePriceRank 漲跌價排名
    - DayRangeRank 日振幅排名

    Args:
        ctx: The tool context containing the API instance
        scanner_type: The type of scanner to use (VolumeRank, AmountRank, TickCountRank, ChangePercentRank, ChangePriceRank, DayRangeRank)
        ascending: Whether to sort in ascending order (default: False)
        limit: Maximum number of stocks to return (default: 20)

    Returns:
        List of stock information
    """
    # Get API from context
    api = ctx.request_context.lifespan_context.api  # type: ignore
    res = api.scanners(scanner_type, ascending=ascending, count=limit)
    df = (
        pl.DataFrame([{**r} for r in res])
        .with_columns(pl.from_epoch("ts", time_unit="ns").alias("datetime"))
        .select(pl.exclude("ts"))
    )
    return df.to_dicts()


def start_server(transport: Literal["stdio", "sse"] = "stdio"):
    """Start the MCP server."""

    logger.info(f"Starting MCP server on {transport}")
    mcp.run(transport=transport)
