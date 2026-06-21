"""
app.py — Interface Streamlit de GamiTeach.

Flux :
  1. Setup : enseignant → cours → leçon (mêmes requêtes SPARQL que le CLI).
  2. Chat  : question → pipeline (graph.run_pipeline) → réponse.

Le code métier vient de src/pipeline.py (partagé avec le CLI src/main.py) :
mêmes sélections, même orchestration, mêmes résultats. Les logs détaillés des
agents s'affichent en temps réel dans la console (prints des nœuds).
"""

import itertools
import re
import sys
from pathlib import Path

import streamlit as st

# ── Racine projet sur le sys.path (import identique au CLI) ───────────────────
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from src.pipeline import list_teachers, courses_of, lessons_of, run
    from src.agent.agent3 import save_resource_to_file, build_traceability
    _PIPELINE_OK = True
    _IMPORT_ERR = None
except Exception as e:  # dépendances/LLM absents : l'app reste affichable
    _PIPELINE_OK = False
    _IMPORT_ERR = e


# ── Rendu Markdown avec graphes Mermaid ───────────────────────────────────────
# st.markdown() affiche les blocs ```mermaid``` comme du texte brut.
# render_trace_md() découpe le texte sur ces blocs et rend chacun via
# st.html(unsafe_allow_javascript=True) avec mermaid.js ESM depuis CDN.
#
# Pourquoi ESM + type="module" + await mermaid.run() :
#   - st.html() rend INLINE (pas d'iframe) → le JS partage le DOM de la page.
#   - startOnLoad ne fonctionne pas (DOMContentLoaded déjà passé au moment du rendu).
#   - Un module ES isolé par bloc garantit que chaque graphe est rendu de façon
#     autonome, sans interférence entre blocs.

_MERMAID_ESM = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs"
_MERMAID_PATTERN = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)

# Compteur global (pas local à un seul appel de render_trace_md) : un même message
# affiche plusieurs graphes Mermaid via PLUSIEURS appels à render_trace_md (aperçu
# visuel, puis traçabilité). Un id basé sur l'index local au texte découpé peut donc
# se répéter entre deux appels ; document.getElementById() renvoie alors le premier
# élément du DOM portant cet id (déjà converti en SVG), jamais le bon nœud.
_mermaid_id_counter = itertools.count()


def _mermaid_html(code: str, block_id: str) -> str:
    return (
        f'<div id="{block_id}"><pre class="mermaid" style="background:transparent">'
        f"{code}</pre></div>"
        f'<script type="module">'
        f'import mermaid from "{_MERMAID_ESM}";'
        f'await mermaid.run({{nodes:[document.getElementById("{block_id}").querySelector(".mermaid")]}});'
        f"</script>"
    )


def render_trace_md(text: str) -> None:
    """Affiche un bloc Markdown contenant éventuellement des graphes Mermaid.

    Découpe sur les blocs ```mermaid```, utilise st.html() pour chacun
    (avec unsafe_allow_javascript=True) et st.markdown() pour le reste."""
    parts = _MERMAID_PATTERN.split(text)
    for i, part in enumerate(parts):
        if i % 2 == 1:                        # indices impairs = code mermaid capturé
            block_id = f"mermaid-{next(_mermaid_id_counter)}"
            st.html(_mermaid_html(part, block_id), unsafe_allow_javascript=True)
        elif part.strip():
            st.markdown(part)


# ── Config page ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GamiTeach",
    page_icon="📚",
    layout="centered",   # empilé (diagramme puis texte) : centré reste lisible
    initial_sidebar_state="collapsed",
)

# ── CSS (décoratif — couleurs gérées par .streamlit/config.toml) ──────────────
st.markdown("""
<style>
.gt-hero { text-align: center; padding: 2.5rem 0 1.5rem; }
.gt-hero h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; margin: 0 0 0.4rem; }
.gt-hero p  { font-size: 0.9rem; color: #64748b; margin: 0; }

.gt-bar {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 0.65rem 1.1rem; display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.85rem; color: #334155; margin-bottom: 0.5rem;
}
.gt-bar .name  { font-weight: 600; color: #0f172a; }
.gt-bar .sep   { color: #cbd5e1; }
.gt-bar .topic { color: #2563eb; }

[data-testid="stChatMessageContent"] { font-size: 0.92rem; line-height: 1.65; }
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Garde-fou : pipeline importée ? (jamais de repli silencieux) ──────────────
if not _PIPELINE_OK:
    st.error(f"Pipeline indisponible (échec d'import) : {_IMPORT_ERR}")
    st.stop()


# ── Sélection (cache pour ne pas relancer SPARQL à chaque rerun) ──────────────

@st.cache_data(show_spinner=False)
def cached_teachers() -> list[str]:
    return list_teachers()


@st.cache_data(show_spinner=False)
def cached_courses(teacher: str) -> list[str]:
    return courses_of(teacher)


@st.cache_data(show_spinner=False)
def cached_lessons(teacher: str, course: str) -> list[str]:
    return lessons_of(teacher, course)


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


# ══════════════════════════════════════════════════════════════════════════════
#  ÉCRAN 1 — SETUP : enseignant → cours → leçon
# ══════════════════════════════════════════════════════════════════════════════

if not st.session_state.setup_done:

    st.markdown("""
    <div class="gt-hero">
        <h1>GamiTeach</h1>
        <p>Assistant de gamification pédagogique · Ontologie TGC</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        teacher = st.selectbox("Enseignant(e)", cached_teachers())

        courses = cached_courses(teacher)
        if not courses:
            st.info(f"**{teacher}** n'a conçu aucune leçon dans l'ontologie — "
                    "rien à gamifier. Choisissez un autre enseignant.")
            st.stop()

        course = st.selectbox("Cours", courses)
        lesson = st.selectbox("Leçon", cached_lessons(teacher, course))

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Démarrer la conversation", use_container_width=True):
            st.session_state.teacher = teacher
            st.session_state.course = course
            st.session_state.lesson = lesson
            st.session_state.messages = []
            st.session_state.setup_done = True
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  ÉCRAN 2 — CHAT
# ══════════════════════════════════════════════════════════════════════════════

else:
    teacher = st.session_state.teacher
    course  = st.session_state.course
    lesson  = st.session_state.lesson

    # Bandeau de contexte + retour
    col_bar, col_btn = st.columns([6, 1])
    with col_bar:
        st.markdown(f"""
        <div class="gt-bar">
            📚 <span class="name">{teacher}</span>
            <span class="sep">·</span> <span>{course}</span>
            <span class="sep">·</span> <span class="topic">{lesson}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_btn:
        if st.button("↩", help="Changer de prof / cours / leçon"):
            st.session_state.setup_done = False
            st.session_state.messages = []
            st.rerun()

    # Message de bienvenue si conversation vide
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(
                f"Bonjour ! Je vais vous aider à gamifier la leçon **{lesson}** "
                f"(cours *{course}*). Posez votre question ci-dessous."
            )

    # Historique (avec bouton de téléchargement persistant pour les ressources)
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            if msg.get("diagram"):
                # Empilé : aperçu visuel en haut, version texte juste en dessous
                # (ni colonnes déséquilibrées, ni onglet dépliable).
                st.caption("🗺️ Aperçu visuel de l'activité")
                render_trace_md("```mermaid\n" + msg["diagram"] + "\n```")
                st.divider()
                st.caption("📄 Version texte (identique à l'export)")
            st.markdown(msg["content"])
            if msg.get("trace_md"):
                with st.expander("🔎 Détails du raisonnement"):
                    # Strictement la même traçabilité que dans le rapport .md backend.
                    render_trace_md(msg["trace_md"])
            if msg.get("resource_md"):
                st.download_button(
                    "⬇ Télécharger la ressource (.md)",
                    data=msg["resource_md"],
                    file_name=msg.get("filename", "ressource.md"),
                    mime="text/markdown",
                    key=f"dl_{i}",
                )
            if msg.get("saved_path"):
                st.caption(f"✓ Ressource sauvegardée : {msg['saved_path']}")

    # Nouvelle question
    if prompt := st.chat_input("Votre question sur la gamification…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Raisonnement en cours… (détails dans la console)"):
                try:
                    state = run(prompt, teacher, course, lesson)
                except Exception as e:
                    state = {"final_answer": f"⚠ Erreur pendant la pipeline : `{e}`"}

            # Construction du message à mémoriser (le rendu se fait au rerun via l'historique).
            msg = {
                "role": "assistant",
                "content": (state.get("final_answer")
                            or state.get("generated_resource")
                            or "(réponse vide)"),
            }
            # Branche ressource : version visuelle (Mermaid), traçabilité, export.
            if state.get("intent") != "people" and state.get("generated_resource"):
                msg["diagram"] = state.get("resource_diagram")
                msg["trace_md"] = build_traceability(state)
                try:
                    path = save_resource_to_file(state)
                    msg["resource_md"] = state["generated_resource"]
                    msg["filename"] = Path(path).name
                    msg["saved_path"] = path
                except Exception as e:
                    st.caption(f"⚠ Sauvegarde impossible : {e}")

        st.session_state.messages.append(msg)
        st.rerun()