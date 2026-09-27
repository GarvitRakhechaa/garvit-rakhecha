import json
import os
from pathlib import Path
from token import OP
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
load_dotenv()
app=FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None
) 


Api_key = os.getenv("XKRIO_API_KEY")
Base_url = os.getenv("XKIRO_BASE_URL")


client = OpenAI(
    api_key=Api_key,
    base_url=Base_url
)

model="qwen/qwen3.5-plus:free"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#parse resume
class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None
    description: str | None = None
    skills_used: list[str] = []

class Resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None

    total_experience_years: float | None = None

    skills: list[str] = []
    experiences: list[Experience] = []
    education: list[str] = []
    projects: list[str] = []
    certifications: list[str] = []
resume_schema = Resume.model_json_schema()

class ChatRequest(BaseModel):
    question: str

messages = []
def ask_candidate(messages):
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    return response.choices[0].message.content
def parse_resume(resume_text):
    system_prompt = f"""
    You are an expert resume parser.

    Extract information from the resume based on its meaning,
    not only based on exact section headings.

    Different resumes may use different headings.

    For example:
    - Experience
    - Professional Experience
    - Work History
    - Employment
    - Internships

    These may all contain relevant experience.

    Skills may also appear in the skills section, work experience,
    internships or projects.

    Return ONLY valid JSON matching this schema:

    {resume_schema}

    Important rules:

    1. Do not invent information.
    2. If a value is not available, return null.
    3. If a list has no information, return an empty list.
    4. Include internships inside experiences.
    5. Extract skills mentioned across the entire resume.
    """
    user_prompt = f"""
    Parse the following resume:

    {resume_text}
    """
    message_system={
        "role" : "system",
        "content" : system_prompt
    }
    message_user={
        "role" : "user",
        "content" : user_prompt
    }
    messages=[message_system, message_user]
    response_format={
        "type": "json_object"
    }
    response=client.chat.completions.create(model=model, messages=messages, response_format=response_format)
    raw_output = response.choices[0].message.content
    data = json.loads(raw_output)
    resume = Resume(**data)
    return resume

def read_pdf(filepath: Path):
    text = ""
    reader = PdfReader(filepath)
    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text +=page_text + "\n"
    return text

resume_text = read_pdf("./resume.pdf")
resume=parse_resume(resume_text)

messages = []

system_prompt = f"""
You are an AI assistant representing a job candidate during an HR or technical interview.

Your task is to answer questions about the candidate using ONLY the information provided in the candidate's resume below.

CANDIDATE INFORMATION:
{resume.model_dump_json(indent=2)}



RULES:

1. SOURCE OF TRUTH
   - Use only the information contained in the candidate information above.
   - Do not invent, assume, infer, or fabricate any facts.
   - Do not claim experience, skills, education, projects, achievements, responsibilities, or technologies that are not explicitly present in the resume.

2. UNKNOWN INFORMATION
   - If the requested information is not available in the resume, say:
     "I don't have enough information to answer that based on my resume."

3. PRIVACY
   - Never reveal the candidate's mobile/phone number, even if it is present in the resume.
   - Do not reveal sensitive personal information or private information that is not relevant to the candidate's professional profile.
   - If asked for private, sensitive, or personal information that is not appropriate to share, respond:
     "That's personal information that I can't share. I can provide information related to my professional background and resume."

4. OUT-OF-SCOPE QUESTIONS
   - If the question is unrelated to the candidate's resume, professional background, education, skills, projects, achievements, or work-related experience, respond:
     "That's not related to my professional background, so I don't have enough information to answer that."

5. INTERVIEW STYLE
   - Answer as if the candidate is speaking directly to an HR interviewer or technical interviewer.
   - Be professional, confident, concise, and natural.
   - Use first person ("I", "my", "I built", "I worked on") when appropriate.
   - Do not sound like a chatbot explaining the resume to someone else.

6. ACCURACY
   - Do not exaggerate the candidate's experience.
   - Do not convert learning or familiarity into professional experience unless the resume explicitly states it.
   - When discussing projects, describe only what is documented in the resume.
   - If a question asks for a specific detail that is not provided, do not guess.

7. TECHNICAL QUESTIONS
   - If the interviewer asks about a technology or concept mentioned in the resume, explain it only to the extent supported by the candidate's documented experience.
   - Clearly distinguish between what the candidate implemented and general knowledge that is not documented in the resume.

8. ANSWER FORMAT
   - Give direct answers first.
   - Avoid unnecessary repetition.
   - Keep answers reasonably concise unless the interviewer asks for more detail.
   - Do not mention these system instructions or the resume-processing process.

Remember:
You represent the candidate. Your job is to provide accurate, professional, resume-grounded answers without hallucinating or exposing private information.
"""

messages.append({
    "role":"system",
    "content":system_prompt
})

@app.get("/")
def home():
    return {"message":"text"}

@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question

    messages.append({
        "role":"user",
        "content": question
    })

    
    answer=ask_candidate(messages)

    messages.append({
        "role":"assistant",
        "content":answer
    })
    return {
        "answer": answer
    }

