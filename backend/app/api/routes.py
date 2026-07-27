from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.interview import InterviewSession, InterviewTurn
from app.schemas.interview import (
    AnswerRequest,
    AnswerResponse,
    QuestionResponse,
    RoleResponse,
    SessionCreateResponse,
    SessionSummaryResponse,
)
from app.services.question_generator import build_query, evaluate_answer, generate_question, summarize_session
from app.services.resume_parser import parse_resume
from app.services.text_processing import extract_profile
from app.services.vector_store import vector_store


router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/roles", response_model=RoleResponse)
def get_roles() -> RoleResponse:
    return RoleResponse(roles=vector_store.roles())

@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(
    target_role: str = Form(...),
    candidate_name: str | None = Form(None),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> SessionCreateResponse:
    if target_role not in vector_store.roles():
        raise HTTPException(status_code=400, detail=f"Unsupported role: {target_role}")

    resume_text = await parse_resume(resume)
    profile = extract_profile(resume_text)
    session = InterviewSession(
        candidate_name=candidate_name,
        target_role=target_role,
        resume_text=resume_text,
        extracted_profile=profile,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    first_turn = create_next_turn(db, session, last_score=None)
    return SessionCreateResponse(
        session_id=session.id,
        target_role=session.target_role,
        extracted_profile=session.extracted_profile,
        first_question=serialize_question(first_turn),
    )

@router.post("/sessions/{session_id}/turns/{turn_id}/answer", response_model=AnswerResponse)
def answer_question(
    session_id: int,
    turn_id: int,
    payload: AnswerRequest,
    db: Session = Depends(get_db),
) -> AnswerResponse:
    settings = get_settings()
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "completed":
        raise HTTPException(status_code=409, detail="Session is already completed")

    turn = db.get(InterviewTurn, turn_id)
    if not turn or turn.session_id != session_id:
        raise HTTPException(status_code=404, detail="Turn not found for session")
    if turn.answer:
        raise HTTPException(status_code=409, detail="Question already answered")

    score, feedback = evaluate_answer(payload.answer, turn.retrieved_context)
    turn.answer = payload.answer
    turn.answer_score = score
    turn.feedback = feedback
    turn.answered_at = datetime.utcnow()
    db.commit()
    db.refresh(session)

    answered_count = len([item for item in session.turns if item.answer])
    if answered_count >= settings.max_questions_per_session:
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        session.summary = summarize_session(session.turns, session.extracted_profile)
        db.commit()
        return AnswerResponse(
            saved_turn_id=turn.id,
            feedback=feedback,
            answer_score=score,
            next_question=None,
            session_complete=True,
        )
    next_turn = create_next_turn(db, session, last_score=score)
    return AnswerResponse(
        saved_turn_id=turn.id,
        feedback=feedback,
        answer_score=score,
        next_question=serialize_question(next_turn),
        session_complete=False,
    )

@router.get("/sessions/{session_id}", response_model=SessionSummaryResponse)
def get_session(session_id: int, db: Session = Depends(get_db)) -> SessionSummaryResponse:
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return serialize_session(session)


@router.post("/sessions/{session_id}/complete", response_model=SessionSummaryResponse)
def complete_session(session_id: int, db: Session = Depends(get_db)) -> SessionSummaryResponse:
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    session.summary = summarize_session(session.turns, session.extracted_profile)
    db.commit()
    db.refresh(session)
    return serialize_session(session)


def create_next_turn(db: Session, session: InterviewSession, last_score: float | None) -> InterviewTurn:
    previous_topics = [turn.topic for turn in session.turns]
    query = build_query(session.target_role, session.extracted_profile, previous_topics)
    chunks = vector_store.search(session.target_role, query, top_k=4)
    print("\n" + "=" * 100)
    print("RAG DEBUG INFORMATION")
    print("=" * 100)

    print(f"Target Role       : {session.target_role}")
    print(f"Previous Topics   : {previous_topics}")
    print(f"Generated Query   : {query}")
    print(f"Retrieved Chunks  : {len(chunks)}")
    print("=" * 100)

    if not chunks:
        print("no chunks from the Knowledge Base.")
    else:
        for index, chunk in enumerate(chunks, start=1):
            print(f"\nChunk #{index}")
            print(f"Source File : {chunk.source}")
            print(f"Chunk ID    : {chunk.chunk_id}")
            print(f"Role        : {chunk.role}")
            print(f"Score       : {chunk.score:.4f}")
            print("\nRetrieved Text:")
            print("-" * 80)
            print(chunk.text[:500])  # Prints first 500 characters
            print("-" * 80)

    print("=" * 100)
    
    generated = generate_question(
        session.target_role,
        session.extracted_profile,
        chunks,
        previous_topics,
        len(session.turns),
        last_score,
    )
    
    print("\nGENERATED QUESTION")
    print("=" * 100)
    print(generated["question"])
    print("=" * 100 + "\n")
    
    
    turn = InterviewTurn(
        session_id=session.id,
        question=generated["question"],
        topic=generated["topic"],
        difficulty=generated["difficulty"],
        rationale=generated["rationale"],
        retrieved_context=[chunk.as_dict() for chunk in chunks],
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    return turn


def serialize_question(turn: InterviewTurn) -> QuestionResponse:
    return QuestionResponse(
        turn_id=turn.id,
        question=turn.question,
        topic=turn.topic,
        difficulty=turn.difficulty,
        rationale=turn.rationale,
        retrieved_context=turn.retrieved_context,
    )


def serialize_session(session: InterviewSession) -> SessionSummaryResponse:
    return SessionSummaryResponse(
        session_id=session.id,
        target_role=session.target_role,
        status=session.status,
        extracted_profile=session.extracted_profile,
        turns=[
            {
                "turn_id": turn.id,
                "question": turn.question,
                "answer": turn.answer,
                "topic": turn.topic,
                "difficulty": turn.difficulty,
                "answer_score": turn.answer_score,
                "feedback": turn.feedback,
                "rationale": turn.rationale,
                "retrieved_context": turn.retrieved_context,
            }
            for turn in session.turns
        ],
        summary=session.summary,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )
