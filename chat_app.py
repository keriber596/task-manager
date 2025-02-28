import asyncio
import datetime
import secrets
import string
import threading
import time

import fastapi
import sqlalchemy.orm as _orm
from fastapi import FastAPI, WebSocket, HTTPException, status, WebSocketException, WebSocketDisconnect

import models
import schemas
import services
from services import send_chat_message

app = FastAPI()

data = {}


def cleanup_thread():
    print("Cleanup thread started")
    while True:
        try:
            time.sleep(300)
            for channel in data:
                if datetime.datetime.now() - data[channel]["lastactive"] > datetime.timedelta(hours=1):
                    del data[channel]
        except Exception as e:
            print("ERROR (A01):", e)


async def generate_unique_string(length):
    characters = string.ascii_letters + string.digits
    unique_string = ''.join(secrets.choice(characters) for _ in range(length))
    return unique_string


async def new_chat_token(user_id: int, mentor_id: int, db: _orm.Session):
    token = await generate_unique_string(8)
    ticket = models.TicketChat(token=token, user_id=user_id, mentor_id=mentor_id)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return token


async def validate_token(user_id, chat_token, db: _orm.Session):
    ticket_1 = db.query(models.TicketChat).filter(models.TicketChat.user_id == user_id).filter(
        models.TicketChat.token == chat_token).first()
    ticket_2 = db.query(models.TicketChat).filter(models.TicketChat.mentor_id == user_id).filter(
        models.TicketChat.token == chat_token).first()
    try:
        return (ticket_1 is not None) or (ticket_2 is not None)
    except KeyError:
        return False


async def chat_available(chat_token, db: _orm.Session):
    chat = db.query(models.TicketChat).filter(models.TicketChat.token == chat_token).first()
    return chat is not None


async def send_message(chat_token, user_id, user2_id, data_to_send, db: _orm.Session):
    for user in [user_id, user2_id]:
        try:
            if "socket" in data[chat_token]["users"][str(user)]:
                await data[chat_token]["users"][str(user)]["socket"].send_json(
                    {'message_text': data_to_send, 'user_id': user_id, 'datetime': str(datetime.datetime.now())})
        except KeyError:
            pass
    chat = db.query(models.TicketChat).filter(models.TicketChat.token == chat_token).first()
    await send_chat_message(chat.id, data_to_send, user_id, db)


@app.websocket("/ws/chat")
async def socket_handler(user_id: str, chat_token: str, websocket: WebSocket,
                         db: _orm.Session = fastapi.Depends(services.get_db)):
    await websocket.accept()
    if not await chat_available(chat_token, db):
        await websocket.close(1008, "Channel not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    chat = db.query(models.TicketChat).filter(models.TicketChat.token == chat_token).first()
    try:
        if data[chat_token]["lock"]:
            chat_f = 1
    except KeyError:
        if chat is not None:
            data[chat_token] = {"auto_join": "true", "max_users": 2, "allow_dm_betwen_members": "true",
                                "admin": [], "users": {}, "lock": asyncio.Lock()}
    async with data[chat_token]["lock"]:
        if not await validate_token(user_id=user_id, chat_token=chat_token, db=db):
            await websocket.close(1008, "Not authorised")
            raise HTTPException(status_code=401, detail="You are not authorized")
        try:
            if "socket" in data[chat_token]["users"][user_id]:
                chat_f = 1
        except KeyError:
            data[chat_token]["users"][user_id] = {"name": user_id}

        user2_id = str(chat.mentor_id) if user_id == str(chat.user_id) else str(chat.user_id)
        try:
            if "socket" in data[chat_token]["users"][user2_id]:
                chat_f = 1
        except KeyError:
            data[chat_token]["users"][user2_id] = {"name": user2_id}
        if "socket" not in data[chat_token]["users"][user_id]:
            data[chat_token]["users"][user_id]["socket"] = websocket
    try:
        while True:
            data_to_send = await websocket.receive_text()
            user2_id = str(chat.mentor_id) if user_id == str(chat.user_id) else str(chat.user_id)
            await send_message(chat_token=chat_token, user_id=user_id, user2_id=user2_id,
                               data_to_send=data_to_send, db=db)
    except (WebSocketDisconnect, WebSocketException):
        async with data[chat_token]["lock"]:
            del data[chat_token]["users"][user_id]


@app.post("/ws/ticket/create")
async def create_group(ticket: schemas.TicketBase,
                       db: _orm.Session = fastapi.Depends(services.get_db)):
    max_users = 2
    open_tickets = db.query(models.TicketChat).filter(models.TicketChat.user_id == ticket.user_id).filter(
        models.TicketChat.closed == False).all()
    if open_tickets != []:
        raise HTTPException(status_code=401, detail={'msg': "You have opened tickets"})
    chat_token = await new_chat_token(ticket.user_id, ticket.mentor_id, db)

    data[chat_token] = {"auto_join": "true", "max_users": max_users, "allow_dm_betwen_members": "true",
                        "admin": [], "users": {}, "lock": asyncio.Lock(), }
    data[chat_token]["users"][str(ticket.user_id)] = {"name": ticket.user_id}
    data[chat_token]["users"][str(ticket.mentor_id)] = {"name": ticket.mentor_id}
    return {"chat_token": chat_token}


threading.Thread(target=cleanup_thread).start()
