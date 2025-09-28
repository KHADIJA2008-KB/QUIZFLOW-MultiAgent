"""
Production-ready FastAPI backend for QuizFlow
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from quizflow.crew import QuizflowCrew

# Initialize FastAPI app
app = FastAPI(
    title="QuizFlow API",
    description="Production-ready AI quiz platform",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG", "false").lower() == "true" else None,
    redoc_url=None
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Initialize data directory and crew
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(exist_ok=True)
crew_instance = QuizflowCrew()

# Pydantic models
class SubjectRequest(BaseModel):
    subject: str

class QuizAnswers(BaseModel):
    user_id: Optional[str] = None
    quiz_id: str
    answers: Dict[str, str]

class QuizSession(BaseModel):
    session_id: str
    subject: str
    status: str
    created_at: str
    quiz_data: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

# In-memory storage (use Redis/DB in production)
quiz_sessions: Dict[str, QuizSession] = {}
quiz_results: Dict[str, Dict[str, Any]] = {}  # session_id -> results

# Subject categories
SUBJECTS = [
    "Computer Science", "Python Programming", "JavaScript Programming",
    "Artificial Intelligence & Machine Learning", "Data Science",
    "Cybersecurity", "Cloud Computing", "Database Management",
    "Operating Systems", "Computer Networks", "Software Engineering"
]

@app.get("/")
async def health_check():
    """API health check"""
    return {
        "message": "QuizFlow API is running!",
        "version": "1.0.0",
        "status": "healthy",
        "subjects_available": len(SUBJECTS)
    }

@app.get("/subjects")
async def get_subjects():
    """Get available quiz subjects"""
    return {"subjects": SUBJECTS}

@app.post("/generate-quiz")
async def generate_quiz(request: SubjectRequest, background_tasks: BackgroundTasks):
    """Start quiz generation"""
    if request.subject not in SUBJECTS:
        raise HTTPException(status_code=400, detail="Invalid subject")
    
    session_id = str(uuid.uuid4())
    session = QuizSession(
        session_id=session_id,
        subject=request.subject,
        status="generating",
        created_at=datetime.now().isoformat()
    )
    quiz_sessions[session_id] = session
    
    background_tasks.add_task(generate_quiz_background, session_id, request.subject)
    
    return {
        "session_id": session_id,
        "status": "generating",
        "message": f"Quiz generation started for {request.subject}",
        "estimated_time_minutes": 4
    }

async def generate_quiz_background(session_id: str, subject: str):
    """Background quiz generation"""
    try:
        print(f"🚀 Generating quiz for {subject} (Session: {session_id})")
        quiz_data = crew_instance.generate_quiz_for_subject(subject)
        
        if session_id in quiz_sessions:
            quiz_sessions[session_id].status = "ready"
            quiz_sessions[session_id].quiz_data = quiz_data
            print(f"✅ Quiz ready for session {session_id}")
    except Exception as e:
        print(f"❌ Quiz generation failed for {session_id}: {e}")
        if session_id in quiz_sessions:
            quiz_sessions[session_id].status = "failed"
            quiz_sessions[session_id].error_message = str(e)

@app.get("/quiz-status/{session_id}")
async def get_quiz_status(session_id: str):
    """Get quiz generation status"""
    if session_id not in quiz_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = quiz_sessions[session_id]
    return {
        "session_id": session_id,
        "status": session.status,
        "subject": session.subject,
        "created_at": session.created_at,
        "error_message": session.error_message
    }

@app.get("/quiz/{session_id}")
async def get_quiz(session_id: str):
    """Get generated quiz"""
    if session_id not in quiz_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = quiz_sessions[session_id]
    
    if session.status == "generating":
        raise HTTPException(status_code=202, detail="Quiz still generating")
    elif session.status == "failed":
        raise HTTPException(status_code=500, detail=f"Generation failed: {session.error_message}")
    elif session.status != "ready":
        raise HTTPException(status_code=400, detail="Invalid session status")
    
    if not session.quiz_data:
        raise HTTPException(status_code=404, detail="Quiz data not found")
    
    return session.quiz_data

@app.post("/submit-answers")
async def submit_answers(answers: QuizAnswers):
    """Submit and evaluate quiz answers"""
    if answers.quiz_id not in quiz_sessions:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    
    session = quiz_sessions[answers.quiz_id]
    if session.status != "ready":
        raise HTTPException(status_code=400, detail="Quiz not ready")
    
    try:
        user_answers = {
            "user_id": answers.user_id or "anonymous",
            "quiz_id": answers.quiz_id,
            **answers.answers
        }
        
        results = crew_instance.evaluate_user_answers(user_answers)
        session.status = "completed"
        session.results = results
        
        # Store results in separate dictionary for easy retrieval
        quiz_results[answers.quiz_id] = results
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.get("/history")
async def get_quiz_history():
    """Get quiz session history"""
    sessions = [
        {
            "session_id": sid,
            "subject": session.subject,
            "status": session.status,
            "created_at": session.created_at
        }
        for sid, session in quiz_sessions.items()
    ]
    sessions.sort(key=lambda x: x["created_at"], reverse=True)
    return {"sessions": sessions}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete quiz session"""
    if session_id not in quiz_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del quiz_sessions[session_id]
    return {"message": "Session deleted"}

@app.get("/results/{session_id}")
async def get_quiz_results(session_id: str):
    """Get quiz results for a completed session"""
    if session_id not in quiz_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = quiz_sessions[session_id]
    
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Quiz not completed yet")
    
    # Check session results first
    if session.results:
        return session.results
    
    # Check separate results storage
    if session_id in quiz_results:
        return quiz_results[session_id]
    
    # Try to load from session-specific results file
    try:
        session_results_file = DATA_DIR / f"results_{session_id}.json"
        if session_results_file.exists():
            with open(session_results_file, 'r') as f:
                stored_results = json.load(f)
                return stored_results
    except Exception as e:
        print(f"Error loading session results file: {e}")
    
    # Try to load from general results file as fallback
    try:
        results_file = DATA_DIR / "results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                stored_results = json.load(f)
                return stored_results
    except Exception as e:
        print(f"Error loading general results file: {e}")
    
    raise HTTPException(status_code=404, detail="Results not found")

def start_server():
    """Start the production server"""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "quizflow.api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()