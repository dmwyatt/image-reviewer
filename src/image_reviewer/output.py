import sys


def log(message: str) -> None:
    """Log a message to stderr."""
    print(message, file=sys.stderr)


def log_error(message: str) -> None:
    """Log an error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)
