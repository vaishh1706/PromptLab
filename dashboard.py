
import csv
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="PromptLab Feedback Dashboard",
    page_icon="🎀",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #fff0f6, #f3e8ff);
    color: #35213f;
}

.stApp h1, .stApp h2, .stApp h3,
.stApp p, .stApp label, .stApp span,
.stApp li, .stApp summary {
    color: #35213f !important;
}

[data-testid="stMetric"] {
    background: #ffffff;
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #e9b8d3;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    color: #35213f !important;
}

[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid #e9b8d3;
    border-radius: 12px;
}

[data-testid="stExpander"] * {
    color: #35213f !important;
}

.stProgress > div > div > div {
    background-color: #d66ba0;
}

/* Download button */
.stDownloadButton button {
    background-color: #d66ba0 !important;
    color: #ffffff !important;
    border: 2px solid #b84d83 !important;
    border-radius: 12px !important;
    font-weight: bold !important;
}

.stDownloadButton button p,
.stDownloadButton button span,
.stDownloadButton button div {
    color: #ffffff !important;
}

.stDownloadButton button:hover {
    background-color: #b84d83 !important;
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🎀 PromptLab Feedback Dashboard")
st.write("A little space to see how PromptLab is doing. 💗")

feedback_file = Path(__file__).parent / "feedback.csv"

if not feedback_file.exists():
    st.info("No feedback file yet. Submit feedback in PromptLab first!")
    st.stop()

try:
    with open(feedback_file, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        data = [
            {
                key.strip().lower(): (value or "").strip()
                for key, value in row.items()
                if key
            }
            for row in reader
        ]
except (OSError, UnicodeDecodeError, csv.Error):
    st.error("Could not read feedback.csv. Please check the file.")
    st.stop()

if not data:
    st.info("No feedback submitted yet.")
    st.stop()

ratings = []

for item in data:
    try:
        rating = float(item.get("rating", ""))
        if 1 <= rating <= 5:
            ratings.append(rating)
    except (ValueError, TypeError):
        pass

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📝 Total Feedback", len(data))

with col2:
    average = sum(ratings) / len(ratings) if ratings else 0
    st.metric(
        "⭐ Average Rating",
        f"{average:.1f}/5" if ratings else "No ratings yet"
    )

with col3:
    st.metric("🌸 Ratings Received", len(ratings))

st.divider()
st.subheader("📊 Visual Rating Chart")

if ratings:
    counts = {
        star: sum(1 for rating in ratings if rating == star)
        for star in range(1, 6)
    }

    chart_data = {
        "Rating": [f"{star} ⭐" for star in range(1, 6)],
        "Number of Responses": [counts[star] for star in range(1, 6)]
    }

    st.bar_chart(
        chart_data,
        x="Rating",
        y="Number of Responses",
        color="#d66ba0"
    )
else:
    st.info("Submit a star rating to see your chart here.")

st.divider()
st.subheader("⭐ Rating Breakdown")

if ratings:
    for star in range(5, 0, -1):
        count = sum(1 for rating in ratings if rating == star)
        st.write(f"**{star} stars** — {count}")
        st.progress(count / len(ratings))
else:
    st.info("No valid star ratings recorded yet.")

st.divider()
st.subheader("📥 Export Feedback")

try:
    csv_content = feedback_file.read_bytes()

    st.download_button(
        label="💗 Download Feedback as CSV",
        data=csv_content,
        file_name="promptlab_feedback.csv",
        mime="text/csv",
        use_container_width=True
    )
except OSError:
    st.error("Could not prepare the feedback download.")

st.divider()
st.subheader("💌 Feedback & Suggestions")

for number, item in enumerate(reversed(data), start=1):
    date = item.get("date", "") or "Date unavailable"
    rating = item.get("rating", "") or "Not provided"
    feedback = item.get("feedback", "")
    suggestion = item.get("suggestions", "")

    with st.expander(
        f"Feedback #{len(data) - number + 1} · ⭐ {rating} · {date}"
    ):
        st.markdown("**Feedback:**")
        st.write(feedback or "No written feedback.")

        st.markdown("**Suggestion:**")
        st.write(suggestion or "No suggestion provided.")

st.caption("Made by vai🎀🍀💪🥀 · Local dashboard")