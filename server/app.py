"""
FastAPI server for Customer Support Inbox Automation environment.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server import create_app
from models import SupportAction, SupportObservation
from server.support_environment import SupportEnvironment


def create_env():
    """Factory function — creates a fresh SupportEnvironment per session."""
    return SupportEnvironment()


app = create_app(
    create_env,
    SupportAction,
    SupportObservation,
    env_name="support_env",
)


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
