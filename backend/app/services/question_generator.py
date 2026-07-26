from app.services.text_processing import keywords
from app.services.vector_store import RetrievedChunk


ROLE_FOCUS = {
    "AI ML Engineer": ["model evaluation", "feature engineering", "generalization", "deployment"],
    "Backend Engineer": ["API design", "data modeling", "scalability", "reliability"],
    "Data Science Applied ML": ["experimentation", "data leakage", "model interpretation", "metrics"],
}


def build_query(role: str, profile: dict, previous_topics: list[str]) -> str:
    skills = ", ".join(profile.get("skills", [])[:8]) or "core fundamentals"
    domains = ", ".join(profile.get("domains", [])[:4]) or "applied projects"
    seen = ", ".join(previous_topics[-3:])
    return (
        f"Role: {role}. Candidate skills: {skills}. Domains: {domains}. "
        f"Seniority: {profile.get('seniority', 'foundational')}. Avoid repeated topics: {seen}."
    )


def select_topic(role: str, profile: dict, chunks: list[RetrievedChunk], previous_topics: list[str]) -> str:
    role_topics = ROLE_FOCUS.get(role, [])
    candidate_terms = profile.get("skills", []) + profile.get("keywords", [])
    retrieved_terms = keywords(" ".join(chunk.text for chunk in chunks), limit=12)
    for topic in role_topics + candidate_terms + retrieved_terms:
        normalized = topic.title()
        if normalized not in previous_topics and len(normalized) > 2:
            return normalized
    return role_topics[0].title() if role_topics else "Core Concepts"


def difficulty_for(profile: dict, turn_count: int, answer_score: float | None = None) -> str:
    base = profile.get("seniority", "foundational")
    if answer_score is not None and answer_score >= 0.76:
        return "advanced" if base != "foundational" or turn_count >= 2 else "intermediate"
    if base == "advanced" or turn_count >= 3:
        return "advanced"
    if base == "intermediate" or turn_count >= 1:
        return "intermediate"
    return "foundational"


def generate_question(role: str, profile: dict, chunks: list[RetrievedChunk], previous_topics: list[str], turn_count: int, last_score: float | None = None) -> dict:
    topic = select_topic(role, profile, chunks, previous_topics)
    difficulty = difficulty_for(profile, turn_count, last_score)
    context_hint = chunks[0].text[:260] if chunks else "the retrieved knowledge base context"
    skills = profile.get("skills", [])
    skill_phrase = f" using your experience with {', '.join(skills[:3])}" if skills else ""

    if difficulty == "advanced":
        question = (
            f"For a {role} interview, explain a production-grade approach to {topic}{skill_phrase}. "
            f"Use the idea from the retrieved context below, discuss trade-offs, and describe how you would validate the solution: "
            f"{context_hint}"
        )
    elif difficulty == "intermediate":
        question = (
            f"How would you apply {topic}{skill_phrase} in a real project? "
            f"Ground your answer in this knowledge-base context and mention one failure mode: {context_hint}"
        )
    else:
        question = (
            f"What is the core idea behind {topic}, and why does it matter for a {role}? "
            f"Relate your answer to this context: {context_hint}"
        )

    return {
        "question": question,
        "topic": topic,
        "difficulty": difficulty,
        "rationale": (
            f"Generated from role={role}, resume signals={skills[:5]}, "
            f"and top retrieved source={chunks[0].source if chunks else 'none'}."
        ),
    }


def evaluate_answer(answer: str, context: list[dict]) -> tuple[float, str]:
    answer_terms = set(keywords(answer, limit=40))
    context_terms = set(keywords(" ".join(item.get("text", "") for item in context), limit=40))
    overlap = len(answer_terms & context_terms)
    length_score = min(len(answer.split()) / 90, 1.0)
    grounding_score = min(overlap / 8, 1.0)
    score = round((0.45 * length_score) + (0.55 * grounding_score), 2)

    if score >= 0.75:
        feedback = "Strong answer: it is detailed and well grounded in the retrieved knowledge context."
    elif score >= 0.45:
        feedback = "Reasonable answer: it covers part of the topic, but could use sharper technical grounding."
    else:
        feedback = "Needs depth: add concrete concepts, trade-offs, examples, and terminology from the topic."
    return score, feedback


def summarize_session(turns: list, profile: dict) -> dict:
    answered = [turn for turn in turns if turn.answer]
    avg_score = round(sum((turn.answer_score or 0) for turn in answered) / max(len(answered), 1), 2)
    strengths = sorted({turn.topic for turn in answered if (turn.answer_score or 0) >= 0.65})
    gaps = sorted({turn.topic for turn in answered if (turn.answer_score or 0) < 0.65})
    return {
        "average_score": avg_score,
        "questions_answered": len(answered),
        "resume_signals_used": {
            "skills": profile.get("skills", []),
            "domains": profile.get("domains", []),
            "seniority": profile.get("seniority"),
        },
        "strengths": strengths,
        "improvement_areas": gaps,
        "recommendation": recommendation(avg_score),
    }


def recommendation(avg_score: float) -> str:
    if avg_score >= 0.75:
        return "Proceed to a deeper technical round."
    if avg_score >= 0.5:
        return "Proceed with caution and probe weak topics in a follow-up round."
    return "Needs more preparation before moving forward."
