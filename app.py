import os
import csv
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

HISTORY_FILE = BASE_DIR / "prompt_history.csv"
FEEDBACK_FILE = BASE_DIR / "feedback.csv"
MODEL = "gemini-flash-lite-latest"


def build_chat_prompt(experiment, messages):
    # Gives Gemini the experiment details plus the chat so far.
    text = "You are helping the user understand a prompt experiment.\n"
    text += f"Original prompt: {experiment['prompt']}\n"
    text += f"Original answer: {experiment['original_answer']}\n"
    if experiment["improve_mode"]:
        text += f"Improved prompt: {experiment['improved_prompt']}\n"
        text += f"Improved answer: {experiment['improved_answer']}\n"
    text += "\nConversation so far:\n"
    for message in messages:
        speaker = "User" if message["role"] == "user" else "Assistant"
        text += f"{speaker}: {message['content']}\n"
    text += "Assistant:"
    return text


st.set_page_config(
    page_title="PromptLab 🎀",
    page_icon="🎀",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #fff5fb, #f1eaff, #fff0f6);
    color: #49345f;
}
h1 {
    color: #8054b5 !important;
    text-align: center;
    font-family: Georgia, serif;
}
.subtitle {
    text-align: center;
    color: #8054b5 !important;
    font-size: 17px;
}
.stMarkdown p, .stMarkdown h2, .stMarkdown h3,
label, .stTextArea label, .stSelectSlider label {
    color: #49345f !important;
}
.stTextArea textarea, .stTextInput input {
    background: #fffaff !important;
    border: 1px solid #dfc8f5;
    border-radius: 15px;
    color: #49345f !important;
}
.stButton button, .stFormSubmitButton button {
    background: linear-gradient(90deg, #c18aff, #ed9ed0);
    color: #ffffff !important;
    border: 0;
    border-radius: 12px;
    font-weight: bold;
}
.stButton button p, .stFormSubmitButton button p {
    color: #ffffff !important;
}
.stAlert p {
    color: #49345f !important;
}
[data-testid="stExpander"] {
    background: #fffaff;
    border: 1px solid #dfc8f5;
    border-radius: 15px;
}
[data-testid="stExpander"] * {
    color: #49345f;
}
[data-testid="stChatMessage"] * {
    color: #49345f;
}
[data-testid="stBottom"] > div {
    background: transparent !important;
}
[data-testid="stChatInput"] {
    background: #fffaff !important;
    border: 1px solid #dfc8f5;
    border-radius: 15px;
}
[data-testid="stChatInput"] textarea {
    background: #fffaff !important;
    color: #49345f !important;
    -webkit-text-fill-color: #49345f !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #8054b5 !important;
    opacity: 0.7;
}
</style>
""", unsafe_allow_html=True)

st.title("🎀 PromptLab")

st.markdown(
    '<p class="subtitle">✨ Test • Compare • Create Better AI Prompts ✨</p>',
    unsafe_allow_html=True
)

st.markdown("### 💌 Let's test your prompt!")

prompt = st.text_area(
    "Your prompt",
    placeholder="✨ Ask me something interesting...",
    height=150
)

improve_mode = st.checkbox(
    "✨ Improve my prompt and compare both answers"
)

if st.button("💪 Test My Prompt"):
    if not prompt.strip():
        st.warning("💪 Please enter a prompt!")
    elif not os.getenv("GEMINI_API_KEY"):
        st.error("Gemini API key not found. Check your .env file.")
    else:
        try:
            client = genai.Client(
                api_key=os.getenv("GEMINI_API_KEY")
            )

            with st.spinner("💪 Generating the original answer..."):
                original_response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt
                )

            original_answer = (
                original_response.text or "No answer was returned."
            )
            improved_prompt = ""
            improved_answer = ""

            if improve_mode:
                with st.spinner("✨ Improving your prompt..."):
                    instruction = (
                        "Rewrite the user's prompt to make it clearer, "
                        "more specific, and effective. Return only the "
                        "improved prompt, not its answer:\n"
                    )
                    improved_response = client.models.generate_content(
                        model=MODEL,
                        contents=instruction + prompt
                    )
                    improved_prompt = improved_response.text or prompt

                with st.spinner("✨ Generating the improved answer..."):
                    final_response = client.models.generate_content(
                        model=MODEL,
                        contents=improved_prompt
                    )
                    improved_answer = (
                        final_response.text or "No answer was returned."
                    )

            # Save the experiment only after generation succeeds.
            history_exists = (
                HISTORY_FILE.exists() and HISTORY_FILE.stat().st_size > 0
            )

            with open(
                HISTORY_FILE,
                "a",
                newline="",
                encoding="utf-8"
            ) as history_file:
                writer = csv.DictWriter(
                    history_file,
                    fieldnames=[
                        "Date",
                        "Original Prompt",
                        "Original Answer",
                        "Improved Prompt",
                        "Improved Answer"
                    ]
                )

                if not history_exists:
                    writer.writeheader()

                writer.writerow({
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Original Prompt": prompt,
                    "Original Answer": original_answer,
                    "Improved Prompt": improved_prompt,
                    "Improved Answer": improved_answer
                })

            st.session_state["latest_experiment"] = {
                "prompt": prompt,
                "original_answer": original_answer,
                "improved_prompt": improved_prompt,
                "improved_answer": improved_answer,
                "improve_mode": improve_mode
            }
            # A new experiment starts a fresh follow-up chat.
            st.session_state["chat_messages"] = []

            st.success("Your experiment has been saved to history! 🎀")

        except Exception as error:
            st.error(f"Something went wrong: {error}")

# Show the latest experiment after Streamlit reruns.
experiment = st.session_state.get("latest_experiment")

if experiment:
    st.markdown("---")

    if experiment["improve_mode"]:
        # Display both answers side by side.
        original_col, improved_col = st.columns(2, gap="large")

        with original_col:
            st.markdown("## 🌸 Original Answer")
            st.markdown("**🌸 Original Prompt:**")
            st.info(experiment["prompt"])
            st.markdown("**💬 Original Answer:**")
            st.markdown(experiment["original_answer"])

        with improved_col:
            st.markdown("## 💪 Improved Answer")
            st.markdown("**✨ Improved Prompt:**")
            st.info(experiment["improved_prompt"])
            st.markdown("**✨ Improved Answer:**")
            st.markdown(experiment["improved_answer"])

        st.markdown("---")
        st.caption(
            "🤔 Compare both answers side by side to see how the prompt "
            "changes the response."
        )

    else:
        st.markdown("## 🌸 Original Prompt & Answer")
        st.markdown("**🌸 Original Prompt:**")
        st.info(experiment["prompt"])
        st.markdown("**💬 Original Answer:**")
        st.markdown(experiment["original_answer"])

    # Follow-up chat about the latest experiment.
    st.markdown("---")
    st.markdown("## 💬 Follow-Up Chat")
    st.caption("Ask more questions about this experiment. 🎀")

    st.session_state.setdefault("chat_messages", [])
    chat_area = st.container()

    with st.container():
        question = st.chat_input("Ask a follow-up question...")

    if question:
        if not os.getenv("GEMINI_API_KEY"):
            st.error("Gemini API key not found. Check your .env file.")
        else:
            messages = st.session_state["chat_messages"]
            messages.append({"role": "user", "content": question})

            try:
                client = genai.Client(
                    api_key=os.getenv("GEMINI_API_KEY")
                )
                with st.spinner("💭 Thinking..."):
                    chat_response = client.models.generate_content(
                        model=MODEL,
                        contents=build_chat_prompt(experiment, messages)
                    )
                reply = chat_response.text or "No answer was returned."
                messages.append({"role": "assistant", "content": reply})

            except Exception as error:
                messages.pop()  # Remove the question that failed.
                st.error(f"Something went wrong: {error}")

    with chat_area:
        for message in st.session_state["chat_messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

# Feedback and application rating.
st.markdown("---")
st.markdown("## 🍀 Help Us Improve PromptLab")
st.markdown(
    "Your feedback means a lot! 🎀 Tell us what you think "
    "and how we can make PromptLab better."
)

with st.form("feedback_form"):
    st.markdown("### ⭐ Rate PromptLab")

    if "selected_rating" not in st.session_state:
        st.session_state.selected_rating = 0

    st.caption("BRO JUST MOVE THE SLIDER TO RATE PROMPTLAB")

    rating_choice = st.select_slider(
        "⭐ Your rating",
        options=[1, 2, 3, 4, 5],
        value=(
            st.session_state.selected_rating
            if st.session_state.selected_rating in [1, 2, 3, 4, 5]
            else 5
        ),
        format_func=lambda value: "⭐" * value
    )

    feedback = st.text_area(
        "💭 What do you think about PromptLab?",
        placeholder="Tell us what you liked..."
    )

    suggestions = st.text_area(
        "🤔 What should we improve or add?",
        placeholder="Suggest new features or improvements..."
    )

    submitted = st.form_submit_button("💌 Submit Feedback")

    if submitted:
        if not feedback.strip() and not suggestions.strip():
            st.warning("💬 Please write some feedback or a suggestion.")
        else:
            try:
                file_exists = (
                    FEEDBACK_FILE.exists()
                    and FEEDBACK_FILE.stat().st_size > 0
                )

                with open(
                    FEEDBACK_FILE,
                    "a",
                    newline="",
                    encoding="utf-8"
                ) as file:
                    writer = csv.writer(file)

                    if not file_exists:
                        writer.writerow([
                            "Date", "Rating", "Feedback", "Suggestions"
                        ])

                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        rating_choice,
                        feedback.strip(),
                        suggestions.strip()
                    ])

                st.success(
                    f"Thank you for rating PromptLab "
                    f"{rating_choice}/5 ⭐🎀"
                )

            except OSError:
                st.error("Could not save feedback. Please try again.")

# Prompt history.
st.markdown("---")
st.markdown("## 🕒 Your Prompt History")
st.markdown(
    "Review previous experiments. Your history is saved locally. 💜"
)

if HISTORY_FILE.exists():
    try:
        with open(
            HISTORY_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as history_file:
            history = list(csv.DictReader(history_file))
    except (OSError, UnicodeDecodeError, csv.Error):
        history = []
        st.warning("Could not read prompt history.")
else:
    history = []

if history:
    st.caption(f"📚 Total experiments saved: {len(history)}")

    search = st.text_input(
        "🔎 Search your prompt history",
        placeholder="Search for a prompt or answer..."
    )

    filtered_history = [
        item for item in reversed(history)
        if search.strip().lower() in " ".join([
            item.get("Original Prompt", ""),
            item.get("Original Answer", ""),
            item.get("Improved Prompt", ""),
            item.get("Improved Answer", "")
        ]).lower()
    ]

    if filtered_history:
        for index, item in enumerate(filtered_history):
            with st.expander(
                f"🌸 Experiment · {item.get('Date', 'Date unavailable')}"
            ):
                st.markdown("**Original Prompt:**")
                st.write(item.get("Original Prompt", ""))

                st.markdown("**Original Answer:**")
                st.write(item.get("Original Answer", ""))

                improved_prompt = item.get("Improved Prompt", "")
                improved_answer = item.get("Improved Answer", "")

                if improved_prompt:
                    st.markdown("**✨ Improved Prompt:**")
                    st.write(improved_prompt)

                if improved_answer:
                    st.markdown("**✨ Improved Answer:**")
                    st.write(improved_answer)

                st.download_button(
                    "📥 Download Original Answer",
                    data=item.get("Original Answer", ""),
                    file_name=f"prompt_experiment_{index + 1}.txt",
                    mime="text/plain",
                    key=f"download_original_{index}"
                )
    else:
        st.info("No matching experiments found. 🔎")
else:
    st.info("No prompt experiments saved yet. Try your first prompt above! 🌸")

st.markdown(
    '<p style="text-align:center;color:#8054b5;">'
    'Made by vai🎀🍀💪🥀</p>',
    unsafe_allow_html=True
)