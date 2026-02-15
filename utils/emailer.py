from __future__ import annotations

import os
from typing import Dict

import yagmail
from jinja2 import Template


HTML_TEMPLATE = Template(
    """
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.4;">
        <h3 style="margin-bottom: 8px;">Nouveau diagnostic complété</h3>
        <table cellpadding="6" cellspacing="0" border="1" style="border-collapse: collapse; font-size: 14px; margin-bottom: 20px;">
          <tr><td><b>Prénom</b></td><td>{{ prenom }}</td></tr>
          <tr><td><b>Nom</b></td><td>{{ nom }}</td></tr>
          <tr><td><b>Entreprise</b></td><td>{{ entreprise }}</td></tr>
          <tr><td><b>Email</b></td><td>{{ email }}</td></tr>
          <tr><td><b>Score</b></td><td>{{ score }}/20</td></tr>
          <tr><td><b>Bande</b></td><td>{{ band }}</td></tr>
        </table>

        <h3 style="margin-bottom: 8px;">Détail des réponses</h3>
        <table cellpadding="6" cellspacing="0" border="1" style="border-collapse: collapse; font-size: 14px; width: 100%;">
          <tr style="background: #f5f5f7;">
            <th style="text-align: left; padding: 8px;">#</th>
            <th style="text-align: left; padding: 8px;">Question</th>
            <th style="text-align: left; padding: 8px;">Réponse</th>
          </tr>
          {% for item in details %}
          <tr>
            <td style="padding: 8px;">{{ item.num }}</td>
            <td style="padding: 8px;">{{ item.label }}</td>
            <td style="padding: 8px;">{{ item.answer }}</td>
          </tr>
          {% endfor %}
        </table>
      </body>
    </html>
    """
)

QUESTION_LABELS = {
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


def send_admin_email(data: Dict[str, str | int]) -> bool:
    admin_email = os.getenv("ADMIN_EMAIL")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not admin_email or not smtp_user or not smtp_pass:
        return False

    try:
        details = []
        for i in range(1, 11):
            key = f"q{i}"
            answer = data.get(key, "")
            details.append({
                "num": i,
                "label": QUESTION_LABELS.get(key, f"Question {i}"),
                "answer": answer,
            })

        yag = yagmail.SMTP(user=smtp_user, password=smtp_pass)
        html_content = HTML_TEMPLATE.render(details=details, **data)
        yag.send(
            to=admin_email,
            subject=f"Diagnostic PME - {data.get('entreprise', 'Sans entreprise')}",
            contents=[html_content],
        )
        return True
    except Exception:
        return False
