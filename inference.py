"""
inference.py - Baseline inference script for Customer Support Inbox Automation.
MANDATORY stdout format:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
Required env vars:
    API_BASE_URL - LLM API endpoint
    MODEL_NAME   - Model identifier
    HF_TOKEN     - Hugging Face / API key
    SPACE_URL    - Environment URL (default: http://localhost:7860)
"""
import os
import sys
import json
import httpx
from openai import OpenAI

# Safe fallback score - never use exact 0.0 or 1.0
SAFE_MIN = 0.01

# ── Configuration ─────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.environ.get("HF_TOKEN")
SPACE_URL    = os.environ.get("SPACE_URL", "http://localhost:7860")
BENCHMARK    = "support_env"
MAX_STEPS    = 10

client = OpenAI(
    api_key=HF_TOKEN,
    base_url=API_BASE_URL,
)

TASKS = ["easy", "medium", "hard"]

# ── Mandatory log helpers (exact format) ──────────────────────────────────────
def log_start(task_id):
    print(f"[START] task={task_id} env={BENCHMARK} model={MODEL_NAME}", flush=True)

def log_step(step, action_type, reward, done, error=None):
    err = str(error).replace("\n", " ") if error else "null"
    print(f"[STEP] step={step} action={action_type} reward={reward:.2f} done={str(done).lower()} error={err}", flush=True)

def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

# ── Environment HTTP client ───────────────────────────────────────────────────
def env_reset(task_id):
    resp = httpx.post(f"{SPACE_URL}/reset", json={"task_id": task_id}, timeout=30)
    resp.raise_for_status()
    return resp.json()

def env_step(action):
    resp = httpx.post(f"{SPACE_URL}/step", json=action, timeout=30)
    resp.raise_for_status()
    return resp.json()

def env_state():
    resp = httpx.get(f"{SPACE_URL}/state", timeout=30)
    resp.raise_for_status()
    return resp.json()

# ── LLM agent ────────────────────────────────────────────────────────────────
SYSTEM_EASY = """You are a customer support classifier.
Classify the email into exactly one category: complaint, refund, inquiry, technical, billing
Respond with ONLY valid JSON: {"action_type": "classify", "category": "<category>"}"""

SYSTEM_MEDIUM = """You are a professional customer support agent.
1) Classify: complaint, refund, inquiry, technical, billing
2) Write a professional empathetic response (at least 80 words)
Respond with ONLY valid JSON:
{"action_type": "respond", "category": "<category>", "response_text": "<reply>"}"""

SYSTEM_HARD_1 = """Classify the email: complaint, refund, inquiry, technical, billing
Respond with ONLY valid JSON: {"action_type": "classify", "category": "<category>"}"""

SYSTEM_HARD_2 = """Write a professional reply to the customer (at least 80 words).
Respond with ONLY valid JSON:
{"action_type": "respond", "category": "<category>", "response_text": "<reply>"}"""

SYSTEM_HARD_3 = """Decide: escalate or resolve.
Escalate if: legal threats, data breach, enterprise client, out-of-policy refund.
Resolve if: simple inquiry, standard billing, low risk.
Respond with ONLY valid JSON:
{"action_type": "escalate", "escalation_reason": "<reason>"}
OR
{"action_type": "resolve", "resolution_summary": "<summary>"}"""

def call_llm(system, obs):
    user = (
        f"Subject: {obs.get('email_subject', '')}\n"
        f"Body: {obs.get('email_body', '')}\n"
        f"Customer: {obs.get('customer_name', 'Customer')} "
        f"(Tier: {obs.get('customer_tier', 'standard')})\n"
        f"Previous interactions: {obs.get('previous_interactions', 0)}"
    )
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        return None

def get_action(obs, task_id, hard_step=1):
    if task_id == "easy":
        return call_llm(SYSTEM_EASY, obs)
    elif task_id == "medium":
        return call_llm(SYSTEM_MEDIUM, obs)
    elif task_id == "hard":
        if hard_step == 1:
            return call_llm(SYSTEM_HARD_1, obs)
        elif hard_step == 2:
            return call_llm(SYSTEM_HARD_2, obs)
        else:
            return call_llm(SYSTEM_HARD_3, obs)
    return {"action_type": "classify", "category": "inquiry"}

# ── Episode runner ────────────────────────────────────────────────────────────
def run_task(task_id):
    rewards = []
    steps_taken = 0
    hard_step = 1
    log_start(task_id)
    try:
        result = env_reset(task_id)
        obs = result.get("observation", result)
        for step in range(1, MAX_STEPS + 1):
            error = None
            try:
                action = get_action(obs, task_id, hard_step)
                if action is None:
                    raise ValueError("LLM returned invalid action")
                action_type = action.get("action_type", "classify")
                step_result = env_step(action)
                reward = float(step_result.get("reward", SAFE_MIN))
                # Ensure reward is never exactly 0.0 or 1.0
                if reward <= 0.0:
                    reward = SAFE_MIN
                elif reward >= 1.0:
                    reward = 0.99
                done = bool(step_result.get("task_complete", step_result.get("done", False)))
                rewards.append(reward)
                steps_taken = step
                log_step(step, action_type, reward, done, error)
                if task_id == "hard":
                    if action_type == "classify":
                        hard_step = 2
                    elif action_type == "respond":
                        hard_step = 3
                    elif action_type in ("escalate", "resolve"):
                        hard_step = 1
                if done:
                    try:
                        state = env_state()
                        if state.get("emails_processed", 0) >= 3:
                            break
                    except Exception:
                        break
                obs = step_result.get("observation", step_result)
            except Exception as e:
                error = str(e).replace("\n", " ")
                rewards.append(SAFE_MIN)
                steps_taken = step
                log_step(step, "null", SAFE_MIN, False, error)
                break
        score = round(sum(rewards) / max(len(rewards), 1), 2)
        # Ensure final score is never exactly 0.0 or 1.0
        if score <= 0.0:
            score = SAFE_MIN
        elif score >= 1.0:
            score = 0.99
        success = score > SAFE_MIN
        log_end(success, steps_taken, score, rewards)
        return score
    except Exception as e:
        log_end(False, steps_taken, SAFE_MIN, rewards if rewards else [SAFE_MIN])
        raise

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    try:
        health = httpx.get(f"{SPACE_URL}/health", timeout=10)
        if health.status_code != 200:
            print(f"[WARN] Health check returned {health.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Cannot reach environment at {SPACE_URL}: {e}", file=sys.stderr)
        sys.exit(1)

    scores = {}
    for task_id in TASKS:
        try:
            score = run_task(task_id)
            scores[task_id] = score
        except Exception as e:
            print(f"[ERROR] Task {task_id} failed: {e}", file=sys.stderr)
            scores[task_id] = SAFE_MIN
        print()

    overall = round(sum(scores.values()) / len(scores), 2)
    print(
        f"[INFO] easy={scores.get('easy', SAFE_MIN):.2f} "
        f"medium={scores.get('medium', SAFE_MIN):.2f} "
        f"hard={scores.get('hard', SAFE_MIN):.2f} "
        f"overall={overall:.2f}",
        flush=True,
    )

if __name__ == "__main__":
    main()
