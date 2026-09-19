
import streamlit as st
from workflow import generate_study_pack, WorkflowError


st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="📚",
    layout="wide",
)


# ---------------------------
# Styling
# ---------------------------
st.markdown(
    """
    <style>
    .main-title {
        text-align: center;
        font-size: 44px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 17px;
        margin-bottom: 30px;
    }

    .workflow-card {
        padding: 16px;
        border-radius: 16px;
        border: 1px solid rgba(128,128,128,.25);
        margin-bottom: 10px;
    }

    .stage-title {
        font-weight: 700;
        font-size: 17px;
    }

    .small-text {
        color: #6b7280;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------
# Header
# ---------------------------
st.markdown(
    '<div class="main-title">📚 AI Study Pack Generator</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Plan → Generate → Assess → Review → Refine"
    "</div>",
    unsafe_allow_html=True,
)


# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.header("⚙️ Study Settings")

    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        help="For deployment, store this in Streamlit Secrets instead.",
    )

    # Prefer Streamlit Secret when available.
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            api_key = ""

    level = st.selectbox(
        "Student Level",
        ["Beginner", "Intermediate", "Advanced"],
    )

    goal = st.text_input(
        "Learning Goal",
        value="Prepare for an exam",
    )

    study_days = st.slider(
        "Study Duration (days)",
        min_value=1,
        max_value=30,
        value=7,
    )

    selected_sections = st.multiselect(
        "Study Pack Sections",
        [
            "Summary",
            "Key Concepts",
            "Flashcards",
            "MCQs",
            "Short Questions",
            "Study Plan",
        ],
        default=[
            "Summary",
            "Key Concepts",
            "Flashcards",
            "MCQs",
            "Short Questions",
            "Study Plan",
        ],
    )


# ---------------------------
# User input
# ---------------------------
st.markdown("### 🎯 Create Your Personalized Study Pack")

topic = st.text_input(
    "📖 Topic",
    placeholder="e.g. Object Oriented Programming",
)

instructions = st.text_area(
    "📝 Additional Instructions",
    placeholder=(
        "Example: Keep explanations simple and focus on university exam preparation."
    ),
)

generate = st.button(
    "✨ Generate Study Pack",
    type="primary",
    use_container_width=True,
)


# ---------------------------
# Workflow UI
# ---------------------------
stage_names = [
    "Planning",
    "Content Generation",
    "Assessment",
    "Review",
    "Refinement",
]


def render_workflow(statuses):
    st.markdown("### 🤖 AI Workflow")

    cols = st.columns(5)

    for index, stage in enumerate(stage_names):
        status = statuses.get(stage, "waiting")

        if status == "complete":
            icon = "✅"
            message = "Complete"
        elif status == "running":
            icon = "🔄"
            message = "Running..."
        elif status == "error":
            icon = "❌"
            message = "Failed"
        else:
            icon = "⏳"
            message = "Waiting"

        with cols[index]:
            st.markdown(
                f"""
                <div class="workflow-card">
                    <div class="stage-title">{icon} {stage}</div>
                    <div class="small-text">{message}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------
# Generate
# ---------------------------
if generate:
    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()

    if not api_key:
        st.error(
            "Gemini API key is missing. Add it in the sidebar or configure "
            "GEMINI_API_KEY in Streamlit Secrets."
        )
        st.stop()

    if not selected_sections:
        st.warning("Select at least one study-pack section.")
        st.stop()

    statuses = {stage: "waiting" for stage in stage_names}

    workflow_placeholder = st.empty()

    def progress_callback(stage, status):
        statuses[stage] = status
        workflow_placeholder.empty()

        with workflow_placeholder.container():
            render_workflow(statuses)

    with st.spinner("Starting the AI workflow..."):
        try:
            result = generate_study_pack(
                api_key=api_key,
                topic=topic,
                level=level,
                goal=goal,
                study_days=study_days,
                selected_sections=selected_sections,
                instructions=instructions,
                progress_callback=progress_callback,
            )

        except WorkflowError as exc:
            for stage in stage_names:
                if statuses.get(stage) == "running":
                    statuses[stage] = "error"

            workflow_placeholder.empty()
            with workflow_placeholder.container():
                render_workflow(statuses)

            st.error(str(exc))
            st.stop()

        except Exception as exc:
            for stage in stage_names:
                if statuses.get(stage) == "running":
                    statuses[stage] = "error"

            workflow_placeholder.empty()
            with workflow_placeholder.container():
                render_workflow(statuses)

            st.error(f"Unexpected application error: {exc}")
            st.stop()

    # ---------------------------
    # Results
    # ---------------------------
    st.success("🎉 Your personalized study pack is ready!")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📚 Final Study Pack",
            "🧭 AI Plan",
            "❓ Assessment",
            "🔍 Review",
            "🧠 Workflow Context",
        ]
    )

    with tab1:
        st.markdown(result["final_pack"])

        st.download_button(
            label="⬇️ Download Study Pack",
            data=result["final_pack"],
            file_name=f"{topic.strip().replace(' ', '_')}_study_pack.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with tab2:
        st.json(result["plan"])

    with tab3:
        st.markdown(result["assessment"])

    with tab4:
        review = result["review"]

        status = review.get("overall_status", "unknown")

        if status == "pass":
            st.success("✅ Review status: PASS")
        else:
            st.warning("⚠️ Review status: NEEDS IMPROVEMENT")

        if review.get("issues"):
            st.markdown("#### Issues")
            for issue in review["issues"]:
                st.write(
                    f"**{issue.get('type', 'Issue')}** — "
                    f"{issue.get('description', '')}"
                )
        else:
            st.write("No major issues were identified.")

        if review.get("improvements"):
            st.markdown("#### Improvements")
            for item in review["improvements"]:
                st.write(f"- {item}")

        if review.get("priority_fixes"):
            st.markdown("#### Priority Fixes")
            for item in review["priority_fixes"]:
                st.write(f"- {item}")

    with tab5:
        st.markdown("#### Content generated before refinement")
        st.markdown(result["content"])

        st.divider()

        st.markdown("#### Final assessment context")
        st.markdown(result["assessment"])


st.divider()

st.caption(
    "AI-generated educational material should be checked against your course "
    "notes, textbook, or instructor material."
)
