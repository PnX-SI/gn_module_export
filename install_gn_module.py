import sys
import subprocess
from pathlib import Path


from geonature.utils.utilsmails import send_mail
from geonature.utils.errors import GNModuleInstallError
from geonature.utils.env import BACKEND_DIR

ROOT_DIR = Path(__file__).absolute().parent


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
            raise GNModuleInstallError("Mail config is not correct please read the doc")

        # here = Path(__file__).parent
        requirements_path = ROOT_DIR / 'backend' / 'requirements.txt'
        assert requirements_path.is_file()
        subprocess.call(
            [sys.executable, '-m', 'pip', 'install', '-r', '{}'.format(requirements_path)],  # noqa: E501
            cwd=str(ROOT_DIR))

        # installation base de données
        gn_db.session.execute(
            open(str(ROOT_DIR / "data/exports.sql"), "r").read()
        )
        gn_db.session.commit()

        # Création repertoires
        Path(BACKEND_DIR / "static/exports").mkdir(
            parents=True, exist_ok=True
        )


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
            "Si vous avez reçu ce mail c'est que les paramètres de configuration des mails sont corrects et que le module est en cours d'installation"
        )
    else:
        raise GNModuleInstallError("Mail config is mandatory")
