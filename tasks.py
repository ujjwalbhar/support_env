"""
Task definitions for the Customer Support Inbox Automation environment.
3 difficulty levels: easy, medium, hard.
Each task has sample emails, expected outcomes, and grader logic.
"""

from typing import Dict, Any

# -------------------------------------------------------------------
# TASK DEFINITIONS
# -------------------------------------------------------------------

TASKS: Dict[str, Dict[str, Any]] = {

    # ----------------------------------------------------------------
    # EASY: Classify the email into the correct category
    # ----------------------------------------------------------------
    "easy": {
        "description": (
            "Classify the incoming customer email into the correct category. "
            "Categories: complaint, refund, inquiry, technical, billing."
        ),
        "emails": [
            {
                "id": "easy_001",
                "subject": "Where is my order?",
                "body": (
                    "Hi, I placed an order 2 weeks ago (Order #45231) and it still hasn't arrived. "
                    "The tracking shows it was last updated 10 days ago. "
                    "I'm very frustrated and need this resolved immediately."
                ),
                "customer_name": "Priya Sharma",
                "customer_tier": "standard",
                "previous_interactions": 1,
                "correct_category": "complaint",
                "acceptable_categories": ["complaint"],
            },
            {
                "id": "easy_002",
                "subject": "Request for refund - damaged product",
                "body": (
                    "Hello, I received my laptop bag yesterday but it arrived with a torn strap. "
                    "I'd like to return it and get a full refund of Rs. 2,499. "
                    "Please let me know the return process."
                ),
                "customer_name": "Rahul Mehta",
                "customer_tier": "premium",
                "previous_interactions": 3,
                "correct_category": "refund",
                "acceptable_categories": ["refund"],
            },
            {
                "id": "easy_003",
                "subject": "What are your business hours?",
                "body": (
                    "Hi there, I wanted to know what your customer support hours are. "
                    "Also, do you have a physical store in Delhi? "
                    "Thanks in advance."
                ),
                "customer_name": "Anjali Singh",
                "customer_tier": "standard",
                "previous_interactions": 0,
                "correct_category": "inquiry",
                "acceptable_categories": ["inquiry"],
            },
            {
                "id": "easy_004",
                "subject": "App keeps crashing on login",
                "body": (
                    "Your mobile app crashes every time I try to log in. "
                    "I've tried reinstalling it twice. "
                    "I'm using Android 13 on a Samsung Galaxy S22. "
                    "Please fix this urgently."
                ),
                "customer_name": "Vikram Patel",
                "customer_tier": "enterprise",
                "previous_interactions": 5,
                "correct_category": "technical",
                "acceptable_categories": ["technical"],
            },
            {
                "id": "easy_005",
                "subject": "Double charged on my invoice",
                "body": (
                    "I noticed I was charged twice for my monthly subscription this month. "
                    "Both charges of Rs. 999 appear on my bank statement dated March 1st and March 3rd. "
                    "Please investigate and refund the duplicate charge."
                ),
                "customer_name": "Deepa Nair",
                "customer_tier": "premium",
                "previous_interactions": 2,
                "correct_category": "billing",
                "acceptable_categories": ["billing", "refund"],
            },
        ],
    },

    # ----------------------------------------------------------------
    # MEDIUM: Classify correctly AND generate an appropriate response
    # ----------------------------------------------------------------
    "medium": {
        "description": (
            "Classify the email AND generate a professional, empathetic customer response. "
            "The response must: (1) acknowledge the issue, (2) provide relevant next steps, "
            "(3) be polite and professional."
        ),
        "emails": [
            {
                "id": "medium_001",
                "subject": "Extremely unhappy - wrong item delivered",
                "body": (
                    "This is unacceptable! I ordered a Blue Wireless Headphone (Model XB55) "
                    "but received a completely different product - a wired keyboard. "
                    "Order #78456. I need this fixed TODAY. I have an important meeting tomorrow "
                    "and need these headphones."
                ),
                "customer_name": "Arjun Kapoor",
                "customer_tier": "enterprise",
                "previous_interactions": 8,
                "correct_category": "complaint",
                "acceptable_categories": ["complaint", "refund"],
                "response_requirements": {
                    "must_include": ["apologize", "replacement", "expedite"],
                    "must_not_include": ["cannot", "impossible", "not our fault"],
                    "tone": "empathetic and urgent",
                    "min_length": 80,
                },
            },
            {
                "id": "medium_002",
                "subject": "Cancel subscription and refund",
                "body": (
                    "I want to cancel my annual subscription immediately. "
                    "I subscribed 2 months ago but the features I was promised are not available. "
                    "I paid Rs. 5,999 for the year. Please process a pro-rated refund for the "
                    "remaining 10 months (Rs. 4,999). Subscription ID: SUB-2024-8821."
                ),
                "customer_name": "Sneha Joshi",
                "customer_tier": "premium",
                "previous_interactions": 1,
                "correct_category": "refund",
                "acceptable_categories": ["refund"],
                "response_requirements": {
                    "must_include": ["confirm", "process", "refund"],
                    "must_not_include": ["no refund", "non-refundable"],
                    "tone": "professional and helpful",
                    "min_length": 80,
                },
            },
            {
                "id": "medium_003",
                "subject": "Integration with Salesforce not working",
                "body": (
                    "Our Salesforce integration has been broken for 3 days now. "
                    "We're an enterprise client and this is severely impacting our sales team (50 users). "
                    "Error code: API_TIMEOUT_503. Our IT team has already checked firewall settings. "
                    "We need a resolution or at minimum a workaround ASAP."
                ),
                "customer_name": "Karan Malhotra",
                "customer_tier": "enterprise",
                "previous_interactions": 15,
                "correct_category": "technical",
                "acceptable_categories": ["technical"],
                "response_requirements": {
                    "must_include": ["escalate", "priority", "team"],
                    "must_not_include": ["reinstall", "basic troubleshooting"],
                    "tone": "urgent and technical",
                    "min_length": 100,
                },
            },
        ],
    },

    # ----------------------------------------------------------------
    # HARD: Multi-step resolution - classify, respond, then decide
    #       whether to escalate or resolve with full reasoning
    # ----------------------------------------------------------------
    "hard": {
        "description": (
            "Handle a complex multi-step support scenario. You must: "
            "(1) classify the email correctly, "
            "(2) generate a response acknowledging the issue, "
            "(3) make the correct final decision: escalate to human or resolve. "
            "Consider customer tier, urgency, legal risk, and complexity."
        ),
        "emails": [
            {
                "id": "hard_001",
                "subject": "Threatening legal action - data breach",
                "body": (
                    "I have reason to believe my personal data has been compromised through your platform. "
                    "I noticed unauthorized login attempts from IP addresses in Russia and Germany. "
                    "I am an enterprise customer (Account: ENT-4421) and my company's confidential "
                    "contracts may have been accessed. I have already spoken with my lawyer and will "
                    "file a complaint with CERT-In if this is not addressed within 24 hours. "
                    "I need an immediate security audit of my account."
                ),
                "customer_name": "Rajesh Verma",
                "customer_tier": "enterprise",
                "previous_interactions": 20,
                "correct_category": "technical",
                "acceptable_categories": ["technical", "complaint"],
                "correct_final_action": "escalate",
                "escalation_required": True,
                "escalation_reasons": ["legal threat", "data breach", "enterprise client", "CERT-In"],
                "response_requirements": {
                    "must_include": ["security", "investigate", "priority"],
                    "must_not_include": ["we are not responsible", "user error"],
                    "tone": "urgent, serious, empathetic",
                    "min_length": 100,
                },
            },
            {
                "id": "hard_002",
                "subject": "Refund request after 90 days",
                "body": (
                    "I purchased your Pro plan 3 months ago (Invoice: INV-20241205, Rs. 11,999/year). "
                    "I was told during sales that the plan includes AI-powered analytics, but this feature "
                    "was never activated on my account despite multiple support tickets (Tickets: #4521, #4892, #5103). "
                    "I want a full refund. I know your policy is 30 days but your team failed to deliver "
                    "the promised feature. This is a breach of contract."
                ),
                "customer_name": "Meera Krishnan",
                "customer_tier": "premium",
                "previous_interactions": 6,
                "correct_category": "refund",
                "acceptable_categories": ["refund", "complaint"],
                "correct_final_action": "escalate",
                "escalation_required": True,
                "escalation_reasons": ["outside refund window", "breach of contract claim", "multiple prior tickets"],
                "response_requirements": {
                    "must_include": ["review", "exception", "understand"],
                    "must_not_include": ["policy clearly states", "not eligible", "sorry nothing we can do"],
                    "tone": "empathetic and solution-oriented",
                    "min_length": 120,
                },
            },
            {
                "id": "hard_003",
                "subject": "Simple billing question",
                "body": (
                    "Hi, I just want to confirm - does my current Standard plan include GST in the Rs. 499 price "
                    "shown on your website, or is GST added on top? "
                    "I need this for my company's expense report."
                ),
                "customer_name": "Suresh Kumar",
                "customer_tier": "standard",
                "previous_interactions": 0,
                "correct_category": "billing",
                "acceptable_categories": ["billing", "inquiry"],
                "correct_final_action": "resolve",
                "escalation_required": False,
                "response_requirements": {
                    "must_include": ["GST", "inclusive", "price"],
                    "must_not_include": [],
                    "tone": "friendly and concise",
                    "min_length": 50,
                },
            },
        ],
    },
}


def get_task_emails(task_id: str) -> list:
    """Return the list of emails for a given task difficulty."""
    return TASKS[task_id]["emails"]


def get_task_description(task_id: str) -> str:
    """Return the description for a task."""
    return TASKS[task_id]["description"]
