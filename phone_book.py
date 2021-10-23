import datetime
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import sqlalchemy
from utils import Base


class Contact(Base):
    __tablename__ = 'contacts'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(length=200), nullable=False)
    phone = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False)
    birth_date = sqlalchemy.Column(sqlalchemy.Date(), nullable=False)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="contacts")

    __table_args__ = (UniqueConstraint('user_id', 'name', 'phone', 'birth_date', name='contacts_uc'),)

    def __repr__(self):
        return "<Contact(name='%s', phone='%s', birth_date='%s')>" % (self.name, self.phone, self.birth_date)


def week_birthdays(session, user_id):
    cur_date = datetime.date.today()
    start_of_week = cur_date - datetime.timedelta(days=cur_date.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    week_birthdays = []
    contacts = session.query(Contact).filter(Contact.user_id == user_id).all()
    for contact in contacts:
        birth_date_this_week = start_of_week <= contact.birth_date.replace(year=cur_date.year) <= end_of_week
        if birth_date_this_week:
            week_birthdays.append(contact)
    week_birthdays.sort(key=lambda x: x.birth_date.replace(year=cur_date.year), reverse=False)
    return week_birthdays


def add_contact(session, user_id, name, phone, birth_date):
    new_contact = Contact(
        user_id=user_id,
        name=name,
        phone=phone,
        birth_date=birth_date
    )

    if session.query(Contact).filter(
            Contact.user_id == user_id,
            Contact.name == name,
            Contact.phone == phone,
            Contact.birth_date == birth_date
    ).first():
        print('such contact already exists')
        return
    else:
        session.add(new_contact)
        session.commit()


def delete_contact(contact_id, session):
    contact = session.query(Contact).get(contact_id)
    session.delete(contact)
    session.commit()


def update_contact(id, session, **kwargs):
    contact = session.query(Contact).get(id)
    for key, value in kwargs.items():
        setattr(contact, key, value)
    session.commit()
