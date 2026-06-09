"""
app.py — Interface Streamlit de GamiTeach.

Flux :
  1. Setup  : choix de l'enseignant(e) + leçon via SPARQL live.
  2. Chat   : conversation libre, style ChatGPT/Claude.
              dummy_response() → à remplacer par graph.run_pipeline().
"""

import sys
from pathlib import Path

import streamlit as st

# ── Racine projet sur le sys.path ─────────────────────────────────────────────
# On importe EXACTEMENT comme le CLI (src.agent.*, src.tools.*) pour réutiliser
# le même code et le même singleton ontologie que test_pipeline -> mêmes résultats.
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from src.agent.test_pipeline import (
        list_teachers, teacher_course, lessons_of, run_pipeline_steps,
    )
    from src.agent.agent3 import save_resource_to_file
    _PIPELINE_OK = True
    _IMPORT_ERR = None
except Exception as e:  # dépendances/LLM absents : l'app reste affichable
    _PIPELINE_OK = False
    _IMPORT_ERR = e

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
    """{nom: spécialité} pour les 15 enseignants — MÊME requête que le CLI (list_teachers)."""
    return {t: teacher_course(t) for t in list_teachers()}


@st.cache_data(show_spinner=False)
def get_lessons(teacher: str) -> list[str]:
    """Leçons de l'enseignant — MÊME requête que le CLI (lessons_of)."""
    return lessons_of(teacher)


# ── Pipeline (même chaîne que test_pipeline) ─────────────────────────────────────

def run_assistant(teacher: str, course: str, lesson: str, question: str):
    """Appelle la pipeline partagée et renvoie (réponse_markdown, trace, result).

    `run_pipeline_steps` est la source unique partagée avec le CLI : la chaîne de
    raisonnement et les résultats sont donc strictement identiques. `log` capture
    les étapes pour les afficher (équivalent des prints du CLI).
    """
    trace: list[str] = []
    result = run_pipeline_steps(teacher, course, lesson, question, log=trace.append)
    return result.get("final_answer") or "(réponse vide)", trace, result


# ── État session ───────────────────────────────────────────────────────────────

for key, default in {
    "setup_done": False,
    "teacher": "",
    "course": "",
    "lesson": "",
    "messages": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Garde-fou : pipeline importée ? (erreur visible, jamais de repli silencieux) ──
if not _PIPELINE_OK:
    st.error(f"Pipeline indisponible (échec d'import) : {_IMPORT_ERR}")
    st.stop()


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
            # Cours de spécialisation (= teacher_course du CLI), récupéré au setup.
            st.session_state.course = teachers.get(teacher) or "ObjectOrientedProgramming"
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
            if not _PIPELINE_OK:
                response = f"⚠ Pipeline indisponible à l'import : `{_IMPORT_ERR}`"
                st.markdown(response)
            else:
                trace, result = [], None
                with st.spinner("Raisonnement en cours…"):
                    try:
                        response, trace, result = run_assistant(
                            teacher, st.session_state.course, lesson, prompt
                        )
                    except Exception as e:
                        response = f"⚠ Erreur pendant la pipeline : `{e}`"
                st.markdown(response)

                # Chaîne de raisonnement (mêmes étapes que les prints du CLI).
                if trace:
                    with st.expander("🧠 Chaîne de raisonnement"):
                        st.code("\n".join(trace).strip(), language="text")

                # Branche ressource : on sauvegarde le .md comme le CLI.
                if result and result.get("branch") == "resource":
                    try:
                        path = save_resource_to_file(result["state"])
                        st.caption(f"✓ Ressource sauvegardée : {path}")
                    except Exception:
                        pass

        st.session_state.messages.append({"role": "assistant", "content": response})
