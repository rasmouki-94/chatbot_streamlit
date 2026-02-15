# Diagnostic Process PME - Streamlit

Application Streamlit orientée conversion, avec UX chatbot, scoring opérationnel, sauvegarde CSV UTF-8 et notification email admin.

## Lancer en local

1. Installer les dépendances :

```bash
pip install -r requirements.txt
```

2. Configurer les variables d’environnement (facultatif pour l’email) :

```bash
ADMIN_EMAIL=admin@exemple.com
SMTP_USER=smtp_user@exemple.com
SMTP_PASS=mot_de_passe_smtp
```

3. Démarrer l’application :

```bash
streamlit run app.py
```

## Déploiement Streamlit Cloud

1. Pousser le repo sur GitHub.
2. Créer une app sur Streamlit Cloud en pointant vers `app.py`.
3. Ajouter les secrets (`ADMIN_EMAIL`, `SMTP_USER`, `SMTP_PASS`) dans la section **Secrets**.
4. Déployer.

## Variables d’environnement

- `ADMIN_EMAIL` : email destinataire des notifications.
- `SMTP_USER` : compte SMTP utilisé pour l’envoi.
- `SMTP_PASS` : mot de passe / app password SMTP.

Si ces variables ne sont pas définies, l’application continue de fonctionner sans envoi d’email (pas de crash).
