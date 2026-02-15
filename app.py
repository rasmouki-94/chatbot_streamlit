from __future__ import annotations

import html
import time
from datetime import datetime, timezone

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from email_validator import EmailNotValidError, validate_email

from utils.emailer import send_admin_email
from utils.scoring import calculate_score, calculate_subscores, determine_band, get_top_leaks
from utils.storage import append_to_csv

load_dotenv()

st.set_page_config(page_title="Diagnostic Process PME", page_icon="💬", layout="centered")


QUESTIONS = [
    {
        "id": "q1",
        "text": "Aujourd'hui, pour piloter vos opérations au quotidien, vous vous appuyez principalement sur :",
        "options": [
            (
                "Principalement Excel",
                2,
                "Excel est un outil puissant — surtout entre de bonnes mains.<br>Mais dans beaucoup d'industries, il finit par devenir le centre névralgique… sans offrir la visibilité d'un vrai système de pilotage.",
            ),
            (
                "Excel + plusieurs outils dispersés",
                1,
                "Multiplier les outils permet souvent d'aller vite au début.<br>Mais sans intégration claire, cela crée progressivement des zones floues où chacun travaille avec sa propre lecture de la réalité.",
            ),
            ("Un ERP bien structuré", 0, None),
        ],
    },
    {
        "id": "q2",
        "text": "Aujourd'hui, combien de versions d'un même fichier circulent réellement dans votre organisation ?",
        "options": [
            ("Une seule version claire", 0, None),
            (
                "2 à 3 versions selon les équipes",
                1,
                "Lorsque plusieurs versions coexistent, les décisions prennent mécaniquement plus de temps.<br>On passe de l'analyse… à la vérification.",
            ),
            (
                "Honnêtement, difficile à dire",
                2,
                "Ne pas savoir quelle est la &laquo;&nbsp;bonne version&nbsp;&raquo; n'est pas un manque de rigueur.<br>C'est souvent le signe qu'un process a grandi plus vite que sa structure.",
            ),
        ],
    },
    {
        "id": "q3",
        "text": "Chaque semaine, combien d'heures vos équipes consacrent-elles à consolider, vérifier ou recouper des données ?",
        "options": [
            ("Moins d'1h", 0, None),
            (
                "1 à 3h",
                1,
                "3h par semaine représentent environ 150h par an.<br>À l'échelle d'un responsable ou d'une assistante, cela peut facilement représenter 8 000 à 10 000€ immobilisés… sans création de valeur directe.",
            ),
            (
                "Plus de 3h",
                2,
                "Au-delà de 3h par semaine, on dépasse souvent 200 à 300 heures par an.<br>Ce sont plusieurs semaines de travail consacrées non pas à piloter, mais à vérifier.",
            ),
        ],
    },
    {
        "id": "q4",
        "text": "Les retards dans vos projets sont généralement :",
        "options": [
            ("Visibles immédiatement", 0, None),
            (
                "Identifiés lors d'un point hebdomadaire",
                1,
                "Un point hebdomadaire est structurant.<br>Mais une semaine peut suffire à transformer un léger décalage en situation sous tension.",
            ),
            (
                "Découverts une fois qu'ils ont déjà un impact",
                2,
                "Découvrir un retard après coup n'est pas une erreur individuelle.<br>C'est souvent le signe qu'il manque un système d'alerte en amont.",
            ),
        ],
    },
    {
        "id": "q5",
        "text": "Vos indicateurs clés sont aujourd'hui :",
        "options": [
            ("Automatiquement mis à jour", 0, None),
            (
                "Semi-manuellement consolidés",
                1,
                "Chaque manipulation manuelle est une charge invisible.<br>Elle mobilise de l'attention, crée un risque d'erreur… et détourne du pilotage stratégique.",
            ),
            (
                "Entièrement mis à jour à la main",
                2,
                "30 minutes par jour de ressaisie représentent environ 110h par an.<br>À l'échelle d'une équipe, cela peut rapidement dépasser 10 000€ par an en temps mobilisé.",
            ),
        ],
    },
    {
        "id": "q6",
        "text": "Si je vous demande maintenant le statut exact d'une deadline critique, vous avez besoin de :",
        "options": [
            ("Quelques secondes", 0, None),
            (
                "Quelques minutes",
                1,
                "Quelques minutes semblent anodines.<br>Mais multipliées par plusieurs vérifications quotidiennes, cela représente des dizaines d'heures par an consacrées uniquement à chercher l'information.",
            ),
            (
                "Plus de 30 minutes",
                2,
                "Lorsque vérifier une échéance prend 30 minutes,<br>cela signifie généralement que l'information existe… mais n'est pas structurée pour décider rapidement.",
            ),
        ],
    },
    {
        "id": "q7",
        "text": "Est-ce que certaines demandes disparaissent temporairement avant d'être traitées ?",
        "options": [
            ("Jamais", 0, None),
            (
                "Rarement",
                1,
                "Même rarement, une demande oubliée peut créer une chaîne d'ajustements imprévus.<br>Et souvent, c'est l'urgence qui révèle la faiblesse du process.",
            ),
            (
                "Oui, cela arrive régulièrement",
                2,
                "Quand les demandes se perdent, le problème n'est pas humain.<br>C'est souvent l'absence d'un système clair de suivi et de priorisation.",
            ),
        ],
    },
    {
        "id": "q8",
        "text": "Si la personne qui tient le fichier principal s'absente une semaine :",
        "options": [
            ("Aucun impact", 0, None),
            (
                "L'activité ralentit sensiblement",
                1,
                "Un ralentissement temporaire est courant.<br>Mais lorsqu'il dépend d'une seule personne, le risque organisationnel devient structurel.",
            ),
            (
                "L'organisation est réellement en difficulté",
                2,
                "Lorsque la connaissance repose sur une seule tête,<br>la continuité opérationnelle devient fragile — même avec des équipes compétentes.",
            ),
        ],
    },
    {
        "id": "q9",
        "text": "Au cours des 12 derniers mois, avez-vous connu des urgences coûteuses ou des pénalités liées à un manque de visibilité ?",
        "options": [
            ("Non", 0, None),
            (
                "Une ou deux situations isolées",
                1,
                "Une seule urgence peut représenter plusieurs milliers d'euros.<br>Mais surtout, elle mobilise l'énergie des équipes en mode &laquo;&nbsp;réaction&nbsp;&raquo;.",
            ),
            (
                "Oui, plusieurs situations",
                2,
                "Lorsque les urgences deviennent répétitives,<br>cela indique souvent que le pilotage est plus réactif que prédictif.",
            ),
        ],
    },
    {
        "id": "q10",
        "text": "Avec recul, vos process actuels vous semblent :",
        "options": [
            ("Robustes", 0, None),
            (
                "Corrects mais perfectibles",
                1,
                "C'est souvent à ce stade que les fuites invisibles commencent à s'installer.<br>Rien de dramatique… mais un potentiel d'optimisation réel.",
            ),
            (
                "Fragiles",
                2,
                "Un process fragile ne coûte pas toujours cher immédiatement.<br>Mais il finit presque toujours par coûter cher au mauvais moment.",
            ),
        ],
    },
]

LEAD_QUESTIONS = [
    ("prenom", "Quel est votre prénom ?"),
    ("nom", "Quel est votre nom ?"),
    ("entreprise", "Quel est le nom de votre entreprise ?"),
    ("email", "Quelle est votre adresse email ?"),
]

QUESTION_TEXTS = {
    "q1": "Outils de pilotage des opérations",
    "q2": "Versions de fichiers en circulation",
    "q3": "Temps de consolidation des données",
    "q4": "Visibilité des retards projets",
    "q5": "Mise à jour des indicateurs clés",
    "q6": "Temps d'accès au statut d'une deadline",
    "q7": "Demandes qui disparaissent",
    "q8": "Dépendance à une personne clé",
    "q9": "Urgences coûteuses (12 derniers mois)",
    "q10": "Robustesse des process actuels",
}


def load_css() -> None:
    with open("static/styles.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def init_state() -> None:
    if "step" not in st.session_state:
        st.session_state.step = "questions"
        st.session_state.question_index = 0
        st.session_state.responses = {}
        st.session_state.response_labels = {}
        st.session_state.lead = {"prenom": "", "nom": "", "entreprise": "", "email": ""}
        st.session_state.lead_index = 0
        st.session_state.progress = 0
        st.session_state.result = {}
        st.session_state.saved = False
        st.session_state.mail_sent = False
        st.session_state.chat = []
        st.session_state.show_typing = False
        add_bot_message(
            "Bonjour 👋<br>En 2 minutes, je vais vous aider à mettre des mots (et des chiffres) sur ce que vous ressentez peut-être déjà dans votre organisation."
        )
        add_bot_message(QUESTIONS[0]["text"])


def add_bot_message(text: str) -> None:
    st.session_state.chat.append({"role": "bot", "text": text})


def add_user_message(text: str) -> None:
    st.session_state.chat.append({"role": "user", "text": text})


def compute_progress() -> int:
    question_part = (len(st.session_state.responses) / len(QUESTIONS)) * 75
    lead_filled = sum(1 for field, _ in LEAD_QUESTIONS if st.session_state.lead.get(field, "").strip())
    lead_part = (lead_filled / len(LEAD_QUESTIONS)) * 15

    if st.session_state.step == "result":
        return 100
    if st.session_state.step == "lead":
        return round(75 + lead_part)
    return round(question_part)


def update_progress() -> None:
    st.session_state.progress = compute_progress()
    col_left, col_right = st.columns([6, 1])
    with col_left:
        st.progress(st.session_state.progress / 100)
    with col_right:
        st.markdown(f"<div class='progress-label'>{st.session_state.progress}%</div>", unsafe_allow_html=True)


def auto_scroll() -> None:
    """Inject JS via components.html to scroll the chat window in the parent frame."""
    components.html(
        """
        <script>
            function doScroll() {
                var el = window.parent.document.querySelector('.chat-window');
                if (el) { el.scrollTop = el.scrollHeight; }
            }
            doScroll();
            setTimeout(doScroll, 100);
            setTimeout(doScroll, 300);
            setTimeout(doScroll, 600);
            setTimeout(doScroll, 1200);
        </script>
        """,
        height=0,
    )


def render_chat() -> None:
    chunks = []
    for message in st.session_state.chat:
        cls = "bubble bot" if message["role"] == "bot" else "bubble user"
        safe_text = message["text"]
        chunks.append(f"<div class='{cls}'>{safe_text}</div>")

    if st.session_state.get("show_typing"):
        chunks.append(
            "<div class='typing-indicator'>"
            "<span></span><span></span><span></span>"
            "</div>"
        )

    html_chat = (
        "<div id='chat-window' class='chat-window'>"
        + "".join(chunks)
        + "<div id='chat-anchor'></div>"
        + "</div>"
        + """<script>
            function scrollChat() {
                // Try multiple selectors to handle Streamlit iframe structure
                var el = document.getElementById('chat-window');
                if (!el) {
                    var els = window.parent.document.querySelectorAll('[id="chat-window"]');
                    if (els.length > 0) el = els[els.length - 1];
                }
                if (el) { el.scrollTop = el.scrollHeight; }
            }
            scrollChat();
            setTimeout(scrollChat, 50);
            setTimeout(scrollChat, 150);
            setTimeout(scrollChat, 300);
            setTimeout(scrollChat, 500);
            setTimeout(scrollChat, 1000);
        </script>"""
    )
    st.markdown(html_chat, unsafe_allow_html=True)


def handle_question_submit(question_idx: int, selected_index: int) -> None:
    question = QUESTIONS[question_idx]
    selected_label, selected_score, impact = question["options"][selected_index]
    add_user_message(html.escape(selected_label))
    st.session_state.responses[question["id"]] = selected_score
    st.session_state.response_labels[question["id"]] = selected_label
    st.session_state.question_index += 1

    if impact:
        add_bot_message(impact)

    if st.session_state.question_index < len(QUESTIONS):
        add_bot_message(QUESTIONS[st.session_state.question_index]["text"])
    else:
        st.session_state.step = "lead"
        st.session_state.lead_index = 0
        add_bot_message(LEAD_QUESTIONS[0][1])


def handle_lead_submit(value: str) -> str | None:
    field, _ = LEAD_QUESTIONS[st.session_state.lead_index]
    clean_value = value.strip()
    if not clean_value:
        return "Ce champ est requis."

    if field == "email":
        try:
            clean_value = validate_email(clean_value, check_deliverability=False).email
        except EmailNotValidError:
            return "Adresse email invalide."

    st.session_state.lead[field] = clean_value
    add_user_message(html.escape(clean_value))
    st.session_state.lead_index += 1

    if st.session_state.lead_index < len(LEAD_QUESTIONS):
        add_bot_message(LEAD_QUESTIONS[st.session_state.lead_index][1])
    else:
        score = calculate_score(st.session_state.responses)
        subscores = calculate_subscores(st.session_state.responses)
        band = determine_band(score)
        leaks = get_top_leaks(subscores)
        st.session_state.result = {"score": score, "band": band, "leaks": leaks, "subscores": subscores}
        st.session_state.step = "result"
        add_bot_message("Merci. Voici votre diagnostic personnalisé.")
    return None


def result_impact_text(score: int) -> str:
    if score >= 15:
        return (
            "Même 1 heure par jour consacrée à des tâches de consolidation ou de recherche d'information représente plus de 200 heures par an.<br>"
            "À 60€ de l'heure, cela peut facilement dépasser 12 000€ immobilisés — sans amélioration directe de la performance.<br><br>"
            "La bonne nouvelle : ces heures ne sont pas perdues par manque de compétence.<br>"
            "Elles sont souvent récupérables avec une meilleure structuration."
        )
    if score >= 7:
        return (
            "Votre organisation est sous tension : des heures utiles sont probablement absorbées par la coordination, la vérification et la ressaisie.<br>"
            "Un cadrage plus structuré permet souvent de récupérer rapidement du temps opérationnel."
        )
    return (
        "Votre base de pilotage semble maîtrisée. Les gains se jouent surtout sur l'optimisation continue et la réduction des frictions résiduelles."
    )


def persist_completion() -> None:
    if st.session_state.saved:
        return

    export_row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prenom": st.session_state.lead["prenom"],
        "nom": st.session_state.lead["nom"],
        "entreprise": st.session_state.lead["entreprise"],
        "email": st.session_state.lead["email"],
        "score": st.session_state.result["score"],
        "band": st.session_state.result["band"],
    }
    for idx, question in enumerate(QUESTIONS, start=1):
        export_row[f"q{idx}"] = st.session_state.response_labels.get(question["id"], "")

    append_to_csv(export_row)
    st.session_state.saved = True
    st.session_state.mail_sent = send_admin_email(export_row)


def show_typing_then_rerun() -> None:
    """Show the typing indicator briefly, then rerun to display the actual messages."""
    st.session_state.show_typing = True
    st.rerun()


def main() -> None:
    load_css()
    init_state()

    # Handle the typing indicator phase: show it briefly, then clear and rerun
    if st.session_state.get("show_typing"):
        st.markdown("<div class='app-shell'>", unsafe_allow_html=True)
        update_progress()
        render_chat()
        auto_scroll()
        st.markdown("</div>", unsafe_allow_html=True)
        time.sleep(2)
        st.session_state.show_typing = False
        st.rerun()

    st.markdown(
        "<h2 class='app-title'>Identifiez vos pertes de temps et d'argent en quelques questions</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='app-shell'>", unsafe_allow_html=True)
    update_progress()
    render_chat()
    auto_scroll()

    st.markdown("<div class='input-sticky'>", unsafe_allow_html=True)
    if st.session_state.step == "questions":
        q_idx = st.session_state.question_index
        current = QUESTIONS[q_idx]

        for opt_idx, (label, _score, _impact) in enumerate(current["options"]):
            if st.button(label, key=f"opt_{q_idx}_{opt_idx}", use_container_width=True):
                handle_question_submit(q_idx, opt_idx)
                show_typing_then_rerun()

    elif st.session_state.step == "lead":
        lead_field, _ = LEAD_QUESTIONS[st.session_state.lead_index]
        value = st.text_input(
            "Votre réponse",
            key=f"lead_input_{lead_field}",
            label_visibility="collapsed",
            placeholder="Saisissez votre réponse...",
        )
        if st.button("Valider", use_container_width=True):
            error = handle_lead_submit(value)
            if error:
                st.warning(error)
            else:
                show_typing_then_rerun()

        st.markdown(
            "<p class='consent'>En soumettant ces informations, vous acceptez d'être recontacté au sujet de votre diagnostic.</p>",
            unsafe_allow_html=True,
        )

    else:
        persist_completion()
        result = st.session_state.result
        company = html.escape(st.session_state.lead["entreprise"])
        band = result["band"]
        badge_class = "badge green" if "Maîtrisé" in band else "badge orange" if "Sous tension" in band else "badge red"

        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-title">Diagnostic — {company}</div>
                <div class="{badge_class}">{html.escape(band)}</div>
                <div class="result-score">Score : {result["score"]}/20</div>
                <div class="result-subtitle">Top 3 fuites</div>
                <ul class="leaks">
                    <li>{html.escape(result["leaks"][0])}</li>
                    <li>{html.escape(result["leaks"][1])}</li>
                    <li>{html.escape(result["leaks"][2])}</li>
                </ul>
                <div class="impact-block">{result_impact_text(result["score"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<a href="https://www.linkedin.com/in/arsmouk-data-analyst/" target="_blank" class="linkedin-cta">Discutons sur LinkedIn</a>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        '<p class="dev-credit">Développé par <a href="https://www.linkedin.com/in/arsmouk-data-analyst/" target="_blank">Abd Arsmouk</a></p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
