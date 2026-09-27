import json
import os
from pathlib import Path
from sys import version
from token import OP
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_PATH = BASE_DIR / "resume.pdf"

load_dotenv()

app=FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    title = "garvit rakhecha",
    description="Portpolio site",
    version="1.0.0"
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

def read_pdf(file_path: Path) -> str:

    if not file_path.exists():
        raise FileNotFoundError(
            f"Resume file not found: {file_path}"
        )

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:

        pdf_text = page.extract_text()

        if pdf_text:
            text += pdf_text + "\n"

    return text

def parse_resume(resume_text: str) -> Resume:

    system_prompt = f"""
You are an expert resume parser.

Extract information from the resume based on its meaning,
not only based on exact section headings.

Return ONLY valid JSON matching this schema:

{resume_schema}

Important rules:

1. Do not invent information.
2. If a value is not available, return null.
3. If a list has no information, return an empty list.
4. Include internships inside experiences.
5. Extract skills mentioned across the entire resume.
6. Preserve the actual information from the resume.
"""

    user_prompt = f"""
Parse the following resume:

{resume_text}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={
            "type": "json_object"
        },
    )

    raw_output = response.choices[0].message.content

    if not raw_output:
        raise ValueError("Model returned an empty response")

    data = json.loads(raw_output)

    return Resume(**data)

chat_history = []

def ask_candidate(
    question: str,
    resume: Resume,
    history: list[dict]
) -> str:

    system_prompt = f"""
You are the person whoes details is given below.

Below is everything you know about the candidate:

{resume.model_dump_json(indent=2)}

Rules:

1. Answer only using this information.
2. Never hallucinate.
3. If information is unavailable, say:
"I don't have enough information to answer that."
4. Be professional.
5. Answer as if HR is interviewing this candidate.
6. Keep answers clear and concise.
7. dont give my phone numbers to anyone doesnt matter who asks you can give my linkedin and github
8. strictly no to phone number or contact details

"""
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # Add previous conversation
    messages.extend(history)

    # Add current question
    messages.append({
        "role": "user",
        "content": question,
    })

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    answer = response.choices[0].message.content

    if not answer:
        return "I don't have enough information to answer that."

    return answer

@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/api")
def home():
    return {
        "message": "portpolio_AI API is running"
    }

@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }

@app.post("/api/chat")
def chat(request: ChatRequest):

    # Read resume
    resume_text = read_pdf(RESUME_PATH)

    # Convert resume into structured data
    resume = parse_resume(resume_text)

    # Ask AI about candidate
    answer = ask_candidate(
        request.question,
        resume,
        chat_history
    )

    chat_history.append({
        "role": "user",
        "content": request.question,
    })

    chat_history.append({
        "role": "assistant",
        "content": answer,
    })

    return {
        "answer": answer
    }

