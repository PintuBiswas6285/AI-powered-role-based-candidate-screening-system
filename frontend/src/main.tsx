import React from "react";
import { createRoot } from "react-dom/client";
import { BrainCircuit, CheckCircle2, FileText, Loader2, Send, Sparkles, UploadCloud } from "lucide-react";

import {
  AnswerResponse,
  Question,
  SessionSummary,
  completeSession,
  fetchRoles,
  getSession,
  startSession,
  submitAnswer
} from "./api/client";
import "./styles/app.css";

type Stage = "entry" | "interview" | "summary";

const DEFAULT_ROLES = ["Backend Engineer",
  "AI ML Engineer",
];


function App() {
  const [roles, setRoles] = React.useState<string[]>([]);
  
  const [selectedRole, setSelectedRole] = React.useState("");
  const [candidateName, setCandidateName] = React.useState("");
  const [resume, setResume] = React.useState<File | null>(null);
  const [stage, setStage] = React.useState<Stage>("entry");
  const [sessionId, setSessionId] = React.useState<number | null>(null);
  const [profile, setProfile] = React.useState<Record<string, unknown>>({});
  const [question, setQuestion] = React.useState<Question | null>(null);
  const [answer, setAnswer] = React.useState("");
  const [history, setHistory] = React.useState<AnswerResponse[]>([]);
  const [summary, setSummary] = React.useState<SessionSummary | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

React.useEffect(() => {
  fetchRoles()
  .then((items) => {
      // ▼▼ This is the replacement for your original code ▼▼
      const availableRoles =
        Array.isArray(items) && items.length > 0
          ? items
          : DEFAULT_ROLES;

      setRoles(availableRoles);
      setSelectedRole(availableRoles[0]);
      // ▲▲ End of replacement ▲▲
  })
    .catch((err) => {
      console.warn("Unable to fetch roles. Using default roles.", err);

      setRoles(DEFAULT_ROLES);
      setSelectedRole(DEFAULT_ROLES[0]);
    });
}, []);

  async function handleStart(event: React.FormEvent) {
    event.preventDefault();
    if (!resume || !selectedRole) {
      setError("Choose a role and upload a resume.");
      return;
    }
    setLoading(true);
    setError("");
    const form = new FormData();
    form.append("target_role", selectedRole);
    form.append("candidate_name", candidateName);
    form.append("resume", resume);
    try {
      const data = await startSession(form);
      setSessionId(data.session_id);
      setProfile(data.extracted_profile);
      setQuestion(data.first_question);
      setStage("interview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start session.");
    } finally {
      setLoading(false);
    }
  }

  async function handleAnswer(event: React.FormEvent) {
    event.preventDefault();
    if (!sessionId || !question || answer.trim().length < 2) return;
    setLoading(true);
    setError("");
    try {
      const data = await submitAnswer(sessionId, question.turn_id, answer);
      setHistory((items) => [...items, data]);
      setAnswer("");
      if (data.session_complete || !data.next_question) {
        const finalSummary = await getSession(sessionId);
        setSummary(finalSummary);
        setStage("summary");
      } else {
        setQuestion(data.next_question);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save answer.");
    } finally {
      setLoading(false);
    }
  }

  async function handleComplete() {
    if (!sessionId) return;
    setLoading(true);
    try {
      setSummary(await completeSession(sessionId));
      setStage("summary");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to complete session.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <BrainCircuit size={28} />
          <div>
            <strong>Role-Based Candidate Screening</strong>
            <span>RAG interview simulator</span>
          </div>
        </div>
        <div className="status-pill">{stage}</div>
      </header>

      {error && <div className="alert">{error}</div>}

      {stage === "entry" && (
        <section className="workspace entry-grid">
          <form className="panel intake" onSubmit={handleStart}>
            <div className="panel-heading">
              <UploadCloud size={22} />
              <h1>Candidate Entry</h1>
            </div>
            <label>
              Candidate name
              <input value={candidateName} onChange={(event) => setCandidateName(event.target.value)} placeholder="Optional" />
            </label>
            <label>
              Target role
              <select value={selectedRole} onChange={(event) => setSelectedRole(event.target.value)}>
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </label>
            <label className="file-drop">
              <FileText size={30} />
              <span>{resume ? resume.name : "Upload PDF or text resume"}</span>
              <input
                type="file"
                accept=".pdf,.txt,text/plain,application/pdf"
                onChange={(event) => setResume(event.target.files?.[0] ?? null)}
              />
            </label>
            <button className="primary" disabled={loading}>
              {loading ? <Loader2 className="spin" size={18} /> : <Sparkles size={18} />}
              Start Interview
            </button>
          </form>

          <aside className="panel flow">
            <h2>System Flow</h2>
            {["Resume parsing", "Profile extraction", "Role-aware retrieval", "Grounded question generation", "Answer storage", "Final insight report"].map(
              (item) => (
                <div className="flow-row" key={item}>
                  <CheckCircle2 size={18} />
                  <span>{item}</span>
                </div>
              )
            )}
          </aside>
        </section>
      )}

      {stage === "interview" && question && (
        <section className="workspace interview-grid">
          <div className="panel question-panel">
            <div className="question-meta">
              <span>{question.topic}</span>
              <span>{question.difficulty}</span>
            </div>
            <h1>{question.question}</h1>
            <form onSubmit={handleAnswer}>
              <textarea value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Type the candidate answer..." />
              <div className="actions">
                <button type="button" className="secondary" onClick={handleComplete} disabled={loading}>
                  Finish
                </button>
                <button className="primary" disabled={loading || answer.trim().length < 2}>
                  {loading ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
                  Submit Answer
                </button>
              </div>
            </form>
          </div>

          <aside className="panel evidence">
            <h2>Resume Signals</h2>
            <TagList items={profile.skills as string[]} empty="No skills detected yet" />
            <h2>Retrieved Context</h2>
            {question.retrieved_context.map((item) => (
              <article key={item.chunk_id} className="context-card">
                <strong>{item.source}</strong>
                <span>score {item.score}</span>
                <p>{item.text}</p>
              </article>
            ))}
          </aside>
        </section>
      )}

      {stage === "summary" && summary && (
        <section className="workspace summary">
          <div className="panel">
            <div className="panel-heading">
              <CheckCircle2 size={22} />
              <h1>Interview Summary</h1>
            </div>
            <div className="metrics">
              <Metric label="Average score" value={String(summary.summary?.average_score ?? "N/A")} />
              <Metric label="Questions answered" value={String(summary.summary?.questions_answered ?? 0)} />
              <Metric label="Decision" value={String(summary.summary?.recommendation ?? "Pending")} />
            </div>
            <h2>Conversation Record</h2>
            {summary.turns.map((turn) => (
              <article className="turn" key={String(turn.turn_id)}>
                <strong>{String(turn.topic)} · {String(turn.difficulty)}</strong>
                <p>{String(turn.question)}</p>
                <blockquote>{String(turn.answer ?? "Not answered")}</blockquote>
                <span>{String(turn.feedback ?? "No feedback")}</span>
              </article>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

function TagList({ items, empty }: { items?: string[]; empty: string }) {
  if (!items || items.length === 0) return <p className="muted">{empty}</p>;
  return (
    <div className="tags">
      {items.map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
