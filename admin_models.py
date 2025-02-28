from fastapi.requests import Request
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend

import database
import models
from services import create_token, authenticate_user


class AdminAuth(AuthenticationBackend):

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]
        db = database.SessionLocal()
        try:
            user = await authenticate_user(username, password, db)
            token = await create_token(user)
            if user.role == 'admin':
                request.session.update({"token": token})
            else:
                return False
        except Exception:
            return False
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        return True


class UserAdmin(ModelView, model=models.User):
    column_list = [models.User.username, models.User.role]
    column_searchable_list = [models.User.username]


class ReferralAdmin(ModelView, model=models.ReferralCode):
    column_list = [models.ReferralCode.username_id]


class ClientInWorkAdmin(ModelView, model=models.ClientInWork):
    column_list = [models.ClientInWork.manager_id, models.ClientInWork.status, models.ClientInWork.name]


class TaskAdmin(ModelView, model=models.Task):
    column_list = [models.Task.category]


class StudyMaterialAdmin(ModelView, model=models.StudyMaterial):
    column_list = [models.StudyMaterial.title]
    edit_template = 'custom_edit.html'


class RegulationAdmin(ModelView, model=models.Regulation):
    column_list = [models.Regulation.title]
    edit_template = 'custom_edit.html'


class RewardsAdmin(ModelView, model=models.ClientReward):
    column_list = [models.Regulation.id]


class JoinCodeAdmin(ModelView, model=models.JoinCode):
    column_list = [models.JoinCode.username_id]


class TicketAdmin(ModelView, model=models.TicketChat):
    column_list = [models.TicketChat.user_id]


class TaskRequestAdmin(ModelView, model=models.TaskRequest):
    column_list = [models.TaskRequest.user_id]


class PaymentCheckAdmin(ModelView, model=models.PaymentCheck):
    column_list = [models.PaymentCheck.username_id, models.PaymentCheck.value]


class PaymentHistoryAdmin(ModelView, model=models.PaymentCheckHistory):
    column_list = [models.PaymentCheckHistory.payment_id]


class UserHistoryAdmin(ModelView, model=models.UserHistory):
    column_list = [models.UserHistory.user_id]


class ReferralHistoryAdmin(ModelView, model=models.ReferralCodeHistory):
    column_list = [models.ReferralCodeHistory.referral_code_id]


class JoinHistoryAdmin(ModelView, model=models.JoinCodeHistory):
    column_list = [models.JoinCodeHistory.username_id]


class ClientHistoryAdmin(ModelView, model=models.ClientInWorkHistory):
    column_list = [models.ClientInWorkHistory.client_id]


class TicketHistoryAdmin(ModelView, model=models.TicketChatHistory):
    column_list = [models.TicketChatHistory.ticket_id]


class ChatMessageAdmin(ModelView, model=models.ChatMessage):
    column_list = [models.ChatMessage.ticket_id]
