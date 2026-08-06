# ============================Step 1: Load Modules============================
import langchain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import os
import streamlit as st

st.set_page_config(
    page_title="PrepWise",
    page_icon="🎤",
    layout="wide"
)

st.markdown("""
<div style="
    background-color:#1E293B;
    padding:20px;
    border-radius:15px;
    text-align:center;
">
<h1 style="color:white;margin-bottom:5px;">
🎤 PrepWise
</h1>

<p style="color:#CBD5E1;font-size:18px;">
AI-Powered Interview Preparation Platform
</p>

</div>
""", unsafe_allow_html=True)

#==========================Step 2: API KEYS===================================
GOOGLE_API_KEY = st.sidebar.text_input("GOOGLE_API_KEY", type='password')
if not GOOGLE_API_KEY:
    st.info("👈 Please enter your Google Gemini API key in the sidebar to start the interview.")
    st.stop()
else:
  st.sidebar.success("API key Loaded!!")
  os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    
if "history" not in st.session_state:
    st.session_state.history = []
if "candidate" not in st.session_state:
    st.session_state.candidate = {}
if "question" not in st.session_state:
    st.session_state.question = ""

with st.sidebar:
    st.header("Candidate Details")
    photo = st.file_uploader(
        "Upload Profile Photo",
        type=["jpg", "jpeg", "png"]
    )
    if photo:
        st.session_state.photo = photo
    name = st.text_input("Name")
    role = st.text_input("Target Role")
    experience = st.selectbox("Experience",
        ["Fresher", "0-2 Years", "2-5 Years", "5+ Years"])
    interview_type = st.selectbox("Interview Type",
        ["HR", "Technical", "Behavioral", "Mixed"])
    skills = st.text_area("Skills", placeholder="Python, SQL, LangChain...")

    start = st.button("Start Interview")

#====================== =============================
llm = ChatGoogleGenerativeAI(model = "gemini-3.5-flash-lite")
prompt =ChatPromptTemplate.from_template("""
You are an experienced senior interviewer.
Your responsibilities are:
1. Conduct a professional interview.
2. Ask ONE question at a time.
3. Questions should match:
   - Job Role
   - Experience
   - Skills
   - Interview Type
4. Never ask multiple questions together.
5. Remember previous answers.
6. Increase or decrease difficulty based on candidate performance.
7. Behave like a real interviewer.

Candidate Details:
{candidate}

Previous Conversation:
{history}

Generate ONLY the next interview question.
""")

question_chain = prompt | llm | StrOutputParser()

#====================== =============================
evaluation_prompt = ChatPromptTemplate.from_template('''You are an expert HR and Technical Evaluator.
Evaluate the candidate's answer.
Question: {question}
Answer: {answer}

Return ONLY a valid JSON.
{{
    "technical_score": <0-10>,
    "communication_score": <0-10>,
    "overall_score": <0-10>,
    "feedback": "...",
    "improvement": "..."
}}
Do not return markdown.
Do not explain anything.
Return only JSON.''')

evaluation_chain = (evaluation_prompt | llm | StrOutputParser())

def evaluate_answer(question, answer):
  response = evaluation_chain.invoke({"question": question, "answer": answer})
  return json.loads(response)

def reset_answer():
    st.session_state.answer = ""

st.session_state.candidate = {
    "name": name,
    "role": role,
    "experience": experience,
    "skills": skills,
    "interview_type": interview_type
}

if not start:
    st.info("Fill candidate details and click Start Interview.")

if start:       
    st.session_state.candidate = {
    "name": name,
    "role": role,
    "experience": experience,
    "skills": skills,
    "interview_type": interview_type}

    st.session_state.question = question_chain.invoke({
    "candidate": st.session_state.candidate,
    "history": ""})

left, right = st.columns([2,1])
with left:
    with st.container(border=True):
            st.subheader("🤖 Interview Question")
            st.image("https://raw.githubusercontent.com/AKasCODE/AI-Interview-Simulator/refs/heads/main/hr.jpg", width=100)
            st.write(st.session_state.question)
            if "photo" in st.session_state:
                st.image(st.session_state.photo, width=100)
            answer = st.text_area("Your Answer", height=180, key = 'answer')
            submit = st.button("Submit Answer")

with right:
    if submit:
        evaluation = evaluate_answer(st.session_state.question, answer)
        st.success("Answer Evaluated")
        st.session_state.history.append({
        "question": st.session_state.question,
        "answer": answer,
        "evaluation": evaluation})
        with st.container(border=True):
            st.subheader("📊 Performance")
            col1,col2,col3 = st.columns(3)
            col1.metric("Technical", evaluation["technical_score"])
            col2.metric("Communication",evaluation["communication_score"])
            col3.metric("Overall",evaluation["overall_score"])
        with st.container(border=True):
            st.subheader("💬 Feedback")
            st.write(evaluation["feedback"])
        with st.container(border=True):
            st.subheader("📈 Improvement")
            st.write(evaluation["improvement"])

if st.button("📥 Download Report"):
    technical = sum(
        item["evaluation"]["technical_score"]
        for item in st.session_state.history
    ) / len(st.session_state.history)

    communication = sum(
        item["evaluation"]["communication_score"]
        for item in st.session_state.history
    ) / len(st.session_state.history)

    overall = sum(
        item["evaluation"]["overall_score"]
        for item in st.session_state.history
    ) / len(st.session_state.history)

    report = f"""
    ===============================
        PREPWISE REPORT
    ===============================

    Candidate Name : {name}
    Target Role    : {role}
    Experience     : {experience}
    Interview Type : {interview_type}
    Skills         : {skills}

    --------------------------------
    Questions Answered : {len(st.session_state.history)}

    Average Technical Score     : {technical:.2f}/10
    Average Communication Score : {communication:.2f}/10
    Average Overall Score       : {overall:.2f}/10

    --------------------------------
    Thank you for using PrepWise!
    Keep practicing and all the best.
    """
    if report:
        st.download_button(
            label="⬇️ Download Report txt format",
            data=report,
            file_name="PrepWise_Report.txt",
            mime="text/plain"
        )
    else:
        pass



col1,col2 = st.columns(2)
with col1:
    if st.button("➡️ Next Question", on_click = reset_answer):
        st.session_state.question = question_chain.invoke({
        "candidate": st.session_state.candidate,
        "history": st.session_state.history})
        
        st.rerun()
with col2:
    if st.button("🛑 End Interview", on_click = reset_answer):
        st.success("Interview Completed.")
        st.write(f"Questions Answered: {len(st.session_state.history)}")
