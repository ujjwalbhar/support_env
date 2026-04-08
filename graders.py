"""
Graders for the Customer Support Inbox Automation environment.
Each grader computes a reward in [0.0, 1.0] with partial credit signals.
"""

from typing import Dict, Any, Tuple


def grade_easy(action: Dict[str, Any], email: Dict[str, Any]) -> Tuple[float, str]:
    """
    Grade an easy task: pure classification.
    Reward:
      1.0 - correct category
      0.5 - acceptable but not optimal category
      0.0 - wrong category or no category provided
    """
    if action.get("action_type") != "classify":
        return 0.0, "Wrong action type. Use 'classify' for easy tasks."

    predicted = action.get("category")
    if predicted is None:
        return 0.0, "No category provided."

    correct = email["correct_category"]
    acceptable = email.get("acceptable_categories", [correct])

    if predicted == correct:
        return 1.0, f"Perfect classification! '{predicted}' is correct."
    elif predicted in acceptable:
        return 0.5, f"Acceptable classification. '{predicted}' is valid but '{correct}' is optimal."
    else:
        return 0.0, f"Incorrect. '{predicted}' is wrong. Expected: '{correct}'."


def grade_medium(action: Dict[str, Any], email: Dict[str, Any]) -> Tuple[float, str]:
    """
    Grade a medium task: classification (40%) + response quality (60%).

    Classification score (0.0-1.0):
      1.0 - correct, 0.5 - acceptable, 0.0 - wrong

    Response quality score (0.0-1.0):
      Checks: required keywords present, forbidden phrases absent, minimum length met
    """
    if action.get("action_type") not in ("respond", "classify"):
        return 0.0, "Use 'respond' (with response_text) or 'classify' for medium tasks."

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

        # Check required keywords (50% of quality score)
        if must_include:
            found = sum(1 for kw in must_include if kw.lower() in response)
            keyword_score = found / len(must_include)
            quality_score += 0.5 * keyword_score
            if keyword_score < 1.0:
                missing = [kw for kw in must_include if kw.lower() not in response]
                quality_notes.append(f"Missing keywords: {missing}.")
        else:
            quality_score += 0.5

        # Check forbidden phrases (30% of quality score)
        if must_not_include:
            violations = [ph for ph in must_not_include if ph.lower() in response]
            if not violations:
                quality_score += 0.3
            else:
                quality_notes.append(f"Forbidden phrases found: {violations}.")
        else:
            quality_score += 0.3

        # Check minimum length (20% of quality score)
        if len(response.split()) >= min_length:
            quality_score += 0.2
        else:
            quality_notes.append(
                f"Response too short ({len(response.split())} words, need {min_length})."
            )

    total = round(0.4 * class_score + 0.6 * quality_score, 3)
    notes = f"Classification: {class_score:.1f}. Response quality: {quality_score:.2f}."
    if quality_notes:
        notes += " Issues: " + " ".join(quality_notes)

    return total, notes


def grade_hard(action: Dict[str, Any], email: Dict[str, Any], step: int) -> Tuple[float, str]:
    """
    Grade a hard task: multi-step.
    Step 1 - classify (20%)
    Step 2 - respond (40%)
    Step 3 - escalate/resolve correctly (40%)

    step: 1, 2, or 3
    """
    reqs = email.get("response_requirements", {})

    if step == 1:
        # Classification step
        if action.get("action_type") != "classify":
            return 0.0, "Step 1: Use 'classify' to categorize the email."
        predicted = action.get("category")
        correct = email["correct_category"]
        acceptable = email.get("acceptable_categories", [correct])
        if predicted == correct:
            return 0.2, "Step 1 complete: Correct classification (+0.2)."
        elif predicted in acceptable:
            return 0.1, f"Step 1 partial: '{predicted}' acceptable but '{correct}' is better (+0.1)."
        else:
            return 0.0, f"Step 1 failed: '{predicted}' is incorrect."

    elif step == 2:
        # Response step
        if action.get("action_type") != "respond":
            return 0.0, "Step 2: Use 'respond' with a response_text."
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

        total = round(score, 3)
        feedback = f"Step 2 response score: +{total:.3f}."
        if notes:
            feedback += " Issues: " + "; ".join(notes) + "."
        return total, feedback

    elif step == 3:
        # Final decision step
        correct_action = email.get("correct_final_action", "resolve")
        taken_action = action.get("action_type")

        if taken_action == correct_action:
            if taken_action == "escalate":
                # Check escalation reasoning quality
                reason = (action.get("escalation_reason") or "").lower()
                escalation_keywords = email.get("escalation_reasons", [])
                if escalation_keywords:
                    found = sum(1 for kw in escalation_keywords if kw.lower() in reason)
                    quality = found / len(escalation_keywords)
                    score = round(0.3 + 0.1 * quality, 3)
                    return score, f"Step 3: Correct escalation! Reasoning quality: {quality:.0%}. (+{score:.3f})"
                return 0.4, "Step 3: Correct escalation with reason provided. (+0.4)"
            else:
                # Resolve
                summary = action.get("resolution_summary") or ""
                if summary and len(summary.split()) >= 10:
                    return 0.4, "Step 3: Correct resolution with good summary. (+0.4)"
                return 0.3, "Step 3: Correct resolution but summary too brief. (+0.3)"
        else:
            # Wrong final action
            if correct_action == "escalate" and taken_action == "resolve":
                return 0.0, (
                    f"Step 3 failed: Should have escalated (legal risk / complexity) but resolved. "
                    f"Correct action: 'escalate'."
                )
            elif correct_action == "resolve" and taken_action == "escalate":
                return 0.1, (
                    "Step 3 partial: Escalated unnecessarily. This simple issue could be resolved directly."
                )
            return 0.0, f"Step 3 failed: Wrong action '{taken_action}'. Expected '{correct_action}'."

    return 0.0, "Unknown step."


def run_all_graders(task_id: str) -> Dict[str, Any]:
    """
    Utility to verify all graders function correctly by running dummy actions.
    Returns a dict summarizing grader smoke-test results.
    """
    from tasks import TASKS

    results = {}
    emails = TASKS[task_id]["emails"]

    for email in emails:
        eid = email["id"]

        if task_id == "easy":
            # Test perfect action
            score, msg = grade_easy(
                {"action_type": "classify", "category": email["correct_category"]},
                email,
            )
            results[eid] = {"score": score, "msg": msg, "in_range": 0.0 <= score <= 1.0}

        elif task_id == "medium":
            reqs = email.get("response_requirements", {})
            keywords = reqs.get("must_include", ["hello"])
            response = " ".join(keywords) + " " * 100  # minimal passing response
            score, msg = grade_medium(
                {
                    "action_type": "respond",
                    "category": email["correct_category"],
                    "response_text": response,
                },
                email,
            )
            results[eid] = {"score": score, "msg": msg, "in_range": 0.0 <= score <= 1.0}

        elif task_id == "hard":
            score, msg = grade_hard(
                {"action_type": "classify", "category": email["correct_category"]},
                email,
                step=1,
            )
            results[eid] = {"score": score, "msg": msg, "in_range": 0.0 <= score <= 1.0}

    return results


if __name__ == "__main__":
    import json
    for t in ["easy", "medium", "hard"]:
        print(f"\n=== {t.upper()} grader test ===")
        r = run_all_graders(t)
        print(json.dumps(r, indent=2))
