"""Entry point for Riddit API server."""

import uvicorn
from riddit.main import app


def main():
    """Run the Riddit API server."""
    uvicorn.run("riddit.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
