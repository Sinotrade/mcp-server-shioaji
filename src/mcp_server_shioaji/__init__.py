def main() -> None:
    """Entry point for the mcp-server-shioaji package."""
    from .server import start_server

    start_server()


__all__ = ["main"]
