import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).absolute().parent


def gnmodule_install_app(gn_db, gn_app):
    '''
        Fonction principale permettant de réaliser les opérations
        d'installation du module :
            - Base de données
            - Module (pour le moment rien)
    '''
    with gn_app.app_context():
        here = Path(__file__).parent
        requirements_path = here / 'backend' / 'requirements.txt'
        assert requirements_path.is_file()
        subprocess.call(
            [sys.executable, '-m', 'pip', 'install', '-r', '{}'.format(requirements_path)],  # noqa: E501
            cwd=str(ROOT_DIR))
        subprocess.call(['./install_db.sh'], cwd=str(ROOT_DIR))
