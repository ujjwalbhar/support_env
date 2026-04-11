"""
Customer Support Inbox Automation Environment.
Implements the OpenEnv Environment interface.
"""
import uuid
import random
from typing import Optional

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SupportAction, SupportObservation, SupportState
from tasks import TASKS, get_task_emails, get_task_description
from graders import grade_easy, grade_medium, grade_hard, sanitize_reward


class SupportEnvironment(Environment):
    """
    Customer Support Inbox Automation RL Environment.
    An AI agent processes incoming customer support emails and must:
    - Easy:   Classify the email into the correct category
    - Medium: Classify + generate a professional response
    - Hard:   Multi-step: classify -> respond -> escalate or resolve
    Reward range: strictly inside (0.0, 1.0) - never equal to endpoints.
    """
    SUPPORTS_CONCURRENT_SESSIONS = False

    def __init__(self):
        self._episode_id: str = str(uuid.uuid4())
        self._step_count: int = 0
        self._current_task: str = "easy"
        self._email_index: int = 0
        self._emails: list = []
        self._hard_step: int = 1
        self._cumulative_reward: float = 0.0
        self._current_email: Optional[dict] = None
        self._classification_done: bool = False
        self._response_done: bool = False

    # ------------------------------------------------------------------
    # reset()
    # ------------------------------------------------------------------
    def reset(self, task_id: str = "easy") -> SupportObservation:
        """
        Start a new episode. task_id: 'easy', 'medium', or 'hard'.
        """
        valid_tasks = ["easy", "medium", "hard"]
        if task_id not in valid_tasks:
            task_id = "easy"

        self._episode_id = str(uuid.uuid4())
        self._step_count = 0
        self._current_task = task_id
        self._emails = get_task_emails(task_id)
        random.shuffle(self._emails)
        self._email_index = 0
        self._current_email = self._emails[self._email_index]
        self._hard_step = 1
        self._cumulative_reward = 0.0
        self._classification_done = False
        self._response_done = False

        description = get_task_description(task_id)
        return SupportObservation(
            email_id=self._current_email["id"],
            email_subject=self._current_email["subject"],
            email_body=self._current_email["body"],
            customer_name=self._current_email["customer_name"],
            customer_tier=self._current_email["customer_tier"],
            previous_interactions=self._current_email["previous_interactions"],
            current_category=None,
            action_feedback=(
                f"New episode started. Task: {task_id.upper()}. "
                f"Description: {description} "
                f"Email {self._email_index + 1} of {len(self._emails)}."
            ),
            task_complete=False,
            reward=0.005,  # safe non-zero initial reward strictly inside (0, 1)
            task_id=task_id,
        )

    # ------------------------------------------------------------------
    # step()
    # ------------------------------------------------------------------
    def step(self, action: SupportAction) -> SupportObservation:
        self._step_count += 1
        action_dict = action.model_dump()
        reward = 0.0
        feedback = ""
        task_complete = False
        email = self._current_email

        # ---- Route to correct grader ----
        if self._current_task == "easy":
            reward, feedback = grade_easy(action_dict, email)
            task_complete = True
        elif self._current_task == "medium":
            reward, feedback = grade_medium(action_dict, email)
            task_complete = True
        elif self._current_task == "hard":
            reward, feedback = grade_hard(action_dict, email, step=self._hard_step)
            if self._hard_step == 1 and action_dict.get("action_type") == "classify":
                self._hard_step = 2
                self._classification_done = True
            elif self._hard_step == 2 and action_dict.get("action_type") == "respond":
                self._hard_step = 3
                self._response_done = True
            elif self._hard_step == 3 and action_dict.get("action_type") in ("escalate", "resolve"):
                task_complete = True

        # Sanitize reward to ensure it is strictly inside (0.0, 1.0)
        reward = sanitize_reward(reward)
        self._cumulative_reward += reward

        # ---- Advance to next email if task is complete ----
        category = action_dict.get("category") or email.get("current_category")
        if task_complete:
            self._email_index += 1
            if self._email_index < len(self._emails):
                self._current_email = self._emails[self._email_index]
                self._hard_step = 1
                self._classification_done = False
                self._response_done = False
                feedback += (
                    f" Moving to email {self._email_index + 1} of {len(self._emails)}."
                )
            else:
                feedback += " All emails processed. Episode complete!"

        return SupportObservation(
            email_id=self._current_email["id"],
            email_subject=self._current_email["subject"],
            email_body=self._current_email["body"],
            customer_name=self._current_email["customer_name"],
            customer_tier=self._current_email["customer_tier"],
            previous_interactions=self._current_email["previous_interactions"],
            current_category=category,
            action_feedback=feedback,
            task_complete=task_complete,
            reward=round(reward, 3),
            task_id=self._current_task,
        )

    # ------------------------------------------------------------------
    # state()
    # ------------------------------------------------------------------
    @property
    def state(self) -> SupportState:
        return SupportState(
            episode_id=self._episode_id,
            step_count=self._step_count,
            current_task=self._current_task,
            emails_processed=self._email_index,
            total_reward=round(self._cumulative_reward, 3),
        )
