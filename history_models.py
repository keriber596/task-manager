import datetime

import sqlalchemy as _sql

from database import Base


class UserHistory(Base):
    __tablename__ = 'user_history'
    id = _sql.Column(_sql.Integer, primary_key=True)
    user_id = _sql.Column(_sql.Integer)
    email = _sql.Column(_sql.String)
    username = _sql.Column(_sql.String)
    role = _sql.Column(_sql.String, default='')
    password = _sql.Column(_sql.String, default='')
    access = _sql.Column(_sql.String, default='in_process')
    recruiter_id = _sql.Column(_sql.Integer, default=0)
    mentor_id = _sql.Column(_sql.Integer, default=0)
    payment_type = _sql.Column(_sql.String, default='')
    payment_details = _sql.Column(_sql.String, default='')
    document_link = _sql.Column(_sql.String, default='')
    real_name = _sql.Column(_sql.String, default='')
    worker_rate = _sql.Column(_sql.Integer, default=0)
    balance = _sql.Column(_sql.Float, default=0)
    change_time = _sql.Column(_sql.DateTime, default=datetime.datetime.now())


class ReferralCodeHistory(Base):
    __tablename__ = 'referral_code_history'
    id = _sql.Column(_sql.Integer, primary_key=True)
    referral_code_id = _sql.Column(_sql.Integer)
    username_id = _sql.Column(_sql.Integer)
    code = _sql.Column(_sql.String, default='')
    change_time = _sql.Column(_sql.DateTime, default=datetime.datetime.now())


class JoinCodeHistory(Base):
    __tablename__ = 'join_code_history'
    id = _sql.Column(_sql.Integer, primary_key=True)
    username_id = _sql.Column(_sql.Integer)
    code = _sql.Column(_sql.String, default='')
    change_time = _sql.Column(_sql.DateTime, default=datetime.datetime.now())


class ClientInWorkHistory(Base):
    __tablename__ = 'client_in_work_history'
    id = _sql.Column(_sql.Integer, primary_key=True)
    client_id = _sql.Column(_sql.Integer)
    start_time = _sql.Column(_sql.DateTime, default=datetime.datetime.now())
    worker_id = _sql.Column(_sql.Integer)
    manager_id = _sql.Column(_sql.Integer)
    name = _sql.Column(_sql.String, default='')
    phone_number = _sql.Column(_sql.String, default='')
    city = _sql.Column(_sql.String, default='')
    call = _sql.Column(_sql.String, default='')
    from_who = _sql.Column(_sql.String, default='')
    link = _sql.Column(_sql.String, default='')
    status = _sql.Column(_sql.String, default='in_process')
    comment = _sql.Column(_sql.String, default='')
    change_time = _sql.Column(_sql.DateTime, default=datetime.datetime.now())


class TicketChatHistory(Base):
    __tablename__ = 'ticket_chat_history'
    id = _sql.Column(_sql.Integer, primary_key=True)
    ticket_id = _sql.Column(_sql.Integer)
    token = _sql.Column(_sql.String, default='')
    user_id = _sql.Column(_sql.Integer)
    mentor_id = _sql.Column(_sql.Integer)
    closed = _sql.Column(_sql.Boolean, default=False)
    change_time = _sql.Column(_sql.DateTime, default=datetime.datetime.now())


class PaymentCheckHistory(Base):
    __tablename__ = 'payment_check_history'
    id = _sql.Column(_sql.Integer, primary_key=True)
    payment_id = _sql.Column(_sql.Integer)
    username_id = _sql.Column(_sql.Integer, _sql.ForeignKey('user.id'))
    payment_type = _sql.Column(_sql.String, default='')
    payment_details = _sql.Column(_sql.String, default='')
    value = _sql.Column(_sql.Float, default=0)
    state = _sql.Column(_sql.String, default='')


class TaskHistory(Base):
    __tablename__ = 'task_hisory'
    id = _sql.Column(_sql.Integer, primary_key=True)
    task_id = _sql.Column(_sql.Integer)
    aim = _sql.Column(_sql.String, default='')
    award = _sql.Column(_sql.Float, default=0)
    mentor_id = _sql.Column(_sql.Integer, _sql.ForeignKey('user.id'))
    username = _sql.Column(_sql.String, default='')


class MissionHistory(Base):
    __tablename__ = 'mission'
    id = _sql.Column(_sql.Integer, primary_key=True)
    name = _sql.Column(_sql.String, default='')
    mentor_id = _sql.Column(_sql.Integer, _sql.ForeignKey('user.id'))
    aim = _sql.Column(_sql.Integer, default=0)
    award = _sql.Column(_sql.Integer, default=0)
    category = _sql.Column(_sql.String, default='')  # worker, manager, one_user
    username = _sql.Column(_sql.String, default='')
    info = _sql.Column(_sql.String, default=0)
