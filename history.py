import sqlalchemy.orm as _orm

import models


def add_user_history(user: models.User, model_name: str, db: _orm.Session):
    user_record = models.UserHistory()
    for attr, value in user.__dict__.items():
        setattr(user_record, attr, value)
    setattr(user_record, f'{model_name}_id', user.id)
    db.add(user_record)
    db.commit()
    db.refresh(user_record)


def add_referral_history(referral: models.ReferralCode, model_name: str, db: _orm.Session):
    user_record = models.ReferralCodeHistory()
    for attr, value in referral.__dict__.items():
        setattr(user_record, attr, value)
    setattr(user_record, f'{model_name}_id', referral.id)
    db.add(user_record)
    db.commit()
    db.refresh(user_record)


def add_join_history(join_code: models.JoinCode, model_name: str, db: _orm.Session):
    user_record = models.ReferralCodeHistory()
    for attr, value in join_code.__dict__.items():
        setattr(user_record, attr, value)
    setattr(user_record, f'{model_name}_id', join_code.id)
    db.add(user_record)
    db.commit()
    db.refresh(user_record)


def add_client_history(client: models.ClientInWork, model_name: str, db: _orm.Session):
    user_record = models.ReferralCodeHistory()
    for attr, value in client.__dict__.items():
        setattr(user_record, attr, value)
    setattr(user_record, f'{model_name}_id', client.id)
    db.add(user_record)
    db.commit()
    db.refresh(user_record)


def add_ticket_history(ticket: models.TicketChat, model_name: str, db: _orm.Session):
    user_record = models.ReferralCodeHistory()
    for attr, value in ticket.__dict__.items():
        setattr(user_record, attr, value)
    setattr(user_record, f'{model_name}_id', ticket.id)
    db.add(user_record)
    db.commit()
    db.refresh(user_record)


def add_payment_history(payment: models.PaymentCheck, model_name: str, db: _orm.Session):
    user_record = models.ReferralCodeHistory()
    for attr, value in payment.__dict__.items():
        setattr(user_record, attr, value)
    setattr(user_record, f'{model_name}_id', payment.id)
    db.add(user_record)
    db.commit()
    db.refresh(user_record)
