import re
from collections import Counter
from pathlib import Path
from typing import Iterable


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "into", "is", "it", "of", "on", "or", "that", "the", "to", "with", "using",
}

SKILL_TERMS = {
    "python", "java", "javascript", "typescript", "react", "next.js", "node.js",
    "fastapi", "flask", "django", "sql", "postgresql", "mysql", "mongodb", "redis",
    "docker", "kubernetes", "aws", "azure", "gcp", "linux", "git", "rest", "graphql",
    "machine learning", "deep learning", "nlp", "computer vision", "pandas", "numpy",
    "scikit-learn", "pytorch", "tensorflow", "langchain", "rag", "llm", "vector database",
    "microservices", "celery", "spark", "airflow", "mlops", "ci/cd",
}

DOMAIN_TERMS = {
    "ecommerce", "healthcare", "finance", "education", "hr", "recruitment", "analytics",
    "recommendation", "chatbot", "automation", "security", "payments", "logistics",
}


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9.+#/-]*", text.lower())


def keywords(text: str, limit: int = 18) -> list[str]:
    counts = Counter(t for t in tokenize(text) if len(t) > 2 and t not in STOPWORDS)
    return [term for term, _ in counts.most_common(limit)]


def chunk_text(text: str, *, size: int = 850, overlap: int = 160) -> list[str]:
    text = normalize_whitespace(text)
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            sentence_end = max(text.rfind(".", start, end), text.rfind("?", start, end), text.rfind("!", start, end))
            if sentence_end > start + int(size * 0.55):
                end = sentence_end + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_profile(resume_text: str) -> dict:
    lowered = resume_text.lower()
    skills = sorted({skill for skill in SKILL_TERMS if skill in lowered})
    domains = sorted({domain for domain in DOMAIN_TERMS if domain in lowered})
    years = re.findall(r"(\d+)\+?\s*(?:years|yrs)", lowered)
    experience_years = max([int(y) for y in years], default=None)
    return {
        "skills": skills,
        "domains": domains,
        "keywords": keywords(resume_text),
        "experience_years": experience_years,
        "seniority": infer_seniority(experience_years, skills),
    }


def infer_seniority(experience_years: int | None, skills: Iterable[str]) -> str:
    skill_count = len(list(skills))
    if experience_years is not None and experience_years >= 4:
        return "advanced"
    if experience_years is not None and experience_years >= 2:
        return "intermediate"
    if skill_count >= 8:
        return "intermediate"
    return "foundational"
