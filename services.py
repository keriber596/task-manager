import datetime
import os
import random
import secrets

import dotenv as _dotenv
import email_validator
import fastapi
import fastapi.security as security
import jwt
import sqlalchemy.orm as _orm
from passlib.context import CryptContext
from sqlalchemy import exc
from conf import *
import database as _database
import schemas
from history import *

_dotenv.load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2schema = security.OAuth2PasswordBearer("/token")


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_id(id: int, db: _orm.Session):
    return db.query(models.User).filter(models.User.id == id).first()


def get_user_by_username(username: str, db: _orm.Session):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(email: str, db: _orm.Session):
    return db.query(models.User).filter(models.User.email == email).first()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def change_user_password(email: str, password: str, db: _orm.Session):
    user = get_user_by_email(email, db)
    user.password = get_password_hash(password)
    db.commit()


async def create_token(user: models.User):
    user_obj = schemas.User.from_orm(user)

    user_dict = user_obj.dict()

    token = jwt.encode(user_dict, os.environ['SECRET_KEY'], algorithm=os.environ['ALGORITHM'])

    return token


async def get_current_user(db: _orm.Session = fastapi.Depends(get_db),
                           token: str = fastapi.Depends(oauth2schema)):
    try:
        payload = jwt.decode(token, os.environ['SECRET_KEY'], algorithms=[os.environ['ALGORITHM']])
        user = db.query(models.User).get(payload['id'])

    except:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Неверные данные'})
    return schemas.User.from_orm(user)


async def authenticate_user(username: str, password: str, db: _orm.Session):
    user_username = get_user_by_username(username=username, db=db)
    user_email = get_user_by_email(username, db)
    if (not user_username) and (not user_email):
        return False
    try:
        if (not user_username.verify_password(password)) and (not user_email.verify_password(password)):
            return False
    except AttributeError:
        return False

    return user_email if user_email else user_username


async def create_user(file, user: schemas.UserCreate, ref_link: str, db: _orm.Session):
    try:
        valid = email_validator.validate_email(user.email)
    except:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Введите действительный email'})
    ref_link = db.query(models.ReferralCode).filter(models.ReferralCode.code == ref_link).all()
    join_code = db.query(models.JoinCode).filter(models.JoinCode.code == user.join_code).all()
    if ref_link != [] and join_code != []:
        recruiter = ref_link[0].username_id
        mentor_id = join_code[0].username_id
        user_obj = models.User(username=user.username, email=user.email, role=user.role,
                               document_link=f'{site_url}/api/staticfiles' + user.username + ".png",
                               recruiter_id=recruiter,
                               real_name=user.real_name,
                               password=get_password_hash(user.password), mentor_id=mentor_id,
                               phone_number=user.phone_number)
        try:
            db.add(user_obj)
            db.commit()
            db.refresh(user_obj)
            with open(f'/var/www/staticfiles/kyc/{user.username}.png', 'wb') as out_file:
                content = file.file.read()
                out_file.write(content)
                file.file.close()
            add_user_history(user_obj, 'user', db)
            return user_obj
        except exc.IntegrityError:
            db.rollback()
            raise fastapi.HTTPException(status_code=400, detail={'msg': 'Пользователь уже существует'})
    else:
        raise fastapi.HTTPException(status_code=400,
                                    detail={'msg': 'Реферальная ссылка или пригласительный код не существуют'})


async def add_mentor_code(username: int, db: _orm.Session):
    user = db.query(models.User).filter(models.User.username == username).first()
    join_code = models.JoinCode(username_id=user.id, code=str(random.randint(100000, 999999)))
    db.add(join_code)
    db.commit()
    db.refresh(join_code)


async def get_mentor_code(user: models.User, db: _orm.Session):
    join_code = db.query(models.JoinCode).filter(models.JoinCode.username_id == user.id).first()
    return join_code.code


async def get_worker_managers(user: models.User, db: _orm.Session):
    if user.manager_id == 0:
        return db.query(models.User).filter(models.User.role == 'manager').all()
    return [db.query(models.User).get(user.manager_id)]


async def change_user_field(user_id: int, fields: schemas.UserChangeField, db: _orm.Session):
    user = db.query(models.User).get(user_id)
    fields_list = ['real_name', 'username', 'email', 'payment_type', 'payment_details']
    for field in fields_list:
        if getattr(fields, field) is not None:
            setattr(user, field, getattr(fields, field))
    if (fields.new_password_1 is not None) and (fields.new_password_1 == fields.new_password_2):
        setattr(user, 'password', get_password_hash(fields.new_password_1))
    db.commit()
    add_user_history(user, 'user', db)


def add_avatar(file, user: models.User, db: _orm.Session):
    with open('/var/www/staticfiles/avatars/' + user.username + '.png', 'wb') as out_file:
        content = file.file.read()
        out_file.write(content)
        file.file.close()
    user_obj = db.query(models.User).get(user.id)
    user_obj.avatar_link = f'{site_url}/api/static' + user.username + '.png'
    db.commit()
    return {'msg': 'ok'}


def get_user_clients(user: models.User, db: _orm.Session):
    clients = db.query(models.ClientInWork).filter(models.ClientInWork.worker_id == user.id).all()
    managers = db.query(models.User).filter(models.User.role == 'manager').all()
    for i in range(len(clients)):
        manager_name = manager_username(managers, clients[i].manager_id)
        setattr(clients[i], 'manager_name', manager_name)
    return clients


def edit_client(client: schemas.ClientEdit, user: models.User, db: _orm.Session):
    if user.role == 'worker':
        client_model = db.query(models.ClientInWork).get(client.id)
        client_obj = client.__dict__
        for field in ['name', 'phone_number', 'city', 'start_time',
                      'from_who', 'call', 'link', 'manager_id', ]:
            if client_obj[field] is not None:
                setattr(client_model, field, client_obj[field])
        db.commit()


# client
def get_user_clients_complete(user: models.User, db: _orm.Session):
    tasks = db.query(models.ClientInWork).filter(models.ClientInWork.worker_id == user.id).filter(
        models.ClientInWork.status == 'approved').all()
    return tasks


async def get_manager_clients(user: models.User, db: _orm.Session):
    clients = db.query(models.ClientInWork).filter(models.ClientInWork.manager_id == user.id).all()
    clients.reverse()
    return clients


async def add_ref_link(username_id: int, db: _orm.Session):
    link = secrets.token_hex(4)
    referal = models.ReferralCode(code=link, username_id=username_id)
    db.add(referal)
    db.commit()
    db.refresh(referal)
    add_referral_history(referal, 'referral', db)
    return link


# client
async def get_tasks_top(db: _orm.Session):
    top = dict()
    tasks = db.query(models.ClientInWork).filter(models.ClientInWork.status == 'approved').all()
    all_users = set()
    unmarked_top = []
    for task in tasks:
        try:
            top[task.worker_id] += 1
        except KeyError:
            top[task.worker_id] = 1
        all_users.add(task.worker_id)
    for user in all_users:
        user_model = db.query(models.User).get(user)
        unmarked_top.append(
            {'username': user_model.username, 'closes': top[user_model.id], 'balance': user_model.balance})
    unmarked_top.sort(key=lambda x: x['closes'])
    unmarked_top.reverse()
    return unmarked_top


def get_user_state(user: models.User, db: _orm.Session):
    return db.query(models.User).filter(models.User.id == user.id).first().access


def get_regulation(db: _orm.Session):
    return db.query(models.Regulation).all()


def get_study_material(db: _orm.Session):
    return db.query(models.StudyMaterial).all()


async def add_client(client: schemas.ClientAdd, user: models.User, db: _orm.Session):
    new_client = models.ClientInWork(name=client.name, phone_number=client.phone_number,
                                     city=client.city, start_time=client.start_time,
                                     from_who=client.from_who, call=client.call,
                                     link=client.link, worker_id=user.id, manager_id=client.manager_id)
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    add_client_history(new_client, 'client', db)
    return {'msg': 'ok'}


async def add_client_comment(comment: schemas.ClientComment, db: _orm.Session):
    client = db.query(models.ClientInWork).filter(models.ClientInWork.id == comment.id).first()
    client.comment = comment.comment
    db.commit()
    add_client_history(client, 'client', db)
    return {'msg': 'ok'}


async def recruiter_team(user: models.User, db: _orm.Session):
    users = db.query(models.User).filter(models.User.recruiter_id == user.id).all()
    team = []
    for worker in users:
        closes = db.query(models.ClientInWork).filter(models.ClientInWork.worker_id == worker.id).filter(
            models.ClientInWork.status == 'approved').all()
        team.append({'username': worker.username, 'closes': len(closes), 'balance': worker.balance})
    return team


async def recruiter_team_info(user: models.User, db: _orm.Session):
    users = db.query(models.User).filter(models.User.recruiter_id == user.id).all()
    ref_link = db.query(models.ReferralCode).filter(models.ReferralCode.username_id == user.id).first()
    shared_balance, amount = 0, 0
    for worker in users:
        amount += 1
        shared_balance += worker.balance
    return {'balance': shared_balance, 'amount': amount, 'ref_link': ref_link.code}


async def get_manager_team(user: models.User, db: _orm.Session):
    users = db.query(models.User).filter(models.User.manager_id == user.id).all()
    team = []
    for worker in users:
        closes = db.query(models.ClientInWork).filter(models.ClientInWork.worker_id == worker.id).filter(
            models.ClientInWork.status == 'approved').all()
        team.append({'username': worker.username, 'closes': len(closes), 'balance': worker.balance})
    team.sort(key=lambda x: x['closes'])
    team.reverse()
    return team


def add_worker_manager(manager_add: schemas.AddManager, user: models.User, db: _orm.Session):
    if user.role == 'mentor':
        worker = db.query(models.User).get(manager_add.worker_id)
        worker.manager_id = manager_add.manager_id
        db.commit()
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Вы не можете закрепить менеджера'})


async def send_chat_message(ticket: int, text: str, user_id: int, db: _orm.Session):
    message = models.ChatMessage(ticket_id=ticket, datetime=datetime.datetime.now(), message_text=text, user_id=user_id)
    db.add(message)
    db.commit()
    db.refresh(message)
    return {'msg': 'ok'}


async def add_ticket(mentor: int, user: models.User, db: _orm.Session):
    ticket = models.TicketChat(mentor_id=mentor, user_id=user.id)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    add_ticket_history(ticket, 'ticket', db)
    return ticket.id


async def close_ticket(ticket: schemas.TicketClose, db: _orm.Session):
    ticket_obj = db.query(models.TicketChat).get(ticket.id)
    ticket_obj.closed = True
    db.commit()
    add_ticket_history(ticket_obj, 'ticket', db)
    return {'msg': 'ok'}


async def get_ticket_chat(ticket: int, db: _orm.Session):
    chat = db.query(models.ChatMessage).filter(models.ChatMessage.ticket_id == ticket).all()
    return chat


def add_payment_check(check: schemas.PaymentCheck, user: models.User, db: _orm.Session):
    check = models.PaymentCheck(username_id=user.id, payment_type=user.payment_type,
                                payment_details=user.payment_details,
                                value=check.value)
    db.add(check)
    db.commit()
    db.refresh(check)
    add_payment_history(check, 'payment', db)
    return {'msg': 'ok'}


async def get_payment_mentor(user: models.User, db: _orm.Session):
    if user.role == 'mentor':
        users = db.query(models.User).filter(models.User.mentor_id == user.id).all()
        payments = []
        for worker in users:
            payments_list = db.query(models.PaymentCheck).filter(models.PaymentCheck.username_id == worker.id).all()
            for i in range(len(payments_list)):
                setattr(payments_list[i], 'username', worker.username)
            payments += payments_list
        payments.sort(key=lambda x: x.id, reverse=True)
        return payments
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'у вас нет доступа к данным'})


def close_payment_mentor(payment: schemas.PaymentClose, user: models.User, db: _orm.Session):
    if user.role == 'mentor':
        check = db.query(models.PaymentCheck).get(payment.id)
        check.state = payment.state
        worker = db.query(models.User).get(check.username_id)
        if check.state == 'approved':
            worker.balance -= check.value
        db.commit()
        add_payment_history(check, 'payment', db)
        return {'msg': 'ok'}
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Вы не можете редактировать чеки'})


def accept_user(user_data: schemas.UserAccept, user: models.User, db: _orm.Session):
    worker_user = db.query(models.User).get(user_data.id)
    if user.role == 'mentor':
        if user_data.access == 'rejected':
            db.delete(worker_user)
            db.commit()
            return {'msg': "ok"}
        worker_user.access = user_data.access
        db.commit()
        add_user_history(worker_user, 'user', db)
        return {'msg': 'ok'}
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Вы не можете принимать пользователей'})


async def get_mentor_users(user: models.User, db: _orm.Session):
    users = db.query(models.User).filter(models.User.mentor_id == user.id).all()
    users.sort(key=lambda x:x.id)
    users.reverse()
    return users


async def get_mentor_ticket(user: models.User, db: _orm.Session):
    if user.role == 'mentor':
        tickets = db.query(models.TicketChat).filter(models.TicketChat.mentor_id == user.id).filter(
            models.TicketChat.closed == False).all()
        for i in range(len(tickets)):
            setattr(tickets[i], 'username', db.query(models.User).get(tickets[i].user_id).username)
        return tickets
    raise fastapi.HTTPException(status_code=400, detail={'msg': 'Нет доступа к данным'})


async def get_worker_ticket(user: models.User, db: _orm.Session):
    tickets = db.query(models.TicketChat).filter(models.TicketChat.user_id == user.id).filter(
        models.TicketChat.closed == False).all()
    return tickets


async def accept_manager_client(client: schemas.AcceptClient, user: models.User, db: _orm.Session):
    if user.role == 'manager':
        client_obj = db.query(models.ClientInWork).get(client.id)
        client_obj.status = client.status
        worker = db.query(models.User).get(client_obj.worker_id)
        if client.status == 'approved':
            reward = db.query(models.ClientReward).first()
            worker.balance += reward.number_reward
        db.commit()
        return {'msg': 'ok'}
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Вы не можете редактировать клиентов'})


async def add_mentor_task(task: schemas.MentorTask, user: models.User, db: _orm.Session):
    if user.role == 'mentor':
        new_task = models.Task(aim=task.aim, username=task.username, award=task.award, mentor_id=user.id,
                               category=task.category)
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Вы не можете добавлять клиентов'})


async def get_new_tasks(user: models.User, db: _orm.Session):
    tasks = db.query(models.Task).filter(models.Task.mentor_id == user.id).all()
    tasks_id = [x.id for x in tasks]
    requests_tasks = db.query(models.TaskRequest).filter(models.TaskRequest.task_id.in_(tasks_id)).all()
    requests_id = [x.task_id for x in requests_tasks]
    new_tasks = []
    for task in tasks:
        if task.id not in requests_id:
            new_tasks.append(task)
    return new_tasks


async def get_active_tasks(user: models.User, db: _orm.Session):
    tasks = db.query(models.Task).filter(models.Task.mentor_id == user.id).all()
    tasks_id = [x.id for x in tasks]
    active_tasks = db.query(models.TaskRequest).filter(models.TaskRequest.task_id.in_(tasks_id)).filter(
        models.TaskRequest.status.in_(['active', 'refused'])).all()
    for task in range(len(active_tasks)):
        task_data = list(filter(lambda x: x.id == active_tasks[task].task_id, tasks))[0]
        setattr(active_tasks[task], 'aim', task_data.aim)
        setattr(active_tasks[task], 'award', task_data.award)
        setattr(active_tasks[task], 'username', task_data.username)
        setattr(active_tasks[task], 'category', task_data.category)
    return active_tasks


async def get_finished_tasks(user: models.User, db: _orm.Session):
    tasks = db.query(models.Task).filter(models.Task.mentor_id == user.id).all()
    tasks_id = [x.id for x in tasks]
    finished_tasks = db.query(models.TaskRequest).filter(models.TaskRequest.task_id.in_(tasks_id)).filter(
        models.TaskRequest.status.in_(['finished', 'approved', 'rejected'])).all()
    for task in range(len(finished_tasks)):
        task_data = list(filter(lambda x: x.id == finished_tasks[task].task_id, tasks))[0]
        setattr(finished_tasks[task], 'aim', task_data.aim)
        setattr(finished_tasks[task], 'award', task_data.award)
        setattr(finished_tasks[task], 'username', task_data.username)
        setattr(finished_tasks[task], 'category', task_data.category)
    return finished_tasks


async def get_tasks_request(user: models.User, db: _orm.Session):
    tasks = db.query(models.Task).filter(models.Task.mentor_id == user.id).all()
    ids = [task.id for task in tasks]
    task_requests = db.query(models.TaskRequest).filter(models.TaskRequest.task_id.in_(ids)).all()
    task_requests.sort(key=lambda x: x.id, reverse=True)
    return task_requests


async def edit_mentor_tasks(task: schemas.MentorTaskEdit, user: models.User, db: _orm.Session):
    if user.role == 'mentor':
        task_obj = db.query(models.Task).get(task.task_id)
        if task.aim != 0:
            setattr(task_obj, 'aim', task.aim)
        for item in ['award', 'username', 'category']:
            if getattr(task_obj, item) != '':
                setattr(task_obj, item, getattr(task, item))
        db.commit()
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Вы не можете редактировать задания'})


async def submit_task_request(task: schemas.MentorTaskSubmit, user: models.User, db: _orm.Session):
    if user.role == 'mentor':
        task_obj = db.query(models.TaskRequest).get(task.request_id)
        task_model = db.query(models.Task).get(task_obj.task_id)
        setattr(task_obj, 'status', task.status)
        setattr(task_obj, 'comment', task.comment)
        if task.status == 'approved':
            user_obj = db.query(models.User).get(task_obj.user_id)
            user_obj.balance += task_model.award
        db.commit()
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Вы не можете подтверждать клиентов'})


def task_state(tasks: list, task_id: int):
    for i in range(len(tasks)):
        if tasks[i].id == task_id:
            return i


async def get_tasks_user(user: models.User, db: _orm.Session):
    tasks_all = db.query(models.Task).filter(models.Task.category == user.role).all()
    tasks_user = db.query(models.Task).filter(models.Task.category == 'one_user').filter(
        models.Task.username == user.username).all()
    all_tasks = tasks_user + tasks_all
    for task in range(len(all_tasks)):
        setattr(all_tasks[task], 'status', 'waiting')
    user_requests = db.query(models.TaskRequest).filter(models.TaskRequest.user_id == user.id).all()
    for req in user_requests:
        task_id = task_state(all_tasks, req.task_id)
        setattr(all_tasks[task_id], 'status', req.status)
    return all_tasks


async def send_task_request(task: schemas.MissionSubmit, user: models.User, db: _orm.Session):
    task_obj = models.TaskRequest(user_id=user.id, task_id=task.task_id, status=task.status)
    db.add(task_obj)
    db.commit()
    db.refresh(task_obj)


async def send_task_submit(task: schemas.MissionSubmit, db: _orm.Session):
    mission = db.query(models.TaskRequest).get(task.task_id)
    mission.status = 'finished'
    db.commit()


async def get_user_mentor(user: models.User, db: _orm.Session):
    user_mentor = db.query(models.User).get(user.mentor_id)
    return schemas.User.from_orm(user_mentor)


def manager_username(managers: list, manager_id: int):
    for i in range(len(managers)):
        if managers[i].id == manager_id:
            return managers[i].username


async def get_mentor_clients(user: models.User, db: _orm.Session):
    if user.role == 'mentor':
        workers = db.query(models.User).filter(models.User.mentor_id == user.id).all()
        managers = db.query(models.User).filter(models.User.role == 'manager').all()
        clients = []
        for worker in workers:
            new_clients = db.query(models.ClientInWork).filter(models.ClientInWork.worker_id == worker.id).all()
            clients += new_clients
        for i in range(len(clients)):
            manager_name = manager_username(managers, clients[i].manager_id)
            setattr(clients[i], 'manager_name', manager_name)
        clients.sort(key=lambda x: x.id)
        clients.reverse()
        return clients
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Нет доступа к данным'})


async def add_manager_deposit(deposit: schemas.AddDeposit, user: models.User, db: _orm.Session):
    if user.role == 'manager':
        client = db.query(models.ClientInWork).get(deposit.client_id)
        reward = db.query(models.ClientReward).first()
        first_day = datetime.datetime.now().replace(day=1)
        all_clients = db.query(models.ClientInWork).filter(models.ClientInWork.worker_id == client.worker_id).filter(
            models.ClientInWork.deposit_date >= first_day).all()
        dep_num = len(all_clients)
        client.deposit = True
        worker = db.query(models.User).get(client.worker_id)
        if dep_num < 3:
            exec(f'worker.balance += reward.deposit_reward_{dep_num + 1}')
        else:
            worker.balance += reward.deposit_reward_3
        db.commit()
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Вы не можете редактировать клиента'})


async def add_manager_call(call: schemas.AddCall, user: models.User, db: _orm.Session):
    if user.role == 'manager':
        client = db.query(models.ClientInWork).get(call.client_id)
        reward = db.query(models.ClientReward).first()
        worker = db.query(models.User).get(client.worker_id)
        worker.balance += reward.call_reward
        client.checked_number = True
        db.commit()
    else:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Вы не можете редактировать клиента'})
