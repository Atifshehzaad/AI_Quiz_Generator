# quiz_generator.py
import os
import random
import json
from typing import List, Dict

# Try OpenAI first (recommended)
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# If you want HF fallback uncomment and install transformers in requirements
# try:
#     from transformers import pipeline
#     HF_AVAILABLE = True
# except Exception:
#     HF_AVAILABLE = False

def _openai_generate(prompt: str, max_tokens=800, temperature=0.7):
    """
    Use OpenAI to generate text. Ensure OPENAI_API_KEY is in environment or Streamlit secrets.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # In Streamlit, user can place key in st.secrets["OPENAI_API_KEY"]
        raise RuntimeError("OpenAI API key not found in environment (OPENAI_API_KEY).")
    openai.api_key = api_key
    resp = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        n=1,
        stop=None
    )
    return resp.choices[0].text

def _simple_fallback_generate(subject, level, difficulty, n=10):
    """
    Deterministic fallback generator: creates question templates and shuffles.
    Not as rich as an LLM, but works offline.
    """
    base_questions = []
    # Create template banks for some subjects. Expand as needed.
    if subject.lower() in ["python", "programming","python programming"]:
        templates = [
            ("What is the output of the following Python expression: `len('{s}')` ?", ["A: 1","B: 2","C: len('{s}')","D: runtime error"], "A"),
            ("Which statement creates a function in Python?", ["A: func x():", "B: def f():", "C: function f()", "D: f := lambda"], "B"),
            ("Which data type is immutable in Python?", ["A: list","B: dict","C: tuple","D: set"], "C"),
            ("How do you start a for-loop over list `L`?", ["A: for i in L:","B: for i = 0; i < L; i++","C: foreach L as i","D: loop(L)"], "A"),
            ("What keyword is used to create a class in Python?", ["A: create","B: class","C: struct","D: def"], "B"),
        ]
    else:
        # Generic knowledge questions
        templates = [
            ("Which choice best defines {s}?", ["A: Option 1","B: Option 2","C: Option 3","D: Option 4"], "A"),
            ("What is a key concept in {s}?", ["A: Concept A","B: Concept B","C: Concept C","D: Concept D"], "B"),
        ]

    for i in range(n):
        t = random.choice(templates)
        q = t[0].format(s=subject)
        opts = t[1]
        correct = t[2]
        # shuffle options while tracking correct label (for simplicity keep as-is)
        base_questions.append({
            "question": q,
            "options": opts,
            "answer": correct  # letter like "A", "B", ...
        })
    return base_questions

def parse_llm_output_to_questions(llm_text: str, n=10) -> List[Dict]:
    """
    Try to parse LLM output into structured questions.
    This is heuristic-based; LLM prompts should output numbered Q + options + ANSWER: format.
    """
    questions = []
    lines = [l.strip() for l in llm_text.splitlines() if l.strip()]
    cur = {}
    for line in lines:
        # detect "1." style question lines
        if line[0].isdigit() and ('.' in line[:3] or ')' in line[:3]):
            # start new
            if cur:
                questions.append(cur)
            qtext = line.split('.',1)[1].strip()
            cur = {"question": qtext, "options": [], "answer": None}
        elif line.upper().startswith(("A:", "B:", "C:", "D:")):
            # option
            cur.setdefault("options", []).append(line)
        elif line.upper().startswith("ANSWER") or line.upper().startswith("CORRECT"):
            # Answer line like "Answer: B"
            parts = line.split(":")
            if len(parts) > 1:
                ans = parts[1].strip().split()[0]
                cur["answer"] = ans
        else:
            # sometimes question spans lines
            if cur and "options" not in cur:
                cur["question"] += " " + line
    if cur:
        questions.append(cur)

    # keep first n and ensure each has 4 options; fallback otherwise
    final = []
    for q in questions[:n]:
        opts = q.get("options", [])
        if len(opts) < 4:
            # generate filler options
            while len(opts) < 4:
                opts.append(f"X: Option {len(opts)+1}")
        final.append({
            "question": q.get("question",""),
            "options": opts[:4],
            "answer": q.get("answer","A")
        })
    return final

def generate_quiz(subject: str, level: str, difficulty: str, n: int = 10) -> List[Dict]:
    """
    Public function to generate quiz. Returns list of dicts:
    { "question": str, "options": [str,str,str,str], "answer": "A" }
    """
    # If OpenAI is available, attempt LLM generation
    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        prompt = f"""
You will generate {n} multiple-choice questions on the subject: {subject}.
Level: {level}. Difficulty: {difficulty}.
Format the output strictly like:
1. Question text?
A: option text
B: option text
C: option text
D: option text
Answer: B

Repeat for 1..{n}. Ensure exactly one correct option (A/B/C/D) per question.
"""
        try:
            text = _openai_generate(prompt, max_tokens=900)
            questions = parse_llm_output_to_questions(text, n=n)
            if len(questions) >= n:
                return questions[:n]
            # else fallback
        except Exception as e:
            print("OpenAI generation failed:", e)

    # Fallback generator
    return _simple_fallback_generate(subject, level, difficulty, n=n)
