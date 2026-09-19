
"""
Prompt templates for the multi-stage AI Study Pack workflow.

The prompts intentionally keep each AI stage focused:
1. Planning
2. Content generation
3. Assessment
4. Review
5. Refinement
"""


def build_planning_prompt(user_input):
    return f"""
You are the Planning Agent in a personalized AI Study Pack Generator.

Create a learning plan for:
Topic: {user_input["topic"]}
Student level: {user_input["level"]}
Goal: {user_input["goal"]}
Study duration: {user_input["study_days"]} days
Requested sections: {", ".join(user_input["selected_sections"])}
Additional instructions: {user_input["instructions"] or "None"}

Your job is ONLY to plan the study pack. Do not write the actual study notes.

Return ONLY valid JSON using exactly this structure:
{{
  "title": "short study pack title",
  "difficulty": "Beginner, Intermediate, or Advanced",
  "learning_objectives": [
    "objective 1",
    "objective 2"
  ],
  "sections": [
    {{
      "name": "section name",
      "purpose": "what this section should teach",
      "priority": "high, medium, or low"
    }}
  ],
  "study_sequence": [
    "first topic to study",
    "second topic to study"
  ],
  "common_mistakes": [
    "mistake 1",
    "mistake 2"
  ]
}}

Make the plan realistic, logically ordered, personalized to the student's level,
and suitable for the stated goal.
"""


def build_content_prompt(user_input, plan):
    return f"""
You are the Content Generation Agent in a multi-stage AI Study Pack Generator.

USER CONTEXT:
Topic: {user_input["topic"]}
Level: {user_input["level"]}
Goal: {user_input["goal"]}
Study duration: {user_input["study_days"]} days
Requested sections: {", ".join(user_input["selected_sections"])}
Additional instructions: {user_input["instructions"] or "None"}

PLANNER OUTPUT:
{plan}

Create the actual learning material based on the planner output.

Include only the requested sections and make the material appropriate for
the student's level.

Requirements:
- Explain concepts clearly.
- Use accurate terminology.
- Prioritize important exam/revision concepts.
- Use examples where useful.
- Avoid unnecessary repetition.
- Do not create the MCQs or final assessment yet.
- Use clean Markdown headings.
- Do not mention that you are an AI agent.

The content must be detailed enough to support the later assessment stage.
"""


def build_assessment_prompt(user_input, plan, content):
    return f"""
You are the Assessment Agent in a multi-stage AI Study Pack Generator.

USER CONTEXT:
Topic: {user_input["topic"]}
Level: {user_input["level"]}
Goal: {user_input["goal"]}

PLANNER OUTPUT:
{plan}

GENERATED CONTENT:
{content}

Create an assessment based ONLY on the topic and generated content.

Include:
1. 10 multiple-choice questions.
2. 5 short-answer questions.
3. Correct answers.
4. A brief explanation for every MCQ answer.

Requirements:
- Match the student's level.
- Test understanding, not only memorization.
- Do not introduce unrelated concepts.
- Avoid ambiguous questions.
- Make sure each MCQ has exactly four options: A, B, C, D.
- Use clean Markdown.
"""


def build_review_prompt(user_input, plan, content, assessment):
    return f"""
You are the Review Agent in a multi-stage AI Study Pack Generator.

Your task is quality control. Do not rewrite the study pack.

USER CONTEXT:
Topic: {user_input["topic"]}
Level: {user_input["level"]}
Goal: {user_input["goal"]}

PLANNER:
{plan}

CONTENT:
{content}

ASSESSMENT:
{assessment}

Check:
- Topic relevance
- Coverage of the planner objectives
- Factual consistency
- Difficulty appropriateness
- Missing important concepts
- Repetition
- Assessment quality
- Whether answers match the questions/content

Return ONLY valid JSON:
{{
  "overall_status": "pass or needs_improvement",
  "issues": [
    {{
      "type": "accuracy, coverage, difficulty, assessment, clarity, or other",
      "description": "specific issue"
    }}
  ],
  "improvements": [
    "specific improvement 1",
    "specific improvement 2"
  ],
  "priority_fixes": [
    "most important fix"
  ]
}}

If there are no meaningful issues, use an empty list for issues and improvements.
"""


def build_refinement_prompt(user_input, plan, content, assessment, review):
    return f"""
You are the Refinement Agent and final editor.

Create the FINAL personalized study pack using all available context.

USER CONTEXT:
Topic: {user_input["topic"]}
Level: {user_input["level"]}
Goal: {user_input["goal"]}
Study duration: {user_input["study_days"]} days
Requested sections: {", ".join(user_input["selected_sections"])}
Additional instructions: {user_input["instructions"] or "None"}

PLANNER:
{plan}

CONTENT:
{content}

ASSESSMENT:
{assessment}

REVIEW:
{review}

Instructions:
- Apply the review's valid corrections.
- Preserve correct material.
- Remove or fix inaccurate, confusing, or repetitive material.
- Keep the difficulty appropriate.
- Make the final pack easy to study.
- Include the requested study sections.
- Include the assessment with answers.
- Include a practical {user_input["study_days"]}-day study plan.
- Use Markdown headings.
- Do not mention internal agents, prompts, workflow, or review instructions.
- Do not claim that information is verified against external sources.
- Do not invent citations or references.

Return ONLY the finished study pack.
"""
