# Fonctions permettant l'envoie de mail
from flask import url_for

from geonature.utils.utilsmails import send_mail

def export_send_mail(role, export, file_name):

    url = url_for('static', filename='exports/'+file_name)

    msg = """
        Bonjour,
        <p>
            Votre export {} est accessible via le lien suivant
            <a href="{}">Lien de téléchargement</a>
        </p>
        <p>
            <b>Attention : Ce fichier sera supprimé sous 15 jours</b>
        </p>
    """.format(export['label'], url)
    send_mail(
        recipients=[role.email],
        subject="[GeoNature]Export {} réalisé".format(export['label']),
        msg_html=msg
    )


