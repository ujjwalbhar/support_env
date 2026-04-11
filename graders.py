"""
Graders for the Customer Support Inbox Automation environment.
Each grader computes a reward strictly inside (0.0, 1.0) - never equal to 0.0 or 1.0.
"""
from typing import Dict, Any, Tuple

MIN_SCORE = 0.01
MAX_SCORE = 0.99


def sanitize_reward(score: float) -> float:
    """Clamp score to strictly inside (0.0, 1.0)."""
    score = float(score)
    if score <= 0.0:
        return MIN_SCORE
    if score >= 1.0:
        return MAX_SCORE
    return round(score, 3)


def grade_easy(action: Dict[str, Any], email: Dict[str, Any]) -> Tuple[float, str]:
    """
    Grade an easy task: pure classification.
    Reward (sanitized):
        ~1.0 - correct category
        0.5  - acceptable but not optimal category
        ~0.0 - wrong category or no category provided
    """
    if action.get("action_type") != "classify":
        return sanitize_reward(0.0), "Wrong action type. Use 'classify' for easy tasks."

    predicted = action.get("category")
    if predicted is None:
        return sanitize_reward(0.0), "No category provided."

    correct = email["correct_category"]
    acceptable = email.get("acceptable_categories", [correct])

    if predicted == correct:
        return sanitize_reward(1.0), f"Perfect classification! '{predicted}' is correct."
    elif predicted in acceptable:
        return sanitize_reward(0.5), (
            f"Acceptable classification. '{predicted}' is valid but '{correct}' is optimal."
        )
    else:
        return sanitize_reward(0.0), (
            f"Incorrect. '{predicted}' is wrong. Expected: '{correct}'."
        )


def grade_medium(action: Dict[str, Any], email: Dict[str, Any]) -> Tuple[float, str]:
    """
    Grade a medium task: classification (40%) + response quality (60%).
    Classification score: 1.0 correct, 0.5 acceptable, 0.0 wrong
    Response quality score: checks keywords, forbidden phrases, min length
    """
    if action.get("action_type") not in ("respond", "classify"):
        return sanitize_reward(0.0), (
            "Use 'respond' (with response_text) or 'classify' for medium tasks."
        )

    reqs = email.get("response_requirements", {})

    # -- Classification score (40%) --
    predicted_cat = action.get("category")
    correct_cat = email["correct_category"]
    acceptable_cats = email.get("acceptable_categories", [correct_cat])

    if predicted_cat == correct_cat:
        class_score = 1.0
    elif predicted_cat in acceptable_cats:
        class_score = 0.5
    else:
        class_score = 0.0

    # -- Response quality score (60%) --
    response = (action.get("response_text") or "").lower()
    quality_score = 0.0
    quality_notes = []

    if not response:
        quality_notes.append("No response text provided.")
    else:
        must_include = reqs.get("must_include", [])
        must_not_include = reqs.get("must_not_include", [])
        min_length = reqs.get("min_length", 50)

        if must_include:
            found = sum(1 for kw in must_include if kw.lower() in response)
            keyword_score = found / len(must_include)
            quality_score += 0.5 * keyword_score
            if keyword_score < 1.0:
                missing = [kw for kw in must_include if kw.lower() not in response]
                quality_notes.append(f"Missing keywords: {missing}.")
        else:
            quality_score += 0.5

        if must_not_include:
            violations = [ph for ph in must_not_include if ph.lower() in response]
            if not violations:
                quality_score += 0.3
            else:
                quality_notes.append(f"Forbidden phrases found: {violations}.")
        else:
            quality_score += 0.3

        if len(response.split()) >= min_length:
            quality_score += 0.2
        else:
            quality_notes.append(
                f"Response too short ({len(response.split())} words, need {min_length})."
            )

    total = 0.4 * class_score + 0.6 * quality_score
    total = sanitize_reward(total)

    notes = f"Classification: {class_score:.1f}. Response quality: {quality_score:.2f}."
    if quality_notes:
        notes += " Issues: " + " ".join(quality_notes)

    return total, notes


def grade_hard(action: Dict[str, Any], email: Dict[str, Any], step: int) -> Tuple[float, str]:
    """
    Grade a hard task: multi-step.
    Step 1 - classify (20%)
    Step 2 - respond  (40%)
    Step 3 - escalate/resolve correctly (40%)
    """
    reqs = email.get("response_requirements", {})

    if step == 1:
        if action.get("action_type") != "classify":
            return sanitize_reward(0.0), "Step 1: Use 'classify' to categorize the email."

        predicted = action.get("category")
        correct = email["correct_category"]
        acceptable = email.get("acceptable_categories", [correct])

        if predicted == correct:
            return sanitize_reward(0.2), "Step 1 complete: Correct classification (+0.2)."
        elif predicted in acceptable:
            return sanitize_reward(0.1), (
                f"Step 1 partial: '{predicted}' acceptable but '{correct}' is better (+0.1)."
            )
        else:
            return sanitize_reward(0.0), f"Step 1 failed: '{predicted}' is incorrect."

    elif step == 2:
        if action.get("action_type") != "respond":
            return sanitize_reward(0.0), "Step 2: Use 'respond' with a response_text."

        response = (action.get("response_text") or "").lower()
        must_include = reqs.get("must_include", [])
        must_not_include = reqs.get("must_not_include", [])
        min_length = reqs.get("min_length", 80)

        score = 0.0
        notes = []

        if must_include:
            found = sum(1 for kw in must_include if kw.lower() in response)
            kw_ratio = found / len(must_include)
            score += 0.25 * kw_ratio
            if kw_ratio < 1.0:
                missing = [kw for kw in must_include if kw.lower() not in response]
                notes.append(f"Missing: {missing}")
        else:
            score += 0.25

        if must_not_include:
            violations = [ph for ph in must_not_include if ph.lower() in response]
            if not violations:
                score += 0.1
            else:
                notes.append(f"Forbidden: {violations}")
        else:
            score += 0.1

        if len(response.split()) >= min_length:
            score += 0.05
        else:
            notes.append(f"Too short ({len(response.split())} words)")

        total = sanitize_reward(score)
        feedback = f"Step 2 response score: +{total:.3f}."
        if notes:
            feedback += " Issues: " + "; ".join(notes) + "."
        return total, feedback

    elif step == 3:
        correct_action = email.get("correct_final_action", "resolve")
        taken_action = action.get("action_type")

        if taken_action == correct_action:
            if taken_action == "escalate":
                reason = (action.get("escalation_reason") or "").lower()
                escalation_keywords = email.get("escalation_reasons", [])
                if escalation_keywords:
                    found = sum(1 for kw in escalation_keywords if kw.lower() in reason)
                    quality = found / len(escalation_keywords)
                    score = sanitize_reward(0.3 + 0.1 * quality)
                    return score, (
                        f"Step 3: Correct escalation! Reasoning quality: {quality:.0%}. (+{score:.3f})"
                    )
                return sanitize_reward(0.4), "Step 3: Correct escalation with reason provided. (+0.4)"
            else:
                summary = action.get("resolution_summary") or ""
                if summary and len(summary.split()) >= 10:
                    return sanitize_reward(0.4), (
                        "Step 3: Correct resolution with good summary. (+0.4)"
                    )
                return sanitize_reward(0.3), (
                    "Step 3: Correct resolution but summary too brief. (+0.3)"
                )

        if correct_action == "escalate" and taken_action == "resolve":
            return sanitize_reward(0.0), (
                "Step 3 failed: Should have escalated (legal risk / complexity) but resolved. "
                "Correct action: 'escalate'."
            )

        if correct_action == "resolve" and taken_action == "escalate":
            return sanitize_reward(0.1), (
                "Step 3 partial: Escalated unnecessarily. This simple issue could be resolved directly."
            )

        return sanitize_reward(0.0), (
            f"Step 3 failed: Wrong action '{taken_action}'. Expected '{correct_action}'."
        )

    return sanitize_reward(0.0), "Unknown step."


def run_all_graders(task_id: str) -> Dict[str, Any]:
    """
    Utility to verify all graders function correctly by running dummy actions.
    Checks that every score is strictly inside (0.0, 1.0).
    """
    from tasks import TASKS

    results = {}
    emails = TASKS[task_id]["emails"]

    for email in emails:
        eid = email["id"]

        if task_id == "easy":
            score, msg = grade_easy(
                {"action_type": "classify", "category": email["correct_category"]},
                email,
            )
            results[eid] = {
                "score": score,
                "msg": msg,
                "strictly_in_range": 0.0 < score < 1.0,
            }

        elif task_id == "medium":
            reqs = email.get("response_requirements", {})
            keywords = reqs.get("must_include", ["hello"])
            response = " ".join(keywords) + " " + ("thank you " * 30)
            score, msg = grade_medium(
                {
                    "action_type": "respond",
                    "category": email["correct_category"],
                    "response_text": response,
                },
                email,
            )
            results[eid] = {
                "score": score,
                "msg": msg,
                "strictly_in_range": 0.0 < score < 1.0,
            }

        elif task_id == "hard":
            score, msg = grade_hard(
                {"action_type": "classify", "category": email["correct_category"]},
                email,
                step=1,
            )
            results[eid] = {
                "score": score,
                "msg": msg,
                "strictly_in_range": 0.0 < score < 1.0,
            }

    return results


if __name__ == "__main__":
    import json

    for t in ["easy", "medium", "hard"]:
        print(f"\n=== {t.upper()} grader test ===")
        r = run_all_graders(t)
        print(json.dumps(r, indent=2))
