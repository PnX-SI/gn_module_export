import os
import sys
import subprocess

from pathlib import Path
from crontab import CronTab

from geonature.utils.utilsmails import send_mail
from geonature.utils.errors import GNModuleInstallError
from geonature.utils.env import BACKEND_DIR, ROOT_DIR

MODULE_DIR = Path(__file__).absolute().parent


def gnmodule_install_app(gn_db, gn_app):
    '''
        Fonction principale permettant de réaliser les opérations
        d'installation du module :
            - Base de données
            - Module (pour le moment rien)
    '''
    with gn_app.app_context():
        try:
            test_mail_config(gn_app)
        except GNModuleInstallError as e:
            raise e
        except Exception:
            raise GNModuleInstallError("Mail config is not correct please read the doc")  # noqa: E501

        # here = Path(__file__).parent
        requirements_path = MODULE_DIR / 'backend' / 'requirements.txt'
        assert requirements_path.is_file()
        subprocess.call(
            [sys.executable, '-m', 'pip', 'install', '-r', '{}'.format(requirements_path)],  # noqa: E501
            cwd=str(MODULE_DIR))

        # installation base de données
        gn_db.session.execute(
            open(str(MODULE_DIR / "data/exports.sql"), "r").read()
        )
        gn_db.session.commit()

        # Création repertoires
        # TODO use config
        Path(BACKEND_DIR / "static/exports/usr_generated").mkdir(
            parents=True, exist_ok=True
        )
        Path(ROOT_DIR / "var/log/gn_export").mkdir(
            parents=True, exist_ok=True
        )

        # Création un lien symbolique pour les exports web
        # TODO use config
        os.symlink(
            str(BACKEND_DIR / "static/exports/usr_generated"),
            str(Path(ROOT_DIR / "frontend/dist/dataexport"))
        )

        # Création script cron
        write_in_cron_tab()


def write_in_cron_tab():
    """
        Fonction qui écrit dans le cron tab la commande
            nocture de réalisation des exports
    """
    print(" ...Création tache cron")

    cron_cmd = "{}/gn_export_cron.sh {}".format(
        str(MODULE_DIR), str(ROOT_DIR)
    )
    cron_cmt = "gn_export cron job"

    cron = CronTab(user=True)

    # Test si le job exist alors suppression
    cron.remove_all(comment=cron_cmt)

    # Création nouveau job
    job = cron.new(command=cron_cmd, comment=cron_cmt)
    # Configuration de la planification => @daily
    job.every().dom()

    # Ecriture dans cron tab
    cron.write()


def test_mail_config(gn_app):
    """
        Fonction qui test si l'envoie de mail est
        possible et correctement configuré lors de l'installation du module
    """
    if gn_app.config['MAIL_CONFIG']:
        print(" ...Test mail configuration")
        send_mail(
            [gn_app.config['MAIL_CONFIG']['MAIL_USERNAME']],
            "[GeoNature][Export]Installation module export",
            "Si vous avez reçu ce mail c'est que les paramètres de configuration des mails sont corrects et que le module est en cours d'installation"  # noqa: E501
        )
    else:
        raise GNModuleInstallError("Mail config is mandatory")
