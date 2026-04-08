"""
Client for the Customer Support Inbox Automation environment.
"""

from openenv.core.env_client import EnvClient
from models import SupportAction, SupportObservation, SupportState


class SupportEnv(EnvClient[SupportAction, SupportObservation]):
    """
    Client for connecting to a running SupportEnvironment server.

    Usage (async):
        async with SupportEnv(base_url="https://your-hf-space.hf.space") as env:
            obs = await env.reset(task_id="easy")
            result = await env.step(SupportAction(action_type="classify", category="complaint"))

    Usage (sync):
        with SupportEnv(base_url="...").sync() as env:
            obs = env.reset(task_id="medium")
            result = env.step(SupportAction(...))
    """

    action_type = SupportAction
    observation_type = SupportObservation
    state_type = SupportState
