"""
app.py — Interface Streamlit de GamiTeach.

Flux :
  1. Setup  : choix de l'enseignant(e) + leçon via SPARQL live.
  2. Chat   : conversation libre, style ChatGPT/Claude.
              dummy_response() → à remplacer par graph.run_pipeline().
"""

import sys
import time
from pathlib import Path

import streamlit as st

# ── Chemin vers src/ pour imports SPARQL ──────────────────────────────────────
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

try:
    from tools.sparql_tools import run_sparql
    _SPARQL_OK = True
except Exception:
    _SPARQL_OK = False

# ── Config page ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GamiTeach",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS (décoratif uniquement — couleurs gérées par .streamlit/config.toml) ───
st.markdown("""
<style>
/* Titre page setup */
.gt-hero {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
}
.gt-hero h1 {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin: 0 0 0.4rem;
}
.gt-hero p {
    font-size: 0.9rem;
    color: #64748b;
    margin: 0;
}

/* Bandeau contexte chat */
.gt-bar {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.65rem 1.1rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.85rem;
    color: #334155;
    margin-bottom: 0.5rem;
}
.gt-bar .name  { font-weight: 600; color: #0f172a; }
.gt-bar .sep   { color: #cbd5e1; }
.gt-bar .topic { color: #2563eb; }

/* Chat messages */
[data-testid="stChatMessageContent"] {
    font-size: 0.92rem;
    line-height: 1.65;
}

/* Supprimer menu hamburger et footer */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Requêtes SPARQL ────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def get_teachers() -> dict[str, str]:
    """Retourne {nom: spécialité} pour tous les enseignants de l'ontologie."""
    if not _SPARQL_OK:
        return {"Sara": "ObjectOrientedProgramming"}
    try:
        rows = run_sparql("""
            SELECT DISTINCT ?teacher ?subject WHERE {
                ?teacher tgc:teaches ?lesson .
                OPTIONAL { ?teacher tgc:specializedIn ?subject }
            }
            ORDER BY ?teacher
        """)
        return {r["teacher"]: r.get("subject") or "" for r in rows}
    except Exception:
        return {"Sara": "ObjectOrientedProgramming"}


@st.cache_data(show_spinner=False)
def get_lessons(teacher: str) -> list[str]:
    """Retourne les leçons de l'enseignant sélectionné."""
    if not _SPARQL_OK:
        return ["Lesson1_JavaBasics", "Lesson2_ClassesAndObjects", "Lesson3_Constructors"]
    try:
        rows = run_sparql(f"""
            SELECT DISTINCT ?lesson WHERE {{
                tgc:{teacher} tgc:teaches ?lesson .
            }}
            ORDER BY ?lesson
        """)
        result = [r["lesson"] for r in rows]
        return result if result else ["(aucune leçon)"]
    except Exception:
        return ["(aucune leçon)"]


# ── Réponse dummy ──────────────────────────────────────────────────────────────

def dummy_response(teacher: str, lesson: str, question: str) -> str:
    """Bouchon — remplacer par graph.run_pipeline(user_input, teacher, lesson)."""
    time.sleep(0.8)
    return (
        f"**Réponse de démonstration** pour *{teacher}* · *{lesson}*\n\n"
        f"> {question}\n\n"
        "Cette réponse est un bouchon. Elle sera remplacée par la pipeline "
        "complète (Agent 1 → Agent 2 → Bridge → Agent 3) lors de l'intégration."
    )


# ── État session ───────────────────────────────────────────────────────────────

for key, default in {
    "setup_done": False,
    "teacher": "",
    "lesson": "",
    "messages": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ══════════════════════════════════════════════════════════════════════════════
#  ÉCRAN 1 — SETUP
# ══════════════════════════════════════════════════════════════════════════════

if not st.session_state.setup_done:

    st.markdown("""
    <div class="gt-hero">
        <h1>GamiTeach</h1>
        <p>Assistant de gamification pédagogique · Ontologie TGC</p>
    </div>
    """, unsafe_allow_html=True)

    teachers = get_teachers()
    teacher_names = list(teachers.keys())

    with st.container(border=True):
        teacher = st.selectbox(
            "Enseignant(e)",
            teacher_names,
            format_func=lambda t: f"{t}  ·  {teachers[t]}" if teachers.get(t) else t,
        )

        lessons = get_lessons(teacher)
        lesson = st.selectbox("Leçon", lessons)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Démarrer la conversation", use_container_width=True):
            st.session_state.teacher = teacher
            st.session_state.lesson = lesson
            st.session_state.messages = []
            st.session_state.setup_done = True
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  ÉCRAN 2 — CHAT
# ══════════════════════════════════════════════════════════════════════════════

else:
    teacher = st.session_state.teacher
    lesson  = st.session_state.lesson

    # Bandeau de contexte
    col_bar, col_btn = st.columns([6, 1])
    with col_bar:
        st.markdown(f"""
        <div class="gt-bar">
            📚
            <span class="name">{teacher}</span>
            <span class="sep">·</span>
            <span class="topic">{lesson}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_btn:
        if st.button("↩", help="Changer de prof / leçon"):
            st.session_state.setup_done = False
            st.session_state.messages = []
            st.rerun()

    # Message de bienvenue si conversation vide
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(
                f"Bonjour ! Je vais vous aider à gamifier la leçon **{lesson}**. "
                "Posez votre question ci-dessous."
            )

    # Historique
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Nouvelle question
    if prompt := st.chat_input("Votre question sur la gamification…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(""):
                response = dummy_response(teacher, lesson, prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
