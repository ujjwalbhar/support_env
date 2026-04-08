"""
inference.py - Baseline inference script for Customer Support Inbox Automation environment.

IMPORTANT: This script emits structured stdout logs in [START], [STEP], [END] format
as required by the hackathon evaluation system. Any deviation will break scoring.

Usage:
    python inference.py

Environment variables required:
    API_BASE_URL  - LLM API endpoint
    MODEL_NAME    - Model identifier
    HF_TOKEN      - Hugging Face / API key
    SPACE_URL     - HF Spaces URL of your deployed environment (optional, defaults to local)
"""

import os
import sys
import json
import time
import asyncio
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# -----------------------------------------------------------------------
# Configuration — loaded from environment variables
# -----------------------------------------------------------------------
API_BASE_URL: str = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME: str = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN: str = os.environ.get("HF_TOKEN", "")
SPACE_URL: str = os.environ.get(
    "SPACE_URL", "http://localhost:7860"
)

# Initialise OpenAI-compatible client
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN if HF_TOKEN else "dummy-key",
)

# -----------------------------------------------------------------------
# Logging helpers — strict format required by the evaluation system
# -----------------------------------------------------------------------

def log_start(task_id: str, episode: int, email_id: str, email_subject: str) -> None:
    """Emit a [START] log line."""
    record = {
        "event": "START",
        "task_id": task_id,
        "episode": episode,
        "email_id": email_id,
        "email_subject": email_subject,
        "timestamp": time.time(),
    }
    print(f"[START] {json.dumps(record)}", flush=True)


def log_step(
    task_id: str,
    episode: int,
    step: int,
    email_id: str,
    action_type: str,
    reward: float,
    feedback: str,
) -> None:
    """Emit a [STEP] log line."""
    record = {
        "event": "STEP",
        "task_id": task_id,
        "episode": episode,
        "step": step,
        "email_id": email_id,
        "action_type": action_type,
        "reward": reward,
        "feedback": feedback,
        "timestamp": time.time(),
    }
    print(f"[STEP] {json.dumps(record)}", flush=True)


def log_end(
    task_id: str,
    episode: int,
    total_reward: float,
    emails_processed: int,
    success: bool,
) -> None:
    """Emit an [END] log line."""
    record = {
        "event": "END",
        "task_id": task_id,
        "episode": episode,
        "total_reward": total_reward,
        "emails_processed": emails_processed,
        "success": success,
        "timestamp": time.time(),
    }
    print(f"[END] {json.dumps(record)}", flush=True)


# -----------------------------------------------------------------------
# LLM agent — calls the model to decide what action to take
# -----------------------------------------------------------------------

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call the LLM using the OpenAI-compatible client and return the text response."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WARN] LLM call failed: {e}", file=sys.stderr, flush=True)
        return ""


def agent_easy(obs: dict) -> dict:
    """Agent for easy task: classify the email."""
    system = (
        "You are a customer support classification expert. "
        "Given a customer email, classify it into exactly one category. "
        "Valid categories: complaint, refund, inquiry, technical, billing. "
        "Respond with ONLY a JSON object: "
        '{"action_type": "classify", "category": "<category>"}'
    )
    user = (
        f"Subject: {obs['email_subject']}\n"
        f"Body: {obs['email_body']}\n"
        f"Customer tier: {obs['customer_tier']}"
    )
    raw = call_llm(system, user)
    try:
        parsed = json.loads(raw)
        if parsed.get("category") not in ("complaint", "refund", "inquiry", "technical", "billing"):
            parsed["category"] = "inquiry"
        return parsed
    except Exception:
        # Fallback: keyword-based classification
        body_lower = (obs["email_subject"] + obs["email_body"]).lower()
        if any(w in body_lower for w in ["refund", "return", "money back"]):
            cat = "refund"
        elif any(w in body_lower for w in ["crash", "error", "bug", "not working", "broken"]):
            cat = "technical"
        elif any(w in body_lower for w in ["bill", "charge", "invoice", "payment"]):
            cat = "billing"
        elif any(w in body_lower for w in ["angry", "frustrated", "unacceptable", "complaint", "wrong"]):
            cat = "complaint"
        else:
            cat = "inquiry"
        return {"action_type": "classify", "category": cat}


def agent_medium(obs: dict) -> dict:
    """Agent for medium task: classify + respond."""
    system = (
        "You are a professional customer support agent. "
        "Given a customer email, you must: "
        "1) Classify it into one of: complaint, refund, inquiry, technical, billing. "
        "2) Write a professional, empathetic response that acknowledges the issue and provides next steps. "
        "Respond ONLY with a JSON object:\n"
        '{"action_type": "respond", "category": "<category>", "response_text": "<your response>"}\n'
        "The response_text must be at least 80 words."
    )
    user = (
        f"Subject: {obs['email_subject']}\n"
        f"Customer: {obs['customer_name']} (Tier: {obs['customer_tier']})\n"
        f"Previous interactions: {obs['previous_interactions']}\n"
        f"Body:\n{obs['email_body']}"
    )
    raw = call_llm(system, user)
    try:
        parsed = json.loads(raw)
        if parsed.get("category") not in ("complaint", "refund", "inquiry", "technical", "billing"):
            parsed["category"] = "inquiry"
        return parsed
    except Exception:
        # Fallback
        easy = agent_easy(obs)
        return {
            "action_type": "respond",
            "category": easy.get("category", "inquiry"),
            "response_text": (
                f"Dear {obs['customer_name']}, thank you for reaching out to us. "
                "We have received your message and understand your concern. "
                "Our team will review your case and get back to you within 24 hours. "
                "We apologize for any inconvenience caused and will do our best to resolve this promptly. "
                "Please let us know if you need any immediate assistance."
            ),
        }


def agent_hard_step1(obs: dict) -> dict:
    """Hard task step 1: classify."""
    return agent_easy(obs)


def agent_hard_step2(obs: dict) -> dict:
    """Hard task step 2: respond."""
    result = agent_medium(obs)
    result["action_type"] = "respond"
    return result


def agent_hard_step3(obs: dict) -> dict:
    """Hard task step 3: escalate or resolve."""
    system = (
        "You are a senior customer support manager. "
        "Given a customer email and its context, decide whether to escalate to a human agent "
        "or resolve it directly. "
        "Escalate if: legal threats, data breach, enterprise client with complex issue, "
        "outside refund policy with valid complaint. "
        "Resolve if: simple billing question, standard inquiry, low risk. "
        "Respond ONLY with a JSON object:\n"
        '{"action_type": "escalate", "escalation_reason": "<reason>"}\n'
        "OR\n"
        '{"action_type": "resolve", "resolution_summary": "<summary>"}'
    )
    user = (
        f"Subject: {obs['email_subject']}\n"
        f"Customer: {obs['customer_name']} (Tier: {obs['customer_tier']})\n"
        f"Previous interactions: {obs['previous_interactions']}\n"
        f"Body:\n{obs['email_body']}"
    )
    raw = call_llm(system, user)
    try:
        parsed = json.loads(raw)
        if parsed.get("action_type") not in ("escalate", "resolve"):
            parsed["action_type"] = "escalate"
        return parsed
    except Exception:
        # Fallback: escalate enterprise clients, resolve standard
        if obs.get("customer_tier") == "enterprise" or obs.get("previous_interactions", 0) > 5:
            return {
                "action_type": "escalate",
                "escalation_reason": "Enterprise client with complex issue requiring senior review.",
            }
        return {
            "action_type": "resolve",
            "resolution_summary": "Standard inquiry resolved with information provided.",
        }


# -----------------------------------------------------------------------
# HTTP client to talk to the running environment server
# -----------------------------------------------------------------------

import httpx

def env_reset(task_id: str) -> dict:
    """Call POST /reset on the environment server."""
    resp = httpx.post(
        f"{SPACE_URL}/reset",
        json={"task_id": task_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def env_step(action: dict) -> dict:
    """Call POST /step on the environment server."""
    resp = httpx.post(
        f"{SPACE_URL}/step",
        json=action,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def env_state() -> dict:
    """Call GET /state on the environment server."""
    resp = httpx.get(f"{SPACE_URL}/state", timeout=30)
    resp.raise_for_status()
    return resp.json()


# -----------------------------------------------------------------------
# Main episode runner
# -----------------------------------------------------------------------

def run_episode(task_id: str, episode: int) -> float:
    """Run one full episode for a given task. Returns total reward."""

    # Reset environment
    obs = env_reset(task_id)
    total_reward = 0.0
    step = 0
    emails_processed = 0
    max_steps = 30  # Safety cap

    log_start(
        task_id=task_id,
        episode=episode,
        email_id=obs.get("email_id", "unknown"),
        email_subject=obs.get("email_subject", ""),
    )

    # Track hard task sub-step
    hard_step_num = 1

    while step < max_steps:
        step += 1

        # Choose action based on task
        if task_id == "easy":
            action = agent_easy(obs)
        elif task_id == "medium":
            action = agent_medium(obs)
        elif task_id == "hard":
            if hard_step_num == 1:
                action = agent_hard_step1(obs)
            elif hard_step_num == 2:
                action = agent_hard_step2(obs)
            else:
                action = agent_hard_step3(obs)
        else:
            action = agent_easy(obs)

        # Step the environment
        result = env_step(action)

        reward = float(result.get("reward", 0.0))
        total_reward += reward
        task_complete = result.get("task_complete", False)
        feedback = result.get("action_feedback", "")
        email_id = result.get("email_id", "unknown")

        log_step(
            task_id=task_id,
            episode=episode,
            step=step,
            email_id=email_id,
            action_type=action.get("action_type", "unknown"),
            reward=reward,
            feedback=feedback,
        )

        # Update hard task sub-step
        if task_id == "hard":
            action_type = action.get("action_type")
            if action_type == "classify":
                hard_step_num = 2
            elif action_type == "respond":
                hard_step_num = 3
            elif action_type in ("escalate", "resolve"):
                hard_step_num = 1  # Reset for next email
                emails_processed += 1

        if task_id in ("easy", "medium") and task_complete:
            emails_processed += 1

        # Check if all emails processed
        state = env_state()
        if state.get("emails_processed", 0) >= 3 or (
            task_complete and state.get("emails_processed", 0) >= len(
                ["easy", "medium", "hard"]
            )
        ):
            # Check if we've done enough
            if emails_processed >= 3:
                break

        obs = result

    log_end(
        task_id=task_id,
        episode=episode,
        total_reward=round(total_reward, 3),
        emails_processed=emails_processed,
        success=total_reward > 0.0,
    )

    return total_reward


# -----------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------

def main():
    print(f"[INFO] Starting inference. Model: {MODEL_NAME}, Base URL: {API_BASE_URL}", flush=True)
    print(f"[INFO] Environment URL: {SPACE_URL}", flush=True)

    # Verify environment is reachable
    try:
        health = httpx.get(f"{SPACE_URL}/health", timeout=10)
        print(f"[INFO] Environment health: {health.status_code}", flush=True)
    except Exception as e:
        print(f"[ERROR] Cannot reach environment at {SPACE_URL}: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

    tasks = ["easy", "medium", "hard"]
    results = {}

    for i, task_id in enumerate(tasks):
        print(f"\n[INFO] Running task: {task_id.upper()} (episode {i + 1})", flush=True)
        try:
            total_reward = run_episode(task_id=task_id, episode=i + 1)
            results[task_id] = round(total_reward, 3)
            print(f"[INFO] Task {task_id} complete. Total reward: {total_reward:.3f}", flush=True)
        except Exception as e:
            print(f"[ERROR] Task {task_id} failed: {e}", file=sys.stderr, flush=True)
            results[task_id] = 0.0

    print("\n[INFO] === FINAL SCORES ===", flush=True)
    for task_id, score in results.items():
        print(f"[INFO]   {task_id:8s}: {score:.3f}", flush=True)

    overall = sum(results.values()) / len(results)
    print(f"[INFO]   overall : {overall:.3f}", flush=True)

    # Final score summary in structured format for eval system
    summary = {
        "event": "SUMMARY",
        "scores": results,
        "overall_score": round(overall, 3),
        "timestamp": time.time(),
    }
    print(f"[SUMMARY] {json.dumps(summary)}", flush=True)


if __name__ == "__main__":
    main()
