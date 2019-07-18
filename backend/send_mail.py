"""
     Fonctions permettant l'envoie de mail
"""
from flask import url_for, current_app

from geonature.utils.utilsmails import send_mail


def export_send_mail(role, export, file_name):
    """
        Send email after export is done

        .. :quickref: Send email after export is done


        :query User role: User who run the export
        :query {} export: Export definition
        :query str file_name: Name of exported file
    """
    url = url_for('static', filename='exports/'+file_name)

    msg = """
        Bonjour,
        <p>
            Votre export {} est accessible via le lien suivant
            <a href="{}">Lien de téléchargement</a>
        </p>
        <p>
            Les données de cet export sont associée à la licence <a href="{}">{}</a>.
            Merci de les utiliser en respectant la licence.
        </p>
        <p>
            <b>Attention : Ce fichier sera supprimé sous {} jours</b>
        </p>
    """.format(
        export['label'],
        url,
        export['licence']['url_licence'],
        export['licence']['name_licence'],
        str(current_app.config['EXPORTS']['nb_days_keep_file'])
    )
    send_mail(
        recipients=[role.email],
        subject="[GeoNature]Export {} réalisé".format(export['label']),
        msg_html=msg
    )


def export_send_mail_error(role, export, error):
    """
        Send email after export is failed

        .. :quickref: Send email after export is failed


        :query User role: User who run the export
        :query {} export: Export definition
        :query str error: Detail of the exception raised

    """

    label = ""
    if export:
        label = export['label']

    msg = """
        Bonjour,
        <p>
            Votre export {} n'a pas fonctionné correctement
        </p>
        <p>
            <b>Detail</b>
            {}
        </p>
        <p>
            Veuillez signaler le problème à l'administrateur du site
        </p>
    """.format(label, error)
    send_mail(
        recipients=[role.email],
        subject="[GeoNature][ERREUR]Export {}".format(label),
        msg_html=msg
    )
