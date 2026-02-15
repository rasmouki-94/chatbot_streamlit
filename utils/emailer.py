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
        <table cellpadding="4" cellspacing="0" border="1" style="border-collapse: collapse; font-size: 14px;">
          <tr><td><b>Prénom</b></td><td>{{ prenom }}</td></tr>
          <tr><td><b>Nom</b></td><td>{{ nom }}</td></tr>
          <tr><td><b>Entreprise</b></td><td>{{ entreprise }}</td></tr>
          <tr><td><b>Email</b></td><td>{{ email }}</td></tr>
          <tr><td><b>Score</b></td><td>{{ score }}/20</td></tr>
          <tr><td><b>Bande</b></td><td>{{ band }}</td></tr>
        </table>
      </body>
    </html>
    """
)


def send_admin_email(data: Dict[str, str | int]) -> bool:
    admin_email = os.getenv("ADMIN_EMAIL")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not admin_email or not smtp_user or not smtp_pass:
        return False

    try:
        yag = yagmail.SMTP(user=smtp_user, password=smtp_pass)
        html_content = HTML_TEMPLATE.render(**data)
        yag.send(
            to=admin_email,
            subject=f"Diagnostic PME - {data.get('entreprise', 'Sans entreprise')}",
            contents=[html_content],
        )
        return True
    except Exception:
        return False
