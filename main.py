from ui.main_ui import AuthenticationWindow, PhoneBookWindow
import sys
import locale
from auth import remember_me_auth

from utils import set_db_session, app


if sys.platform == 'win32':
    locale.setlocale(locale.LC_ALL, 'rus_rus')
else:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

session = set_db_session()

rm_auth_res = remember_me_auth(session)

if rm_auth_res:
    application = PhoneBookWindow(rm_auth_res)
else:
    application = AuthenticationWindow()

application.show()

sys.exit(app.exec())
