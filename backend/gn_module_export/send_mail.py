"""
     Fonctions permettant l'envoi d'email
"""
from flask import url_for, current_app

from geonature.utils.utilsmails import send_mail


def export_send_mail(mail_to, export, file_name):
    """
    Send email after export is done

    .. :quickref: Send email after export is done


    :query [str] mail_to: User who runs the export
    :query {} export: Export definition
    :query str file_name: Name of exported file
    """
    module_conf = current_app.config["EXPORTS"]

    if module_conf.get("export_web_url"):
        url = "{}/{}".format(module_conf.get("export_web_url"), file_name)
    else:
        url = url_for(
            "media",
            filename=module_conf.get("usr_generated_dirname") + "/" + file_name,
            _external=True,
        )

    msg = """
            Bonjour,
            <p>
                Votre export <i>{}</i> est accessible via le lien suivant :
                <a href="{}">Téléchargement</a>.
            </p>
            <p>
                Les données de cet export sont associées à la licence <a href="{}">{}</a>.
                Merci de les utiliser en respectant cette licence.
            </p>
            <p>
                <b>Attention</b> : Ce fichier sera supprimé sous {} jours.
            </p>
        """.format(
        export["label"],
        url,
        export["licence"]["url_licence"],
        export["licence"]["name_licence"],
        str(current_app.config["EXPORTS"]["nb_days_keep_file"]),
    )

    send_mail(
        recipients=mail_to,
        subject="[GeoNature] Export {} réalisé".format(export["label"]),
        msg_html=msg,
    )


def export_send_mail_error(mail_to, export, error):
    """
    Send email after export is failed

    .. :quickref: Send email after export is failed


    :query [str] mail_to: User who runs the export
    :query {} export: Export definition
    :query str error: Detail of the exception raised

    """

    label = ""
    if export:
        label = export["label"]

    msg = """
        Bonjour,
        <p>
            Votre export <i>{}</i> n'a pas fonctionné correctement.
        </p>
        <p>
            <b>Detail : </b>
            {}
        </p>
        <p>
            Veuillez signaler le problème à l'administrateur du site.
        </p>
    """.format(
        label, error
    )

    # Si configuration de mail_on_error
    #   envoie d'un mail d'erreur à l'administrateur
    if "ERROR_MAIL_TO" in current_app.config:
        if (
            type(current_app.config["ERROR_MAIL_TO"]) is list
            and current_app.config["ERROR_MAIL_TO"]
        ):
            export_send_admin_mail_error(
                current_app.config["ERROR_MAIL_TO"], export, error
            )

    send_mail(
        recipients=mail_to,
        subject="[GeoNature][ERREUR] Export {}".format(label),
        msg_html=msg,
    )


def export_send_admin_mail_error(mail_to, export, error):
    """
    Send email after export has failed

    .. :quickref: Send email after export has failed


    :query [str] role: User who runs the export
    :query {} export: Export definition
    :query str error: Detail of the exception raised

    """

    label = ""
    if export:
        label = export["label"]

    msg = """
        Bonjour,
        <p>
            L'export <i>{}</i> n'a pas fonctionné correctement.
        </p>
        <p>
            <b>Detail : </b>
            {}
        </p>
    """.format(
        label, error
    )
    send_mail(
        recipients=mail_to,
        subject="[GeoNature-export][ERREUR] Export {}".format(label),
        msg_html=msg,
    )
