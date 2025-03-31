# MCP Server for Shioaji

A Model Context Protocol (MCP) server that provides AI assistants with access to Shioaji trading API for the Taiwanese financial market.

## Overview

This server implements the MCP protocol to expose Shioaji API functionality as tools that can be used by AI assistants. It allows AI models to:

- Retrieve current stock prices
- Fetch historical data
- List available stocks
- And more...

## Installation

### Prerequisites

- Python 3.10 or higher
- uv (fast Python package manager)

### Using uv

```bash
uv sync
```

## Configuration

Before running the server, you need to configure your Shioaji API credentials. There are two ways to do this:

### Environment Variables

Set the following environment variables:

```bash
export SHIOAJI_API_KEY="your_api_key"
export SHIOAJI_SECRET_KEY="your_secret_key"
```

### Using .env File

Create a `.env` file in the root directory with the following content:

```
SHIOAJI_API_KEY=your_api_key
SHIOAJI_SECRET_KEY=your_secret_key
```

## Running the Server

Start the server with:

```bash
uv run mcp-server-shioaji
```

The server will start on `http://0.0.0.0:8000` by default.

## Available Tools

The server exposes the following tools via MCP:

### get_stock_price

Get the current price of a stock by its symbol.

```json
{
  "tool": "get_stock_price",
  "params": {
    "symbols": "TW.2330,TW.2317"
  }
}
```

Response will include price information for the requested stocks, including open, high, low, close prices, volume, and other trading data.


### get_kbars

Fetch K-Bar (candlestick) data for a stock within a date range.

```json
{
  "tool": "get_kbars",
  "params": {
    "symbol": "TW.2330",
    "start_date": "2023-12-01",
    "end_date": "2023-12-15"
  }
}
```

If `start_date` is not provided, it defaults to today. If `end_date` is not provided, it defaults to the same as `start_date`.


### scan_stocks

Scan stocks based on various ranking criteria.

```json
{
  "tool": "scan_stocks",
  "params": {
    "scanner_type": "VolumeRank",
    "ascending": false,
    "limit": 10
  }
}
```

Supported scanner types:
- `VolumeRank` - Ranking by trading volume
- `AmountRank` - Ranking by trading amount
- `TickCountRank` - Ranking by number of transactions
- `ChangePercentRank` - Ranking by percentage change
- `ChangePriceRank` - Ranking by price change
- `DayRangeRank` - Ranking by daily range

Default limit is 20, and results are sorted in descending order by default (set `ascending` to `true` for ascending order).

## Development

### Project Structure

```
mcp-server-shioaji/
├── src/
│   └── mcp_server_shioaji/
│       ├── __init__.py      # Package entry point
│       └── server.py        # MCP server implementation
├── pyproject.toml           # Project metadata and dependencies
└── README.md                # This file
```

### Adding New Tools

To add new Shioaji functionality, modify `server.py` and add new tool definitions using the `@mcp.tool` decorator.

## License

MIT

## Acknowledgements

- [Shioaji](https://sinotrade.github.io/) - The Python wrapper for SinoPac's trading API
- [MCP](https://github.com/pfnet/mcp) - Model Context Protocol