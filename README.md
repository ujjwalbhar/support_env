---
title: Support Env
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Customer Support Inbox Automation — OpenEnv Environment

An OpenEnv reinforcement learning environment where an AI agent learns to handle real-world customer support emails. The agent must classify incoming emails, generate professional responses, and make escalation or resolution decisions.

---

## Overview

| Property | Value |
|---|---|
| Framework | OpenEnv (meta-pytorch) |
| Difficulty Levels | 3 (easy, medium, hard) |
| Reward Range | 0.0 – 1.0 (partial signals at each step) |
| Action Space | classify / respond / escalate / resolve |
| Deployment | Hugging Face Spaces (Docker) |

---

## Environment Description

### Action Space

The agent sends one of four action types:

| Action | Required Fields | When to Use |
|---|---|---|
| `classify` | `category` | Categorise the email |
| `respond` | `category`, `response_text` | Send a reply to the customer |
| `escalate` | `escalation_reason` | Route to a human agent |
| `resolve` | `resolution_summary` | Mark the ticket as resolved |

Valid categories: `complaint`, `refund`, `inquiry`, `technical`, `billing`

### Observation Space

Each step returns:

| Field | Type | Description |
|---|---|---|
| `email_id` | string | Unique ticket identifier |
| `email_subject` | string | Email subject line |
| `email_body` | string | Full email content |
| `customer_name` | string | Customer's name |
| `customer_tier` | string | standard / premium / enterprise |
| `previous_interactions` | int | Prior contact count |
| `current_category` | string | Classification so far (if done) |
| `action_feedback` | string | Grader feedback on last action |
| `task_complete` | bool | Whether this email is done |
| `reward` | float | Reward for last action (0.0–1.0) |
| `task_id` | string | Current difficulty level |

---

## Task Definitions

### Easy — Email Classification
Classify the incoming email into the correct category. Single-step task.

**Reward:**
- 1.0 — Correct category
- 0.5 — Acceptable but not optimal category
- 0.0 — Wrong category

### Medium — Classify + Respond
Classify the email AND write a professional, empathetic reply.

**Reward (weighted):**
- 40% from classification accuracy
- 60% from response quality (keyword checks, forbidden phrases, minimum length)

### Hard — Multi-Step Resolution
Three-step workflow per email:
1. **Step 1 — Classify** (20% of reward): Categorise the email
2. **Step 2 — Respond** (40% of reward): Acknowledge and address the issue
3. **Step 3 — Decide** (40% of reward): Escalate or resolve based on risk/complexity

Escalation is required for: legal threats, data breach reports, enterprise clients with complex issues, out-of-policy refund requests with valid reasons. Resolution is correct for: simple inquiries, standard billing questions.

---

## Reward Function

All rewards are in `[0.0, 1.0]` with meaningful partial signals:

```
Easy:    reward = classification_score           # binary or half-credit
Medium:  reward = 0.4 * class_score + 0.6 * response_quality_score
Hard:    reward = step1_score + step2_score + step3_score  # cumulative
```

The grader for response quality checks:
- Required keywords present (50% of quality score)
- Forbidden phrases absent (30% of quality score)
- Minimum word count met (20% of quality score)

---

## Project Structure

```
support_env/
├── inference.py              # Baseline inference script (root level, required)
├── models.py                 # SupportAction, SupportObservation, SupportState (Pydantic)
├── tasks.py                  # All task definitions and email scenarios
├── graders.py                # Reward graders for easy / medium / hard
├── client.py                 # SupportEnv(EnvClient) for external use
├── openenv.yaml              # OpenEnv manifest
├── pyproject.toml            # Dependencies
├── Dockerfile                # HF Spaces compatible container
├── .env.example              # Required env vars template
├── README.md                 # This file
└── server/
    ├── __init__.py
    ├── app.py                # FastAPI application
    ├── support_environment.py # Core environment logic
    └── requirements.txt      # Docker dependencies
```

---

## Setup & Local Run

### 1. Install dependencies

```bash
pip install openenv-core fastapi uvicorn pydantic openai httpx python-dotenv
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your API_BASE_URL, MODEL_NAME, HF_TOKEN, SPACE_URL
```

### 3. Start the environment server

```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

### 4. Run the baseline inference script

```bash
python inference.py
```

---

## Docker Build & Run

```bash
# Build the image
docker build -t support-env .

# Run locally
docker run -p 7860:7860 --env-file .env support-env

# Verify health
curl http://localhost:7860/health

# Test reset
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}'
```

---

## Deploy to Hugging Face Spaces

```bash
# Login
huggingface-cli login

# Push (from inside the support_env directory)
openenv push --repo-id YOUR-USERNAME/support-env
```

Or manually:
1. Create a new Space at huggingface.co with Docker SDK
2. Push your repo: `git push`
3. Set the Secrets in Space Settings: `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`

---

## API Endpoints

Once running, the following endpoints are available:

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check — returns 200 if running |
| `/reset` | POST | Start a new episode. Body: `{"task_id": "easy"}` |
| `/step` | POST | Take an action. Body: `SupportAction` JSON |
| `/state` | GET | Get current episode state |

### Example API calls

```bash
# Reset with easy task
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}'

# Classify an email
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "classify", "category": "complaint"}'

# Get state
curl http://localhost:7860/state
```

---

## Inference Script Log Format

The `inference.py` script emits three structured log types to stdout:

```
[START] {"event": "START", "task_id": "easy", "episode": 1, "email_id": "easy_001", ...}
[STEP]  {"event": "STEP", "task_id": "easy", "episode": 1, "step": 1, "reward": 1.0, ...}
[END]   {"event": "END", "task_id": "easy", "episode": 1, "total_reward": 1.0, ...}
```

---

## Required Environment Variables

| Variable | Description |
|---|---|
| `API_BASE_URL` | LLM API endpoint (OpenAI-compatible) |
| `MODEL_NAME` | Model identifier |
| `HF_TOKEN` | Hugging Face / LLM API key |
| `SPACE_URL` | Deployed HF Space URL (for inference.py) |

---

## Infra Constraints

- Inference script runtime: < 20 minutes
- Target machine: 2 vCPU / 8GB RAM
- Python: 3.10+

---

## License

MIT
