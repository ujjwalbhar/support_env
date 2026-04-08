"""
FastAPI server app for Customer Support Inbox Automation environment.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server import create_fastapi_app
from models import SupportAction, SupportObservation
from server.support_environment import SupportEnvironment

env = SupportEnvironment()

app = create_fastapi_app(env, SupportAction, SupportObservation)
