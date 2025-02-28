import os
from typing import Annotated

import sqlalchemy.orm as _orm
from fastapi import UploadFile, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from sqladmin import Admin
from starlette.middleware.cors import CORSMiddleware
from conf import *
import schemas
from admin_models import *
from chat_app import *
from chat_websocket import ConnectionManager
from database import engine

data = {}
authentication_backend = AdminAuth(secret_key=os.environ['SECRET_KEY'])
app = FastAPI(docs_url='/docs', openapi_url='/openapi.json')
admin = Admin(app, engine, authentication_backend=authentication_backend, base_url='/admin')
manager = ConnectionManager()

origins = ['*']
templateLoader = FileSystemLoader(searchpath="templates")
env = Environment(
    loader=templateLoader,
    autoescape=select_autoescape(['html', 'xml']))

app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])

async def reset_password_email(email: str, password: str):
    template = env.get_template('password_reset.html')
    html = template.render(password=password).encode('utf-8')
    message = MessageSchema(
        subject=f"Сброс пароля",
        recipients=[email],
        body=html,
        subtype=MessageType.html)
    fm = FastMail(conf)
    await fm.send_message(message, template_name='password_reset.html')
    return {"message": "email has been sent"}


@app.post('/user')
async def create_user(file: UploadFile, email: Annotated[str, Form()], username: Annotated[str, Form()],
                      password: Annotated[str, Form()], real_name: Annotated[str, Form()],
                      join_code: Annotated[str, Form()], role: Annotated[str, Form()],
                      phone_number: Annotated[str, Form()],
                      db: _orm.Session = fastapi.Depends(services.get_db),
                      ref_link: str = ''):
    db_user = services.get_user_by_email(email=email, db=db)
    if db_user:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Пользователь с данной почтой существует'})
    user_obj = schemas.UserCreate(username=username, password=password, email=email, join_code=join_code,
                                  real_name=real_name, role=role, phone_number=phone_number)
    user = await services.create_user(file=file,
                                      user=user_obj, ref_link=ref_link, db=db)
    if user.role == 'mentor':
        await services.add_mentor_code(user.username, db)
    if user.role == 'recruiter':
        await services.add_ref_link(user.id, db)
    return await services.create_token(user=user)


@app.get('/user', response_model=schemas.User)
async def get_user(user: schemas.User = fastapi.Depends(services.get_current_user)):
    data = user.__dict__
    return data


@app.post('/user/change')
async def change_user_field(change_field: schemas.UserChangeField,
                            user: schemas.User = fastapi.Depends(services.get_current_user),
                            db: _orm.Session = fastapi.Depends(services.get_db)):
    user_change = await services.change_user_field(user.id, change_field, db)
    return user_change


@app.post('/user/password/change')
async def change_user_password(email_obj:schemas.PasswordChange, db: _orm.Session = fastapi.Depends(services.get_db)):
    email = email_obj.email
    new_pass = secrets.token_hex(4)
    pwd = services.change_user_password(email, new_pass, db)
    await reset_password_email(email, new_pass)
    return new_pass


@app.post('/user/avatar/add')
def add_user_avatar(file: UploadFile, user: schemas.User = fastapi.Depends(services.get_current_user),
                    db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.add_avatar(file, user, db)


@app.options("/token", status_code=status.HTTP_200_OK)
def users_options():
    try:
        return {'msg': 'ok'}
    except:
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Not Found'})


@app.post('/token')
async def get_token(login_form: Annotated[OAuth2PasswordRequestForm, fastapi.Depends()],
                    db: _orm.Session = fastapi.Depends(services.get_db)):
    user = await services.authenticate_user(login_form.username, login_form.password, db)
    if not user:
        raise fastapi.HTTPException(
            status_code=400,
            detail={'msg': 'Неверные данные'})

    return {'access_token': await services.create_token(user=user)}


@app.get('/user/state')
async def get_user_state(user: models.User = fastapi.Depends(services.get_current_user),
                         db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.get_user_state(user, db)


@app.get('/worker/clients')
async def get_user_clients(user: models.User = fastapi.Depends(services.get_current_user),
                           db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.get_user_clients(user, db)


@app.get('/worker/clients/complete')
async def get_user_clients_complete(user: models.User = fastapi.Depends(services.get_current_user),
                                    db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.get_user_clients_complete(user, db)


@app.post('/worker/client/edit')
def edit_worker_client(client: schemas.ClientEdit, user: models.User = fastapi.Depends(services.get_current_user),
                       db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.edit_client(client, user, db)


@app.get('/worker/top')
async def get_tasks_top(user: models.User = fastapi.Depends(services.get_current_user),
                        db: _orm.Session = fastapi.Depends(services.get_db)):
    if user.role != 'worker':
        raise fastapi.HTTPException(status_code=400, detail={'msg': 'Данные недоступны'})
    top = await services.get_tasks_top(db)
    return top


@app.get('/worker/tickets/list')
async def get_worker_tickets(user: models.User = fastapi.Depends(services.get_current_user),
                             db: _orm.Session = fastapi.Depends(services.get_db)):
    tickets = await services.get_worker_ticket(user, db)
    return tickets


@app.get('/worker/managers')
async def get_worker_managers(user: models.User = fastapi.Depends(services.get_current_user),
                              db: _orm.Session = fastapi.Depends(services.get_db)):
    managers = await services.get_worker_managers(user, db)
    return managers


@app.get('/mission')
async def get_missions(user: models.User = fastapi.Depends(services.get_current_user),
                       db: _orm.Session = fastapi.Depends(services.get_db)):
    mission = await services.get_tasks_user(user, db)
    return mission


@app.get('/regulations')
def get_regulations(db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.get_regulation(db)


@app.get('/study_materials')
def get_study_material(db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.get_study_material(db)


@app.post('/client/add')
async def add_new_client(client: schemas.ClientAdd, user: models.User = fastapi.Depends(services.get_current_user),
                         db: _orm.Session = fastapi.Depends(services.get_db)):
    new_client = await services.add_client(client, user, db)
    return new_client


@app.post('/client/comment')
async def add_client_comment(comment: schemas.ClientComment, db: _orm.Session = fastapi.Depends(services.get_db)):
    client_comment = await services.add_client_comment(comment, db)
    return client_comment


@app.get('/recruiter/team')
async def get_recruiter_team(user: models.User = fastapi.Depends(services.get_current_user),
                             db: _orm.Session = fastapi.Depends(services.get_db)):
    team = await services.recruiter_team(user, db)
    return team


@app.get('/recruiter/team/info')
async def get_recruiter_team_info(user: models.User = fastapi.Depends(services.get_current_user),
                                  db: _orm.Session = fastapi.Depends(services.get_db)):
    team_info = await services.recruiter_team_info(user, db)
    return team_info


@app.get('/manager/clients')
async def get_manager_clients(user: models.User = fastapi.Depends(services.get_current_user),
                              db: _orm.Session = fastapi.Depends(services.get_db)):
    clients = await services.get_manager_clients(user, db)
    return clients


@app.get('/manager/team')
async def get_manager_team(user: models.User = fastapi.Depends(services.get_current_user),
                           db: _orm.Session = fastapi.Depends(services.get_db)):
    team = await services.get_manager_team(user, db)
    return team


@app.post('/manager/accept/client')
async def accept_client(client: schemas.AcceptClient, user: models.User = fastapi.Depends(services.get_current_user),
                        db: _orm.Session = fastapi.Depends(services.get_db)):
    client = await services.accept_manager_client(client, user, db)
    return client


@app.post('/manager/deposit/add/1')
async def add_manager_deposit(deposit: schemas.AddDeposit,
                              user: models.User = fastapi.Depends(services.get_current_user),
                              db: _orm.Session = fastapi.Depends(services.get_db)):
    deposit_res = await services.add_manager_deposit(deposit, user, db)
    return deposit_res


@app.post('/manager/call/add')
async def add_manager_call(call: schemas.AddCall, user: models.User = fastapi.Depends(services.get_current_user),
                           db: _orm.Session = fastapi.Depends(services.get_db)):
    call_obj = await services.add_manager_call(call, user, db)
    return call_obj


@app.get('/ticket/chat')
async def get_ticket_chat(ticket: int, db: _orm.Session = fastapi.Depends(services.get_db)):
    chat = await services.get_ticket_chat(ticket, db)
    return chat


@app.post('/ticket/close')
async def close_ticket(ticket: schemas.TicketClose, db: _orm.Session = fastapi.Depends(services.get_db)):
    ticket_1 = await services.close_ticket(ticket, db)
    return ticket_1


@app.post('/payment/check/add')
async def app_payment_check(check: schemas.PaymentCheck, user: models.User = fastapi.Depends(services.get_current_user),
                            db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.add_payment_check(check, user, db)


@app.get('/mentor/payment/check')
async def get_payment_check(user: models.User = fastapi.Depends(services.get_current_user),
                            db: _orm.Session = fastapi.Depends(services.get_db)):
    payments = await services.get_payment_mentor(user, db)
    return payments


@app.post('/mentor/payment/check/close')
async def close_payment_check(payment: schemas.PaymentClose,
                              user: models.User = fastapi.Depends(services.get_current_user),
                              db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.close_payment_mentor(payment, user, db)


@app.get('/mentor/users/list')
async def get_users_mentors(user: models.User = fastapi.Depends(services.get_current_user),
                            db: _orm.Session = fastapi.Depends(services.get_db)):
    users = await services.get_mentor_users(user, db)
    return users


@app.post('/mentor/accept/user')
def accept_user_request(user_data: schemas.UserAccept, user: models.User = fastapi.Depends(services.get_current_user),
                        db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.accept_user(user_data, user, db)


@app.get('/mentor/ticket/list')
async def get_mentor_tickets(user: models.User = fastapi.Depends(services.get_current_user),
                             db: _orm.Session = fastapi.Depends(services.get_db)):
    tickets = await services.get_mentor_ticket(user, db)
    return tickets


@app.post('/mentor/tasks/add')
async def app_mentor_task(task: schemas.MentorTask, user: models.User = fastapi.Depends(services.get_current_user),
                          db: _orm.Session = fastapi.Depends(services.get_db)):
    task_result = await services.add_mentor_task(task, user, db)
    return task_result


@app.post('/mentor/tasks/edit')
async def edit_mentor_tasks(task: schemas.MentorTaskEdit,
                            user: models.User = fastapi.Depends(services.get_current_user),
                            db: _orm.Session = fastapi.Depends(services.get_db)):
    task_res = await services.edit_mentor_tasks(task, user, db)
    return task_res


@app.get('/mentor/tasks/new')
async def get_mentor_tasks(user: models.User = fastapi.Depends(services.get_current_user),
                           db: _orm.Session = fastapi.Depends(services.get_db)):
    tasks = await services.get_new_tasks(user, db)
    return tasks


@app.get('/mentor/tasks/active')
async def get_mentor_tasks_active(user: models.User = fastapi.Depends(services.get_current_user),
                                  db: _orm.Session = fastapi.Depends(services.get_db)):
    tasks = await services.get_active_tasks(user, db)
    return tasks


@app.get('/mentor/tasks/finished')
async def get_mentor_tasks_finished(user: models.User = fastapi.Depends(services.get_current_user),
                                    db: _orm.Session = fastapi.Depends(services.get_db)):
    tasks = await services.get_finished_tasks(user, db)
    return tasks


@app.post('/mentor/mission/submit')
async def submit_mentor_task(task: schemas.MentorTaskSubmit,
                             user: models.User = fastapi.Depends(services.get_current_user),
                             db: _orm.Session = fastapi.Depends(services.get_db)):
    task = await services.submit_task_request(task, user, db)
    return task


@app.get('/mentor/code')
async def get_join_code(user: models.User = fastapi.Depends(services.get_current_user),
                        db: _orm.Session = fastapi.Depends(services.get_db)):
    code = await services.get_mentor_code(user, db)
    return code


@app.post('/mentor/worker/manager/add')
def add_worker_manager(manager_add: schemas.AddManager, user: models.User = fastapi.Depends(services.get_current_user),
                       db: _orm.Session = fastapi.Depends(services.get_db)):
    return services.add_worker_manager(manager_add, user, db)


@app.get('/mentor/worker/clients')
async def get_mentor_clients(user: models.User = fastapi.Depends(services.get_current_user),
                             db: _orm.Session = fastapi.Depends(services.get_db)):
    clients = await services.get_mentor_clients(user, db)
    return clients


@app.get('/user/tasks')
async def get_user_tasks(user: models.User = fastapi.Depends(services.get_current_user),
                         db: _orm.Session = fastapi.Depends(services.get_db)):
    tasks = await services.get_tasks_user(user, db)
    return tasks


@app.post('/user/mission/take')
async def send_task_request(task: schemas.MissionRequest,
                            user: models.User = fastapi.Depends(services.get_current_user),
                            db: _orm.Session = fastapi.Depends(services.get_db)):
    task_result = await services.send_task_request(task, user, db)
    return task_result


@app.post('/user/mission/submit')
async def send_task_request(task: schemas.MissionSubmit, user: models.User = fastapi.Depends(services.get_current_user),
                            db: _orm.Session = fastapi.Depends(services.get_db)):
    task_result = await services.send_task_request(task, user, db)
    return task_result


@app.get('/user/mentor')
async def get_user_mentor(user: models.User = fastapi.Depends(services.get_current_user),
                          db: _orm.Session = fastapi.Depends(services.get_db)):
    mentor = await services.get_user_mentor(user, db)
    return mentor


admin.add_view(UserAdmin)
admin.add_view(ReferralAdmin)
admin.add_view(RegulationAdmin)
admin.add_view(ClientInWorkAdmin)
admin.add_view(StudyMaterialAdmin)
admin.add_view(PaymentCheckAdmin)
admin.add_view(JoinCodeAdmin)
admin.add_view(RewardsAdmin)
admin.add_view(TicketAdmin)
admin.add_view(TaskAdmin)
admin.add_view(TaskRequestAdmin)
admin.add_view(ChatMessageAdmin)
admin.add_view(UserHistoryAdmin)
admin.add_view(ReferralHistoryAdmin)
admin.add_view(ClientHistoryAdmin)
admin.add_view(PaymentHistoryAdmin)
admin.add_view(JoinHistoryAdmin)
