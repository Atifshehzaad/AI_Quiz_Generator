import streamlit as st
import pandas as pd
import random
from transformers import pipeline

# Load AI model (same as in Colab)
quiz_gen = pipeline("text-generation", model="gpt2")

def generate_quiz(subject, level, difficulty):
    prompt = f"Generate 10 multiple choice questions with 4 options each on {subject} at {level} level, difficulty {difficulty}. Include the correct answer."
    quiz_text = quiz_gen(prompt, max_length=900, num_return_sequences=1)[0]['generated_text']
    
    # Basic question split
    questions = [q.strip() for q in quiz_text.split('\n') if '?' in q][:10]
    return questions

# --- Streamlit UI ---
st.title("🧠 AI Quiz Generator App")

st.sidebar.header("👤 User Details")
name = st.sidebar.text_input("Full Name")
email = st.sidebar.text_input("Email")
user_id = st.sidebar.text_input("Student ID")

st.sidebar.header("📚 Quiz Settings")
subject = st.sidebar.selectbox("Select Subject", ["Python", "AI", "Data Science", "Math", "C++"])
level = st.sidebar.selectbox("Select Level", ["Beginner", "Intermediate", "Advanced"])
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

if st.sidebar.button("Generate Quiz"):
    if not (name and email and user_id):
        st.warning("Please enter your details first.")
    else:
        with st.spinner("AI is generating your quiz..."):
            quiz = generate_quiz(subject, level, difficulty)
        st.success("✅ Quiz Generated!")
        st.session_state['quiz'] = quiz
        st.session_state['answers'] = {}

if 'quiz' in st.session_state:
    st.header(f"Quiz on {subject} ({level} - {difficulty})")
    for i, q in enumerate(st.session_state['quiz'], 1):
        st.session_state['answers'][i] = st.radio(f"{i}. {q}", ["A", "B", "C", "D"], key=f"q{i}")

    if st.button("Submit Quiz"):
        score = random.randint(5, 10)  # mock scoring for now
        st.success(f"🎯 Your Score: {score}/10")

        # Save result
        data = {
            "Name": name,
            "Email": email,
            "UserID": user_id,
            "Subject": subject,
            "Level": level,
            "Difficulty": difficulty,
            "Score": score
        }

        df = pd.DataFrame([data])
        df.to_csv("quiz_data.csv", mode='a', header=False, index=False)

        st.info("📄 Your quiz report has been saved!")
        st.download_button("Download Report", df.to_csv(index=False).encode(), "quiz_report.csv", "text/csv")
