import json
import re
import time
from google import genai

from prompt import (
    build_planning_prompt,
    build_content_prompt,
    build_assessment_prompt,
    build_review_prompt,
    build_refinement_prompt,
)

class WorkflowError(Exception):
    """Raised when an AI workflow stage fails."""
    pass

def _extract_json(text):
    """Extract a JSON object from an AI response."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise

def _call_ai(client, prompt_text, stage_name, retries=2):
    """Call Gemini using the new google-genai SDK structure."""
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt_text
            )
            if not response or not getattr(response, "text", None):
                raise ValueError("The AI returned an empty response.")
            return response.text.strip()
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    raise WorkflowError(f"{stage_name} failed after {retries + 1} attempts: {last_error}")

def planning_stage(client, user_input):
    raw = _call_ai(client, build_planning_prompt(user_input), "Planning stage")
    try:
        plan = _extract_json(raw)
    except Exception as exc:
        raise WorkflowError(f"Planning stage returned invalid JSON: {exc}")
    required = ["title", "learning_objectives", "sections", "difficulty"]
    missing = [key for key in required if key not in plan]
    if missing:
        raise WorkflowError(f"Planning stage is missing required fields: {', '.join(missing)}")
    return plan

def content_generation_stage(client, user_input, plan):
    raw = _call_ai(client, build_content_prompt(user_input, plan), "Content generation stage")
    if len(raw) < 100:
        raise WorkflowError("Content generation returned too little content.")
    return raw

def assessment_stage(client, user_input, plan, content):
    raw = _call_ai(client, build_assessment_prompt(user_input, plan, content), "Assessment stage")
    if len(raw) < 100:
        raise WorkflowError("Assessment generation returned too little content.")
    return raw

def review_stage(client, user_input, plan, content, assessment):
    raw = _call_ai(client, build_review_prompt(user_input, plan, content, assessment), "Review stage")
    try:
        review = _extract_json(raw)
    except Exception as exc:
        raise WorkflowError(f"Review stage returned invalid JSON: {exc}")
    required = ["overall_status", "issues", "improvements"]
    missing = [key for key in required if key not in review]
    if missing:
        raise WorkflowError(f"Review stage is missing required fields: {', '.join(missing)}")
    return review

def refinement_stage(client, user_input, plan, content, assessment, review):
    raw = _call_ai(client, build_refinement_prompt(user_input, plan, content, assessment, review), "Refinement stage")
    if len(raw) < 200:
        raise WorkflowError("Refinement returned too little content.")
    return raw

def generate_study_pack(api_key, topic, level, goal, study_days, selected_sections, instructions="", progress_callback=None):
    """Runs the complete sequential AI workflow."""
    if not api_key or not api_key.strip():
        raise WorkflowError("Gemini API key is missing.")
    if not topic or not topic.strip():
        raise WorkflowError("Topic is required.")

    # Initialize the new SDK client
    client = genai.Client(api_key=api_key.strip())

    user_input = {
        "topic": topic.strip(),
        "level": level,
        "goal": goal.strip() if goal else "General learning",
        "study_days": int(study_days),
        "selected_sections": selected_sections,
        "instructions": instructions.strip() if instructions else "",
    }

    def update(stage, status):
        if progress_callback:
            progress_callback(stage, status)

    update("Planning", "running")
    plan = planning_stage(client, user_input)
    update("Planning", "complete")

    update("Content Generation", "running")
    content = content_generation_stage(client, user_input, plan)
    update("Content Generation", "complete")

    update("Assessment", "running")
    assessment = assessment_stage(client, user_input, plan, content)
    update("Assessment", "complete")

    update("Review", "running")
    review = review_stage(client, user_input, plan, content, assessment)
    update("Review", "complete")

    update("Refinement", "running")
    final_pack = refinement_stage(client, user_input, plan, content, assessment, review)
    update("Refinement", "complete")

    return {
        "plan": plan,
        "content": content,
        "assessment": assessment,
        "review": review,
        "final_pack": final_pack,
    }
