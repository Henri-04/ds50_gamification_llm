import streamlit as st
import time

# ─────────────────────────────────────────────
#  CONFIG PAGE
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="GamiTeach – Assistant Pédagogique",
    page_icon="🎮",
    layout="wide",
)

# ─────────────────────────────────────────────
#  CSS PERSONNALISÉ
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        color: #e8e8f0;
    }

    .main-header { text-align: center; padding: 1.5rem 0 0.5rem 0; }
    .main-header h1 {
        font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2.6rem;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; letter-spacing: -1px; margin: 0;
    }
    .main-header p { color: #94a3b8; font-size: 0.95rem; font-weight: 300; margin-top: 0.3rem; }

    /* Carte profil */
    .profile-card {
        background: rgba(167,139,250,0.08);
        border: 1px solid rgba(167,139,250,0.25);
        border-radius: 14px;
        padding: 1rem 1.3rem;
        margin-bottom: 1rem;
    }
    .profile-card h4 {
        font-family: 'Syne', sans-serif;
        color: #a78bfa; font-size: 0.8rem;
        letter-spacing: 0.1em; text-transform: uppercase; margin: 0 0 0.7rem 0;
    }
    .profile-tag {
        display: inline-block; padding: 0.2rem 0.6rem;
        border-radius: 6px; font-size: 0.72rem; font-weight: 500;
        margin: 0.15rem; background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.12); color: #cbd5e1;
    }
    .profile-tag.highlight {
        background: rgba(96,165,250,0.15);
        border-color: rgba(96,165,250,0.35); color: #93c5fd;
    }

    /* Onboarding */
    .onboarding-box {
        background: linear-gradient(135deg, rgba(167,139,250,0.1), rgba(96,165,250,0.08));
        border: 1px solid rgba(167,139,250,0.3);
        border-radius: 16px; padding: 2rem; text-align: center; margin: 1rem 0;
    }
    .onboarding-box h3 { font-family: 'Syne', sans-serif; color: #a78bfa; margin-bottom: 0.5rem; }
    .onboarding-box p { color: #94a3b8; font-size: 0.9rem; }

    /* Mode badges */
    .mode-badge {
        display: inline-block; padding: 0.3rem 0.9rem; border-radius: 999px;
        font-size: 0.75rem; font-weight: 500; letter-spacing: 0.05em; margin-bottom: 1rem;
    }
    .mode-objectif { background: rgba(167,139,250,0.15); color: #a78bfa; border: 1px solid rgba(167,139,250,0.3); }
    .mode-cours    { background: rgba(52,211,153,0.15);  color: #34d399;  border: 1px solid rgba(52,211,153,0.3); }

    /* Bulles de chat */
    .chat-bubble { padding: 0.85rem 1.1rem; border-radius: 16px; margin-bottom: 0.7rem; max-width: 85%; line-height: 1.6; font-size: 0.92rem; }
    .bubble-user  { background: linear-gradient(135deg, rgba(167,139,250,0.2), rgba(96,165,250,0.2)); border: 1px solid rgba(167,139,250,0.3); margin-left: auto; text-align: right; }
    .bubble-assistant { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); margin-right: auto; }
    .bubble-label { font-size: 0.7rem; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.3rem; opacity: 0.6; }

    /* Context hint */
    .context-hint {
        background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.2);
        border-radius: 10px; padding: 0.6rem 0.9rem; font-size: 0.8rem; color: #6ee7b7;
        margin-bottom: 0.8rem;
    }

    hr { border-color: rgba(255,255,255,0.07); }

    .stButton > button {
        border-radius: 10px; font-family: 'DM Sans', sans-serif; font-weight: 500; transition: all 0.2s ease;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(167,139,250,0.3); }

    .stTextInput > div > div > input, .stTextArea textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: #e8e8f0 !important; border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    [data-testid="stSidebar"] {
        background: rgba(10,10,20,0.8) !important;
        border-right: 1px solid rgba(255,255,255,0.07) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.03); border-radius: 12px; padding: 4px; gap: 4px;
    }
    .stTabs [data-baseweb="tab"] { border-radius: 9px; font-family: 'DM Sans', sans-serif; font-weight: 500; color: #94a3b8; }
    .stTabs [aria-selected="true"] { background: rgba(167,139,250,0.2) !important; color: #a78bfa !important; }
    .stAlert { background: rgba(255,255,255,0.04) !important; border-radius: 10px !important; }
    
    /* Step indicator */
    .step-indicator {
        display: flex; align-items: center; gap: 0.5rem;
        font-size: 0.8rem; color: #94a3b8; margin-bottom: 1rem;
    }
    .step-dot {
        width: 24px; height: 24px; border-radius: 50%; display: flex;
        align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700;
    }
    .step-done { background: rgba(52,211,153,0.2); color: #34d399; border: 1px solid rgba(52,211,153,0.4); }
    .step-active { background: rgba(167,139,250,0.2); color: #a78bfa; border: 1px solid rgba(167,139,250,0.4); }
    .step-todo { background: rgba(255,255,255,0.05); color: #475569; border: 1px solid rgba(255,255,255,0.08); }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  DONNÉES DE L'ONTOLOGIE TGC (valeurs extraites du OWL)
# ─────────────────────────────────────────────

TGC_TEACHING_STYLES = [
    "Structured", "Collaborative", "Project-based", "Exploratory",
    "Visual", "Hands-on", "Coaching", "Discussion-based",
    "Analytical", "Mentoring", "Case-based"
]

TGC_PLAYER_TYPES = {
    "Achiever":      "🏆 Motivé par les accomplissements, badges et classements",
    "Socializer":    "🤝 Aime les interactions sociales et la collaboration",
    "Free_Spirit":   "🕊️ Préfère l'exploration libre et la créativité",
    "Philanthropist":"💛 Satisfait par l'aide aux autres et le partage",
}

TGC_ACADEMIC_TITLES = ["Instructor", "Associate Professor", "Professor"]

TGC_SUBJECT_AREAS = [
    "Computer Sciences", "Software Engineering", "Mathematics",
    "Languages", "Arts Education", "Social Sciences", "Engineering",
    "GamificationDesign", "InteractiveLearningDesign"
]

TGC_GAMIF_EXPERIENCE = ["Novice", "Beginner", "Intermediate", "Advanced"]

TGC_PED_EXPERIENCE = [
    "≤ 5 ans", "6–11 ans", "12–17 ans", "18–23 ans", "24+ ans"
]

TGC_DIGITAL_CONTENT = {
    "Creator": "Crée le contenu éducatif (cours, ressources, activités)",
    "Curator":  "Sélectionne, organise et adapte du contenu existant"
}

TGC_SOCIAL_COMMITMENT = {
    "socially_competent": "Utilise activement les outils numériques pour communiquer avec les étudiants",
    "socially_limited":   "Préfère un contact limité via les outils numériques"
}

TGC_LANGUAGES = ["Français", "Anglais", "Arabe"]

# ─────────────────────────────────────────────
#  FONCTIONS BOUCHONS
# ─────────────────────────────────────────────

def build_teacher_context_prompt(profile: dict) -> str:
    """
    Construit le contexte enseignant à partir du profil TGC
    pour personnaliser les recommandations.
    """
    player_desc = TGC_PLAYER_TYPES.get(profile.get("player_type", ""), "")
    return f"""
PROFIL ENSEIGNANT (Ontologie TGC) :
- Nom : {profile.get('name', 'Non précisé')}
- Style d'enseignement : {profile.get('teaching_style', 'Non précisé')}
- Type de joueur : {profile.get('player_type', 'Non précisé')} → {player_desc}
- Discipline : {profile.get('subject_area', 'Non précisée')}
- Titre académique : {profile.get('academic_title', 'Non précisé')}
- Expérience pédagogique : {profile.get('ped_experience', 'Non précisée')}
- Expérience en gamification : {profile.get('gamif_experience', 'Non précisée')}
- Compétence numérique (contenu) : {profile.get('digital_content', 'Non précisée')}
- Engagement social numérique : {profile.get('social_commitment', 'Non précisé')}
- Niveau des apprenants : {profile.get('learner_level', 'Non précisé')}
- Cours de référence : {profile.get('course_name', 'Non précisé')}
"""

def dummy_objectif_pedagogique(objectif: str, profile: dict) -> str:
    """
    BOUCHON – À remplacer par appel LLM (Étudiant 4).
    Personnalise la réponse selon le profil TGC de l'enseignant.
    """
    pt = profile.get("player_type", "")
    ts = profile.get("teaching_style", "")
    ge = profile.get("gamif_experience", "Novice")
    name = profile.get("name", "Enseignant(e)")

    # Personnalisation selon le type de joueur (ontologie TGC)
    player_reco = {
        "Achiever":      "🏆 **Badges de progression** : récompensez chaque étape franchie. Les classements intermédiaires motiveront particulièrement vos apprenants.",
        "Socializer":    "🤝 **Quêtes collaboratives** : divisez la classe en guildes. Les défis d'équipe correspondent parfaitement à votre profil de socialiseur.",
        "Free_Spirit":   "🕊️ **Exploration libre** : proposez des chemins d'apprentissage alternatifs. Vos apprenants choisissent leur parcours gamifié.",
        "Philanthropist":"💛 **Système de mentorat** : les apprenants avancés aident les débutants. Les points de partage et de contribution sont valorisés.",
    }

    # Conseil adapté au niveau de gamification
    if ge == "Novice":
        complexity_note = "\n\n💡 *Conseil pour débutant en gamification :* commencez par **un seul mécanisme** (ex. les points) avant d'en ajouter d'autres."
    elif ge == "Beginner":
        complexity_note = "\n\n💡 *Conseil :* combinez 2-3 mécanismes simples (points + badges + défi) pour créer une première boucle d'engagement."
    elif ge == "Intermediate":
        complexity_note = "\n\n💡 *Conseil :* pensez aux **boucles progressives** (Progressive Loops) : chaque niveau débloque de nouveaux défis."
    else:
        complexity_note = "\n\n💡 *Conseil avancé :* intégrez le modèle **BrainHex** pour individualiser les parcours selon le profil de joueur de chaque apprenant."

    base = player_reco.get(pt, "🎯 **Système de points XP** : récompensez chaque activité complétée. Simple et efficace pour démarrer.")
    
    context = build_teacher_context_prompt(profile)

    return (
        f"**Recommandation GamiTeach pour {name}** *(profil : {ts} / {pt})*\n\n"
        f"{base}"
        f"{complexity_note}\n\n"
        f"---\n"
        f"*[Réponse simulée – contexte TGC injecté dans le prompt :]*\n"
        f"```\n{context.strip()}\n```"
    )


def dummy_question_cours(question: str, profile: dict) -> str:
    """
    BOUCHON – À remplacer par RAG (Étudiant 3) + LLM (Étudiant 4).
    Personnalise la réponse selon le profil TGC.
    """
    cours = profile.get("course_name", "Cours non précisé")
    name  = profile.get("name", "Enseignant(e)")
    pt    = profile.get("player_type", "")
    dc    = profile.get("digital_content", "Creator")
    ll    = profile.get("learner_level", "Licence")

    digital_tip = (
        "🛠️ En tant que **Curator**, adaptez des ressources gamifiées existantes plutôt que de tout créer from scratch."
        if dc == "Curator" else
        "✏️ En tant que **Creator**, vous pouvez concevoir vos propres activités gamifiées sur mesure."
    )

    context = build_teacher_context_prompt(profile)

    return (
        f"**Réponse RAG pour {name}** *(cours : {cours}, niveau : {ll})*\n\n"
        f"📚 *Extrait simulé du cours* : « Les concepts clés liés à votre question sont directement "
        f"exploitables via des mécanismes de gamification ciblés. »\n\n"
        f"**Suggestion gamifiée adaptée à votre profil {pt} :**\n"
        f"Proposez un **défi contextuel** en lien avec ce concept : les apprenants débloquent "
        f"la notion suivante en répondant correctement à une question-clé.\n\n"
        f"{digital_tip}\n\n"
        f"---\n"
        f"*[Réponse simulée – contexte TGC injecté dans le prompt :]*\n"
        f"```\n{context.strip()}\n```"
    )


# ─────────────────────────────────────────────
#  ÉTAT SESSION
# ─────────────────────────────────────────────
if "profile_complete" not in st.session_state:
    st.session_state.profile_complete = False
if "teacher_profile" not in st.session_state:
    st.session_state.teacher_profile = {}
if "historique_objectif" not in st.session_state:
    st.session_state.historique_objectif = []
if "historique_cours" not in st.session_state:
    st.session_state.historique_cours = []


# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎮 GamiTeach</h1>
    <p>Assistant IA de gamification pédagogique · Basé sur l'ontologie TGC</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# ─────────────────────────────────────────────
#  ÉTAPE 1 — ONBOARDING PROFIL ENSEIGNANT (TGC)
# ─────────────────────────────────────────────
if not st.session_state.profile_complete:

    st.markdown("""
    <div class="onboarding-box">
        <h3>👤 Créez votre profil enseignant</h3>
        <p>GamiTeach personnalise chaque recommandation selon votre profil.<br>
        Ces informations proviennent de l'ontologie <strong>TGC (Teacher in Gamified Context)</strong>.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_profil"):
        st.markdown("##### 🧑‍🏫 Identité & Contexte d'enseignement")
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Prénom *", placeholder="ex : Sara")
        with c2:
            academic_title = st.selectbox("Titre académique *", TGC_ACADEMIC_TITLES)
        with c3:
            subject_area = st.selectbox("Domaine *", TGC_SUBJECT_AREAS)

        c4, c5 = st.columns(2)
        with c4:
            first_language = st.selectbox("Langue principale", TGC_LANGUAGES)
        with c5:
            second_language = st.selectbox("Langue secondaire", ["Aucune"] + TGC_LANGUAGES)

        st.markdown("---")
        st.markdown("##### 🎮 Profil de joueur & Style d'enseignement")
        c6, c7 = st.columns(2)
        with c6:
            player_type = st.selectbox(
                "Type de joueur (TGC) *",
                list(TGC_PLAYER_TYPES.keys()),
                format_func=lambda x: f"{x} – {TGC_PLAYER_TYPES[x][:40]}…"
            )
        with c7:
            teaching_style = st.selectbox("Style d'enseignement *", TGC_TEACHING_STYLES)

        st.markdown("---")
        st.markdown("##### 📊 Expérience & Compétences numériques")
        c8, c9 = st.columns(2)
        with c8:
            ped_experience  = st.selectbox("Expérience pédagogique *", TGC_PED_EXPERIENCE)
            gamif_experience = st.selectbox("Expérience en gamification *", TGC_GAMIF_EXPERIENCE)
        with c9:
            digital_content = st.selectbox(
                "Compétence numérique – Contenu *",
                list(TGC_DIGITAL_CONTENT.keys()),
                format_func=lambda x: f"{x} – {TGC_DIGITAL_CONTENT[x][:45]}…"
            )
            social_commitment = st.selectbox(
                "Engagement social numérique *",
                list(TGC_SOCIAL_COMMITMENT.keys()),
                format_func=lambda x: "Socialement compétent" if x == "socially_competent" else "Engagement limité"
            )

        st.markdown("---")
        st.markdown("##### 🎓 Contexte du cours")
        c10, c11 = st.columns(2)
        with c10:
            course_name   = st.text_input("Nom du cours", placeholder="ex : Introduction à la Programmation")
            learner_level = st.selectbox("Niveau des apprenants", ["Primaire","Collège","Lycée","Licence","Master","Formation pro"])
        with c11:
            age = st.number_input("Âge (optionnel)", min_value=20, max_value=99, value=35, step=1)

        submitted = st.form_submit_button("✅ Créer mon profil et accéder à GamiTeach", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Veuillez entrer votre prénom.")
        else:
            st.session_state.teacher_profile = {
                "name": name.strip(),
                "academic_title": academic_title,
                "subject_area": subject_area,
                "first_language": first_language,
                "second_language": second_language,
                "player_type": player_type,
                "teaching_style": teaching_style,
                "ped_experience": ped_experience,
                "gamif_experience": gamif_experience,
                "digital_content": digital_content,
                "social_commitment": social_commitment,
                "course_name": course_name.strip() if course_name.strip() else "Non précisé",
                "learner_level": learner_level,
                "age": age,
            }
            st.session_state.profile_complete = True
            st.rerun()

# ─────────────────────────────────────────────
#  ÉTAPE 2 — INTERFACE PRINCIPALE (profil créé)
# ─────────────────────────────────────────────
else:
    p = st.session_state.teacher_profile

    # ── SIDEBAR : résumé du profil TGC ──
    with st.sidebar:
        st.markdown("### 👤 Profil TGC actif")
        st.markdown(f"""
        <div class="profile-card">
            <h4>Enseignant(e)</h4>
            <div>
                <span class="profile-tag highlight">{p['name']}</span>
                <span class="profile-tag">{p['academic_title']}</span>
                <span class="profile-tag">{p['subject_area']}</span>
            </div>
            <div style="margin-top:0.5rem">
                <span class="profile-tag">🎮 {p['player_type']}</span>
                <span class="profile-tag">📐 {p['teaching_style']}</span>
            </div>
            <div style="margin-top:0.5rem">
                <span class="profile-tag">Pédagogie : {p['ped_experience']}</span>
                <span class="profile-tag">Gamif. : {p['gamif_experience']}</span>
            </div>
            <div style="margin-top:0.5rem">
                <span class="profile-tag">🖥️ {p['digital_content']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if p["course_name"] != "Non précisé":
            st.markdown(f"""
            <div class="profile-card" style="border-color: rgba(52,211,153,0.25);">
                <h4 style="color:#34d399">Cours actif</h4>
                <div>
                    <span class="profile-tag highlight">{p['course_name']}</span>
                    <span class="profile-tag">{p['learner_level']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### 🧹 Réinitialiser")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Chat 1", use_container_width=True):
                st.session_state.historique_objectif = []
                st.rerun()
        with col2:
            if st.button("Chat 2", use_container_width=True):
                st.session_state.historique_cours = []
                st.rerun()

        if st.button("🔄 Modifier mon profil", use_container_width=True):
            st.session_state.profile_complete = False
            st.session_state.historique_objectif = []
            st.session_state.historique_cours = []
            st.rerun()

        st.markdown("---")
        st.markdown(
            "<small style='color:#475569'>GamiTeach · MVP Semaine 1<br>DS50 – Christine Lahoud<br>Ontologie TGC v1.0.0</small>",
            unsafe_allow_html=True,
        )

    # ── TABS ──
    tab1, tab2 = st.tabs([
        "🎯  Mode 1 – Objectif pédagogique",
        "📚  Mode 2 – Question sur le cours",
    ])

    # ══════════════════════════════════════════════
    #  TAB 1 — Objectif pédagogique
    # ══════════════════════════════════════════════
    with tab1:
        st.markdown(
            '<span class="mode-badge mode-objectif">🎯 Objectif pédagogique → Recommandations gamification</span>',
            unsafe_allow_html=True,
        )

        # Hint personnalisé selon profil
        pt_hint = {
            "Achiever":       "Votre profil **Achiever** → les recommandations mettront l'accent sur les badges, classements et défis individuels.",
            "Socializer":     "Votre profil **Socializer** → les recommandations privilégieront la collaboration et les quêtes de groupe.",
            "Free_Spirit":    "Votre profil **Free Spirit** → les recommandations favoriseront l'exploration libre et les parcours ouverts.",
            "Philanthropist": "Votre profil **Philanthropist** → les recommandations valoriseront le mentorat et le partage de connaissances.",
        }
        st.markdown(
            f'<div class="context-hint">✨ {pt_hint.get(p["player_type"], "")}</div>',
            unsafe_allow_html=True,
        )

        for msg in st.session_state.historique_objectif:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-bubble bubble-user"><div class="bubble-label">Vous</div>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble bubble-assistant"><div class="bubble-label">🤖 GamiTeach</div>{msg["content"]}</div>', unsafe_allow_html=True)

        st.markdown("---")
        with st.form("form_objectif", clear_on_submit=True):
            objectif_input = st.text_area(
                "Votre objectif pédagogique",
                placeholder=f"Ex : Je veux améliorer l'engagement de mes étudiants en {p['learner_level']} dans mon cours de {p['subject_area']}…",
                height=90, label_visibility="collapsed",
            )
            submitted1 = st.form_submit_button("✨ Obtenir des recommandations", use_container_width=True)

        if submitted1 and objectif_input.strip():
            st.session_state.historique_objectif.append({"role": "user", "content": objectif_input})
            with st.spinner("GamiTeach analyse votre profil TGC et génère une recommandation…"):
                time.sleep(1.3)
                reponse = dummy_objectif_pedagogique(objectif_input, p)
            st.session_state.historique_objectif.append({"role": "assistant", "content": reponse})
            st.rerun()

        if not st.session_state.historique_objectif:
            st.info(f"💡 Exemples d'objectifs pour un enseignant **{p['teaching_style']}** : améliorer la participation, encourager la mémorisation, renforcer la collaboration entre apprenants…")

    # ══════════════════════════════════════════════
    #  TAB 2 — Question sur le cours (RAG)
    # ══════════════════════════════════════════════
    with tab2:
        st.markdown(
            '<span class="mode-badge mode-cours">📚 Question sur le cours → Suggestion gamifiée (RAG)</span>',
            unsafe_allow_html=True,
        )

        if p["course_name"] == "Non précisé":
            st.warning("⚠️ Aucun cours renseigné dans votre profil. Modifiez-le via la barre latérale.")
        else:
            dc_hint = (
                "En tant que **Curator**, GamiTeach vous proposera des ressources gamifiées existantes à adapter."
                if p["digital_content"] == "Curator" else
                "En tant que **Creator**, GamiTeach vous aidera à concevoir vos propres activités gamifiées."
            )
            st.markdown(f'<div class="context-hint">🖥️ {dc_hint}</div>', unsafe_allow_html=True)

        for msg in st.session_state.historique_cours:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-bubble bubble-user"><div class="bubble-label">Vous</div>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble bubble-assistant"><div class="bubble-label">🤖 GamiTeach</div>{msg["content"]}</div>', unsafe_allow_html=True)

        st.markdown("---")
        with st.form("form_cours", clear_on_submit=True):
            question_input = st.text_area(
                "Votre question sur le cours",
                placeholder=f"Ex : Comment introduire un concept difficile de {p['course_name']} de façon engageante ?",
                height=90, label_visibility="collapsed",
            )
            submitted2 = st.form_submit_button("🔍 Interroger le cours", use_container_width=True)

        if submitted2 and question_input.strip():
            st.session_state.historique_cours.append({"role": "user", "content": question_input})
            with st.spinner("Recherche dans le cours et personnalisation selon votre profil TGC…"):
                time.sleep(1.5)
                reponse = dummy_question_cours(question_input, p)
            st.session_state.historique_cours.append({"role": "assistant", "content": reponse})
            st.rerun()

        if not st.session_state.historique_cours:
            st.info(f"💡 Exemples de questions pour votre cours *{p['course_name']}* : comment gamifier l'évaluation ? quels défis proposer pour ce chapitre ?")