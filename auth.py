import datetime
import random
import string
from sqlalchemy import Column, DateTime, UniqueConstraint, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, expression
import sqlalchemy
import hashlib
import os
from utils import send_email, Base


class EmailVerification(Base):
    __tablename__ = 'email_verification_codes'
    code = sqlalchemy.Column(sqlalchemy.String(length=20), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    email = sqlalchemy.Column(sqlalchemy.String(length=100))
    is_verified = sqlalchemy.Column(sqlalchemy.Boolean, server_default=expression.false(), nullable=False)


class RememberMe(Base):
    __tablename__ = 'remember_last_user'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, default=1)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="remember_me")
    hashed_password = sqlalchemy.Column(sqlalchemy.LargeBinary(), nullable=False)
    updated_dt = Column(DateTime, default=datetime.datetime.now(),
                        nullable=False, onupdate=datetime.datetime.now())
    __table_args__ = (CheckConstraint(id == 1),)

    def __repr__(self):
        return "User '%s' is remembered" % self.user.username


class User(Base):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    username = sqlalchemy.Column(sqlalchemy.String(length=200), nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.LargeBinary())
    salt = sqlalchemy.Column(sqlalchemy.LargeBinary())
    email = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False, unique=True)

    contacts = relationship("Contact", back_populates="user", cascade="all, delete", lazy='dynamic')

    remember_me = relationship("RememberMe", back_populates="user", uselist=False, cascade="all, delete")

    __table_args__ = (UniqueConstraint('username', 'email', name='users_uc'),)

    def __repr__(self):
        return "<User(username='%s', email='%s')>" % (self.username, self.email)


def add_user(session, username, password, email):
    new_user = User(username=username, email=email)
    session.add(new_user)
    session.commit()
    set_password(new_user, password, session)


def set_password(user, plain_password, session):
    password_hashing_res = password_hashing(plain_password)
    hashed_password = password_hashing_res["hashed_password"]
    salt = password_hashing_res["salt"]
    user.hashed_password = hashed_password
    user.salt = salt
    session.commit()


def password_hashing(plain_password):
    salt = os.urandom(32)
    hashed_password = hashlib.pbkdf2_hmac(
        'sha256',
        plain_password.encode('utf-8'),
        salt,
        100000
    )
    return {"hashed_password": hashed_password, "salt": salt}


def verify_password(plainPasswordToCheck, hashed_password, salt):
    hashed_password_to_check = hashlib.pbkdf2_hmac(
        'sha256',
        plainPasswordToCheck.encode('utf-8'),
        salt,
        100000)

    if hashed_password_to_check == hashed_password:
        print('Password is correct')
        return True
    else:
        print('Password is incorrect')
        return False


def get_user_by_username(session, username):
    user = session.query(User).filter_by(username=username).first()
    if user:
        return user
    else:
        print("user {username} not exists".format(username=username))
        return None


def remember_me_auth(session):
    remember_me_instance = session.query(RememberMe).first()
    if remember_me_instance:
        user = remember_me_instance.user
        pass_to_check = remember_me_instance.hashed_password
        if user.hashed_password == pass_to_check:
            return user.id
        else:
            print('remembered pass does not valid')
            return False
    else:
        print('no memorized users')
        return False


def authentication(session, username, password):
    user = get_user_by_username(session, username)

    if user:
        verify_password_res = verify_password(
            plainPasswordToCheck=password,
            hashed_password=user.hashed_password,
            salt=user.salt)

        return verify_password_res
    else:
        return False


def reset_passwords_request(email, session):
    user = session.query(User).filter_by(email=email).first()
    if not user:
        print('Пользователь с таким email не найден в базе')
        return False
    code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    message = 'Здравствуйте, {username}. Ваш код для замены пароля - {code}'.format(code=code, username=user.username)
    subject = 'Смена пароля'

    send_email(receiver_email=email, subject=subject, message=message)

    new_code = EmailVerification(code=code, email=email)
    session.add(new_code)
    session.commit()
    return True


def reset_password(code, new_password, session):
    email_verif = session.query(EmailVerification).get(code)
    if not email_verif:
        print('Code {code} not found in db'.format(code=code))
        return False
    if not email_verif.is_verified:
        user = session.query(User).filter_by(email=email_verif.email).first()
        set_password(user, new_password, session)
        email_verif.is_verified = expression.true()
        session.commit()
        print('set new password for {username}'.format(username=user.username))
        return True
    else:
        print('Code {code} already used'.format(code=code))
        return False


def remember_me(session, user_id):
    remember_me_instance = session.query(RememberMe).first()
    user_instance = session.query(User).get(user_id)
    username = user_instance.username
    hashed_password = user_instance.hashed_password
    if not remember_me_instance:
        session.add(RememberMe(user_id=user_id, hashed_password=hashed_password))
        session.commit()
    else:
        remember_me_instance.user_id = user_id
        remember_me_instance.hashed_password = hashed_password
        session.commit()
    print(f'{username} (id={user_id}) remembered')


def forget_me(session):
    remember_me_instance = session.query(RememberMe).first()
    if remember_me_instance:
        username = remember_me_instance.user.username
        session.delete(remember_me_instance)
        session.commit()
        print(f'forget {username}'.format(username=username))
