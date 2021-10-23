import datetime
from utils import app, check_email, check_phone
from ui.designer.authentication_window_des import Ui_AuthDialog
from ui.designer.create_contact_dialog_des import Ui_CreateContactDialog
from ui.designer.pass_reset_window_des import Ui_pswdResetDialog
from ui.designer.phone_book_window_des import Ui_PhoneBook
from ui.designer.registration_window_des import Ui_RegistrationQDialog
from auth import authentication, get_user_by_username, add_user, reset_passwords_request, reset_password, \
      remember_me, forget_me, User

from PyQt5 import QtCore
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView
from PyQt5 import QtWidgets
from phone_book import add_contact, delete_contact, update_contact, Contact, week_birthdays


from ui.designer.update_contact_dialog_des import Ui_UpdateContactDialog
from utils import session
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction


class AuthenticationWindow(QtWidgets.QDialog):

    def __init__(self):
        super(AuthenticationWindow, self).__init__()

        self.ui = Ui_AuthDialog()
        self.ui.setupUi(self)

        self.ui.notifyLabel.setText('')
        self.ui.regButton.clicked.connect(self.on_regButton_click)
        self.ui.enterButton.clicked.connect(self.on_enterButton_click)
        self.ui.cancelButton.clicked.connect(lambda: self.close())
        self.ui.forgetPassButton.clicked.connect(self.on_forgetPassButton_click)

        self.ui.showPassCheckBox.stateChanged.connect(self.on_showPassCheckBox_click)

    def on_showPassCheckBox_click(self):
        checked = self.ui.showPassCheckBox.isChecked()
        if checked:
            self.ui.Password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
        else:
            self.ui.Password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

    def on_forgetPassButton_click(self):
        self.forget = PassResetWindow()
        self.forget.show()
        self.close()

    def on_regButton_click(self):
        self.reg = RegistrationWindow()
        self.reg.show()
        self.close()

    def on_enterButton_click(self):
        username = self.ui.Username.text()
        password = self.ui.Password.text()
        if not (username and password):
            self.ui.notifyLabel.setText("Пожалуйста, заполните все поля")
            return
        auth = authentication(session=session, username=username, password=password)
        if auth:
            checked = self.ui.rememberMecheckBox.isChecked()
            if checked:
                user = get_user_by_username(session, username)
                remember_me(user_id=user.id, session=session)
            else:
                forget_me(session)
            self.pb = PhoneBookWindow(get_user_by_username(session, username).id)
            self.pb.show()
            self.close()

        else:
            self.ui.notifyLabel.setText("Пользователь с такими данными не найден")


class RegistrationWindow(QtWidgets.QDialog):
    def __init__(self):
        super(RegistrationWindow, self).__init__()
        self.ui = Ui_RegistrationQDialog()
        self.ui.setupUi(self)

        self.ui.notifyLabel.setText('')

        self.ui.okButton.clicked.connect(self.on_okButton_click)
        self.ui.cancelButton.clicked.connect(self.on_cancelButton_click)


    def on_cancelButton_click(self):
        self.au = AuthenticationWindow()
        self.au.show()
        self.close()

    def on_okButton_click(self):
        username = self.ui.Username.text()
        password = self.ui.Password.text()
        password_confirm = self.ui.PasswordConfirm.text()
        email = self.ui.Email.text()

        if not (username and password and email):
            self.ui.notifyLabel.setText("Пожалуйста, заполните все поля")
            return
        if password != password_confirm:
            self.ui.notifyLabel.setText("Пароли не совпадают")
            return
        if not check_email(email):
            self.ui.notifyLabel.setText("Неправильный формат email")
            return
        for user in session.query(User).all():
            if user.email == email:
                self.ui.notifyLabel.setText("Email занят")
                return

        add_user(session, username, password, email)
        self.au = AuthenticationWindow()
        self.au.show()
        self.close()


class PhoneBookWindow(QtWidgets.QMainWindow):

    def __init__(self, user_id):
        super(PhoneBookWindow, self).__init__()
        self.user = session.query(User).get(user_id)
        self.current_tab = 'Все'
        self.current_contacts = []
        self.ui = Ui_PhoneBook()
        self.ui.setupUi(self)
        self.tray = Tray(user_id)
        self.tray.show_birthdays()
        self.ui.notifyLabel.clear()

        self.ui.usernameLabel.setText(f'Вы зашли как {self.user.username}')
        self.ui.tableWidget.setColumnCount(3)

        self.ui.tableWidget.setHorizontalHeaderLabels(
            ('Имя', 'Телефон', 'Дата рождения')
        )
        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        stylesheet = "::section{Background-color:rgb(195, 195, 195)}"
        header.setStyleSheet(stylesheet)
        self.fill_TableWidget(self.current_tab)

        # select only 1 row
        self.ui.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.tabsTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tabsTableWidget.setSelectionMode(QAbstractItemView.SingleSelection)

        # tabsTableWidget config
        tabs_letters = ['Все', 'аб', 'вг', 'де', 'жзий', 'кл', 'мн', 'оп', 'рс', 'ту', 'фх', 'цчшщ', 'ъыьэ', 'юя']
        self.ui.tabsTableWidget.horizontalHeader().hide()
        self.ui.tabsTableWidget.setColumnCount(1)
        self.ui.tabsTableWidget.setRowCount(len(tabs_letters))
        row = 0
        for tab in tabs_letters:
            if tab == 'Все':
                cellinfo = QTableWidgetItem(tab)
            else:
                cellinfo = QTableWidgetItem(tab.upper())
            cellinfo.setFlags(
                QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
            )
            self.ui.tabsTableWidget.setItem(0, row, cellinfo)
            row += 1

        self.ui.tabsTableWidget.currentCellChanged.connect(self.tab_was_changed)
        self.ui.createPushButton.clicked.connect(self.ui_create_contact)
        self.ui.deletePushButton.clicked.connect(self.ui_delete_contact)
        self.ui.updatePushButton.clicked.connect(self.ui_update_contact)
        self.ui.logoutPushButton.clicked.connect(self.ui_logout)
        self.contactWindow = CreateContactWindow(self.user)

    def ui_logout(self):
        forget_me(session)
        self.au = AuthenticationWindow()
        self.au.show()
        self.tray.hide()
        self.close()

    def ui_delete_contact(self):
        currentRow = self.ui.tableWidget.currentRow()
        selectedIndexes = self.ui.tableWidget.selectedIndexes()
        if not selectedIndexes:
            self.ui.notifyLabel.setText("Пожалуйста, выделите контакт для удаления")
            return
        contact_to_delete = self.current_contacts[currentRow]
        delete_contact(contact_to_delete.id, session)
        self.fill_TableWidget(self.current_tab)

    def ui_update_contact(self):
        currentRow = self.ui.tableWidget.currentRow()
        selectedIndexes = self.ui.tableWidget.selectedIndexes()
        if not selectedIndexes:
            self.ui.notifyLabel.setText("Пожалуйста, выделите контакт для редактирования")
            return
        contact_to_update = self.current_contacts[currentRow]

        self.updateContactWindow = UpdateContactWindow(contact_to_update)
        self.updateContactWindow.window_closed.connect(self.fill_TableWidget_db)
        self.updateContactWindow.displayInfo()

    def ui_create_contact(self):
        self.contactWindow.window_closed.connect(self.fill_TableWidget_db)
        self.contactWindow.tray = self.tray
        self.contactWindow.displayInfo()

    def tab_was_changed(self):
        item = self.ui.tabsTableWidget.currentItem()
        self.current_tab = item.text()
        self.fill_TableWidget(self.current_tab)

    def fill_TableWidget_db(self):
        if self.current_tab == 'Все':
            # self.current_contacts = self.user.contacts.all()
            self.current_contacts = session.query(Contact).filter(Contact.user_id == self.user.id).all()
        else:
            self.current_contacts = self.get_tab_contacts_db(self.current_tab)

        self.ui.tableWidget.setRowCount(len(self.current_contacts))

        def contact_to_tuple(contact):
            birth_date = contact.birth_date.strftime("%d %B %Y")
            return contact.name, contact.phone, birth_date

        tuples = list(map(contact_to_tuple, self.current_contacts))

        # fill tableWidget
        row = 0
        for tup in tuples:
            col = 0

            for item in tup:
                cellinfo = QTableWidgetItem(item)
                cellinfo.setFlags(
                    QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
                )
                self.ui.tableWidget.setItem(row, col, cellinfo)
                col += 1

            row += 1

    def get_tab_contacts_db(self, tab):
        contacts_list = []
        user_contacts = session.query(Contact).filter(Contact.user_id == self.user.id).all()
        get_contacts_by_letter = lambda l: user_contacts.filter(Contact.name.startswith(l)).all()
        for l in tab: contacts_list += get_contacts_by_letter(l)
        return contacts_list

    def fill_TableWidget(self, tab):
        self.ui.notifyLabel.clear()
        if self.current_tab == 'Все':
            self.current_contacts = self.user.contacts.all()
        else:
            self.current_contacts = self.get_tab_contacts(tab)

        self.ui.tableWidget.setRowCount(len(self.current_contacts))

        def contact_to_tuple(contact):
            birth_date = contact.birth_date.strftime("%d %B %Y")
            return contact.name, contact.phone, birth_date

        tuples = list(map(contact_to_tuple, self.current_contacts))

        # fill tableWidget
        row = 0
        for tup in tuples:
            col = 0

            for item in tup:
                cellinfo = QTableWidgetItem(item)
                cellinfo.setFlags(
                    QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
                )
                self.ui.tableWidget.setItem(row, col, cellinfo)
                col += 1

            row += 1

    def get_tab_contacts(self, tab):
        contacts_list = []
        get_contacts_by_letter = lambda l: self.user.contacts.filter(Contact.name.startswith(l)).all()
        for l in tab: contacts_list += get_contacts_by_letter(l)
        return contacts_list


class CreateContactWindow(QtWidgets.QDialog):
    window_closed = pyqtSignal()

    def __init__(self, user):
        super(CreateContactWindow, self).__init__()
        self.ui = Ui_CreateContactDialog()
        self.ui.setupUi(self)

        self.ui.notifyLabel.setText('')

        self.user = user
        self.ui.cancelButton.clicked.connect(lambda: self.close())
        self.ui.okButton.clicked.connect(self.on_enterButton_click)

    def closeEvent(self, event):
        self.window_closed.emit()
        event.accept()

    def displayInfo(self):
        self.ui.notifyLabel.clear()
        self.show()

    def on_enterButton_click(self):
        name = self.ui.name.text()
        phone = self.ui.phone.text()
        birth_date = self.ui.birthDate.date().toPyDate()
        user_id = self.user.id

        if not (name and phone and birth_date):
            self.ui.notifyLabel.setText("Пожалуйста, заполните все поля")
            return
        if not check_phone(phone):
            self.ui.notifyLabel.setText("Неправильный формат телефона")
            return
        if session.query(Contact).filter(
                Contact.user_id == user_id,
                Contact.name == name,
                Contact.phone == phone,
                Contact.birth_date == birth_date
        ).first():
            self.ui.notifyLabel.setText("Такой контакт уже существует")
            return

        add_contact(session, user_id, name, phone, birth_date)
        self.tray.showMessage('Контакт добавлен:', name)
        self.close()


class UpdateContactWindow(QtWidgets.QDialog):
    window_closed = pyqtSignal()

    def __init__(self, contact):
        super(UpdateContactWindow, self).__init__()
        self.ui = Ui_UpdateContactDialog()
        self.ui.setupUi(self)

        self.ui.notifyLabel.setText('')

        self.contact = contact
        self.ui.name.setText(contact.name)
        self.ui.phone.setText(contact.phone)
        self.ui.birthDate.setDate(contact.birth_date)
        self.ui.cancelButton.clicked.connect(lambda: self.close())
        self.ui.okButton.clicked.connect(self.on_enterButton_click)

    def closeEvent(self, event):
        self.window_closed.emit()
        event.accept()

    def displayInfo(self):
        self.ui.notifyLabel.clear()
        self.show()

    def on_enterButton_click(self):
        name = self.ui.name.text()
        phone = self.ui.phone.text()
        birth_date = self.ui.birthDate.date().toPyDate()

        if not (name and phone and birth_date):
            self.ui.notifyLabel.setText("Пожалуйста, заполните все поля")
            return

        update_contact(id=self.contact.id, session=session, name=name, phone=phone, birth_date=birth_date)
        self.close()


class PassResetWindow(QtWidgets.QDialog):

    def __init__(self):
        super(PassResetWindow, self).__init__()
        self.ui = Ui_pswdResetDialog()
        self.ui.setupUi(self)

        self.ui.stackedWidget.setCurrentWidget(self.ui.requestPass)

        self.ui.requestNotifyLabel.setText('')

        self.ui.sendCode.clicked.connect(self.on_send_code)
        self.ui.okButton.clicked.connect(self.on_confirm_pass)
        self.ui.requestCancelButton.clicked.connect(self.onRequestCancelButton)
        self.ui.confirmCancelButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.requestPass))
        self.tray = Tray()

    def onRequestCancelButton(self):
        self.au = AuthenticationWindow()
        self.au.show()
        self.close()

    def on_send_code(self):
        email = self.ui.Email.text()
        if not check_email(email):
            self.ui.requestNotifyLabel.setText("Неправильный формат email")
            return

        rp = reset_passwords_request(email, session)
        if rp is False:
            self.ui.requestNotifyLabel.setText('Пользователь с таким email не найден')
            return
        self.tray.showMessage('Восстановление пароля', f'На почту {email} отправлен код')
        self.ui.stackedWidget.setCurrentWidget(self.ui.confirmPass)
        self.ui.requestNotifyLabel.setText("")

    def on_confirm_pass(self):
        code = self.ui.Code.text()
        password = self.ui.Password.text()
        password_confirm = self.ui.PasswordConfirm.text()

        if not (code and password and password_confirm):
            self.ui.confirmNotifyLabel.setText("Пожалуйста, заполните все поля")
            return

        if password != password_confirm:
            self.ui.confirmNotifyLabel.setText("Пароли не совпадают")
            return
        if reset_password(code, password, session):
            self.au = AuthenticationWindow()
            self.au.show()
            self.close()
        else:
            self.ui.confirmNotifyLabel.setText("Код не валиден")


class Tray(QSystemTrayIcon):
    def __init__(self, user_id=None):
        super(Tray, self).__init__()
        icon = QIcon("icon.png")
        self.setIcon(icon)
        self.setVisible(True)

        if user_id:
            self.user = session.query(User).get(user_id)

    def show_birthdays(self):
        week_birthdays_list_str = ""
        cur_date = datetime.date.today()
        birthdays = week_birthdays(session, self.user.id)
        if not birthdays:
            return
        for contact in birthdays:
            date_str = "{1} {0}\n".format(contact.name,
                                          contact.birth_date.replace(year=cur_date.year).strftime("%d/%m %A"))
            week_birthdays_list_str += date_str
        self.showMessage('Дни рождения на этой неделе:', week_birthdays_list_str, QSystemTrayIcon.Information, 15000)

    def show_message(self, subject, message, message_time=3000):
        self.showMessage(subject, message, QSystemTrayIcon.Information, message_time)
