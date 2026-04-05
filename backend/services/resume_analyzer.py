import os
import json
import PyPDF2
import docx
from google import genai
from dotenv import load_dotenv
from database import get_db

# Ensure environment is loaded right here
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

client = None

def extract_text(file_stream, filename):
    text = ""
    try:
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file_stream)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        elif lower_name.endswith(".docx"):
            doc = docx.Document(file_stream)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            return None
        
        # Strip excessive spaces securely
        text = " ".join(text.split())
        return text
    except Exception as e:
        print(f"[RESUME ANALYZER] Extraction error: {e}")
        return None

def analyze_resume(text):
    global client
    try:
        if client is None:
            api_key = os.environ.get("GEMINI_API_KEY")
            print("[DEBUG] GEMINI KEY:", "Found" if api_key else "Missing")
            if not api_key:
                return None
            client = genai.Client(api_key=api_key)
            
        prompt = f"""
You are an AI resume analyzer.

Extract the following and return ONLY valid JSON:

* skills (list)
* experience (fresher/intermediate/experienced)
* roles (list)

DO NOT include explanation.
DO NOT include markdown.
DO NOT include ```json.

Resume:
{text}
"""
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
        except Exception as e:
            print(f"GEMINI ERROR: {e}")
            return {"skills": [], "experience": "Unknown", "roles": []}
        
        print("RAW GEMINI RESPONSE:", response.text)
        content = response.text.strip()
        
        # Robustly clean markdown wrappers dynamically
        content = content.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(content)
        except:
            print("RAW:", content)
            return {
                "skills": [],
                "experience": "Unknown",
                "roles": []
            }
        
        # Normalize skills into lowercase standard arrays 
        if "skills" in data and isinstance(data["skills"], list):
            data["skills"] = [s.lower().strip() for s in data["skills"]]
            
        return data
    except Exception as e:
        print("GEMINI ERROR:", e)
        return None

def match_jobs(user_skills):
    conn = get_db()
    matched_jobs = []
    
    try:
        # Avoid circular imports for job bindings
        from routes.jobs import job_to_dict
        
        rows = conn.execute("SELECT * FROM jobs WHERE is_active = 1").fetchall()
        user_skills_set = set(s.lower() for s in user_skills)
        
        for job in rows:
            job_skills_raw = job.get('skills')
            job_skills = []
            if job_skills_raw:
                try:
                    job_skills = json.loads(job_skills_raw)
                except Exception:
                    job_skills = [s.strip() for s in job_skills_raw.split(',')]
            
            req_skills_set = set(s.lower() for s in job_skills)
            
            if not req_skills_set:
                score = 0
                missing = []
            else:
                intersect = user_skills_set.intersection(req_skills_set)
                score = len(intersect) / len(req_skills_set)
                missing = list(req_skills_set - user_skills_set)
            
            if score > 0 or not req_skills_set:
                matched_jobs.append({
                    "job": job_to_dict(job),
                    "score": round(score * 100),
                    "missing_skills": missing
                })
                
        # Highest matched items sorted at the top (limited up to top 5 hits)
        matched_jobs.sort(key=lambda x: x["score"], reverse=True)
        return matched_jobs[:5]
    finally:
        conn.close()
