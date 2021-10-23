import os
import smtplib, ssl
from PyQt5 import QtWidgets
import sqlalchemy
from sqlalchemy.orm import declarative_base
import re

from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


def set_db_session():
    user = os.environ["DATABASE_USER"]
    database_name = os.environ["DATABASE_NAME"]
    password = os.environ["DATABASE_PASSWORD"]
    host = os.environ["DATABASE_HOST"]
    port = os.environ["DATABASE_PORT"]
    engine = sqlalchemy.create_engine(
        "mariadb+mariadbconnector://{0}:{1}@{2}:{3}/{4}".format(
            user,
            password,
            host,
            port,
            database_name
        ))
    Base.metadata.create_all(engine)

    # Create a session
    Session = sqlalchemy.orm.sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    return session


session = set_db_session()


def send_email(subject, message, receiver_email):
    port = os.environ["EMAIL_PORT"]
    smtp_server = os.environ["EMAIL_HOST"]
    sender_email = os.environ["EMAIL_HOST_USER"]
    password = os.environ["EMAIL_HOST_PASSWORD"]
    context = ssl.create_default_context()

    mail = f"""\
   Subject: {subject}
   To: {receiver_email}
   From: phone book app
    
   {message}""".format(subject=subject, sender_email=sender_email, message=message, receiver_email=receiver_email)

    # print(mail)
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, mail.encode('utf-8'))
        print("send email on {email}".format(email=receiver_email))
    except:
        print("can't send email on {email}".format(email=receiver_email))


def check_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.fullmatch(regex, email):
        return True
    else:
        return False


def check_phone(phone):
    regex = r'^\s*(?:\+?(\d{1,3}))?([-. (]*(\d{3})[-. )]*)?((\d{3})[-. ]*(\d{2,4})(?:[-.x ]*(\d+))?)\s*$'
    if re.match(regex, phone):
        return True
    else:
        return False


app = QtWidgets.QApplication([])
