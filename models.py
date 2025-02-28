import datetime

import sqlalchemy as _sql
from passlib.context import CryptContext

from history_models import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = 'user'
    id = _sql.Column(_sql.Integer, primary_key=True)
    email = _sql.Column(_sql.String, unique=True)
    username = _sql.Column(_sql.String, unique=True)
    role = _sql.Column(_sql.String, default='')  # recruiter, worker, manager, future_worker, mentor, admin
    password = _sql.Column(_sql.String, default='')
    access = _sql.Column(_sql.String, default='in_process')  # approved, in_process, rejected
    recruiter_id = _sql.Column(_sql.Integer, default=0)
    mentor_id = _sql.Column(_sql.Integer,  default=0)
    manager_id = _sql.Column(_sql.Integer, default=0)
    payment_type = _sql.Column(_sql.String, default=' ')
    payment_details = _sql.Column(_sql.String, default=' ')
    document_link = _sql.Column(_sql.String, default=' ')
    phone_number = _sql.Column(_sql.String, default='-')
    real_name = _sql.Column(_sql.String, default=' ')
    avatar_link = _sql.Column(_sql.String, default=' ')
    worker_rate = _sql.Column(_sql.Integer, default=0)
    balance = _sql.Column(_sql.Float, default=0)

    def verify_password(self, password: str):
        return pwd_context.verify(password, self.password)


class ReferralCode(Base):
    __tablename__ = 'referral_code'
    id = _sql.Column(_sql.Integer, primary_key=True)
    username_id = _sql.Column(_sql.Integer)
    code = _sql.Column(_sql.String, default='')


class JoinCode(Base):
    __tablename__ = 'join_code'
    id = _sql.Column(_sql.Integer, primary_key=True)
    username_id = _sql.Column(_sql.Integer)
    code = _sql.Column(_sql.String, default='')


class ClientInWork(Base):
    __tablename__ = 'client_in_work'
    id = _sql.Column(_sql.Integer, primary_key=True)
    start_time = _sql.Column(_sql.DateTime, default=datetime.datetime.now())
    worker_id = _sql.Column(_sql.Integer)
    manager_id = _sql.Column(_sql.Integer)
    name = _sql.Column(_sql.String, default='')
    phone_number = _sql.Column(_sql.String, default='')
    city = _sql.Column(_sql.String, default='')
    call = _sql.Column(_sql.String, default='')
    from_who = _sql.Column(_sql.String, default='')
    link = _sql.Column(_sql.String, default='')
    status = _sql.Column(_sql.String, default='in_process')  # accepted, in_process, rejected
    comment = _sql.Column(_sql.String, default='')
    deposit_date = _sql.Column(_sql.DateTime, default=datetime.datetime.now())
    deposit = _sql.Column(_sql.Boolean, default=False)
    checked_number = _sql.Column(_sql.Boolean, default=False)



class ChatMessage(Base):
    __tablename__ = 'chat_message'
    id = _sql.Column(_sql.Integer, primary_key=True)
    ticket_id = _sql.Column(_sql.Integer)
    datetime = _sql.Column(_sql.DateTime, default=datetime.datetime.now())
    message_text = _sql.Column(_sql.String, default='')
    user_id = _sql.Column(_sql.Integer)


class TicketChat(Base):
    __tablename__ = 'ticket_chat'
    id = _sql.Column(_sql.Integer, primary_key=True)
    token = _sql.Column(_sql.String, default='')
    user_id = _sql.Column(_sql.Integer)
    mentor_id = _sql.Column(_sql.Integer)
    closed = _sql.Column(_sql.Boolean, default=False)

"""
class Mission(Base):
    __tablename__ = 'mission'
    __table_args__ = {'extend_existing': True}
    id = _sql.Column(_sql.Integer, primary_key=True)
    name = _sql.Column(_sql.String, default='')
    mentor_id = _sql.Column(_sql.Integer, _sql.ForeignKey('user.id', name='user_id'))
    aim = _sql.Column(_sql.Integer, default=0)
    award = _sql.Column(_sql.Integer, default=0)
    category = _sql.Column(_sql.String, default='')  # worker, manager, one_user
    username = _sql.Column(_sql.String, default='')
    info = _sql.Column(_sql.String, default=0)


class MissionRequest(Base):
    __tablename__ = 'mission_request'
    id = _sql.Column(_sql.Integer, primary_key=True)
    mission_id = _sql.Column(_sql.Integer, _sql.ForeignKey('mission.id', name='mission_id'))
    user_id = _sql.Column(_sql.Integer, _sql.ForeignKey('user.id', name='user_id'))
    status = _sql.Column(_sql.String, default='in_process')  # accepted, in_process, rejected
    comment = _sql.Column(_sql.String, default='')
"""


class StudyMaterial(Base):
    __tablename__ = 'study_material'
    id = _sql.Column(_sql.Integer, primary_key=True)
    title = _sql.Column(_sql.String, default='')
    content = _sql.Column(_sql.Text, default='')


class Regulation(Base):
    __tablename__ = 'regulation'
    id = _sql.Column(_sql.Integer, primary_key=True)
    title = _sql.Column(_sql.String, default='')
    content = _sql.Column(_sql.Text, default='')


class PaymentCheck(Base):
    __tablename__ = 'payment_check'
    id = _sql.Column(_sql.Integer, primary_key=True)
    username_id = _sql.Column(_sql.Integer)
    payment_type = _sql.Column(_sql.String, default='')
    payment_details = _sql.Column(_sql.String, default='')
    value = _sql.Column(_sql.Float, default=0)
    state = _sql.Column(_sql.String, default='in_process')  # in_process, accepted, rejected


class Task(Base):
    __tablename__ = 'task'
    id = _sql.Column(_sql.Integer, primary_key=True)
    name = _sql.Column(_sql.String, default='')
    aim = _sql.Column(_sql.String, default='')
    award = _sql.Column(_sql.Float, default=0)
    mentor_id = _sql.Column(_sql.Integer)
    category = _sql.Column(_sql.String, default='')  # worker, manager, one_user
    username = _sql.Column(_sql.String, default='')
    date = _sql.Column(_sql.DateTime, default=datetime.datetime.now())


class TaskRequest(Base):
    __tablename__ = 'task_request'
    id = _sql.Column(_sql.Integer, primary_key=True)
    task_id = _sql.Column(_sql.Integer)
    user_id = _sql.Column(_sql.Integer)
    status = _sql.Column(_sql.String, default='in_process')  # active, refused, finished, approved, rejected
    comment = _sql.Column(_sql.String, default='')
    date = _sql.Column(_sql.DateTime, default=datetime.datetime.now())


class ClientReward(Base):
    __tablename__ = 'reward'
    id = _sql.Column(_sql.Integer, primary_key=True)
    number_reward = _sql.Column(_sql.Float, default=0)
    call_reward = _sql.Column(_sql.Float, default=0)
    deposit_reward_1 = _sql.Column(_sql.Float, default=0)
    deposit_reward_2 = _sql.Column(_sql.Float, default=0)
    deposit_reward_3 = _sql.Column(_sql.Float, default=0)
