import datetime

from pydantic import BaseModel


class _UserBase(BaseModel):
    email: str
    username: str
    real_name: str
    # displayed_name: Optional[str]
    # state: Optional[bool]
    role: str
    phone_number: str

    class Config:
        from_attributes = True
        # orm_mode = True


class User(_UserBase):
    id: int
    # date_created: datetime.datetime
    avatar_link: str = ' '
    payment_details: str = ' '
    payment_type: str = ' '
    mentor_id: int
    manager_id: int
    recruiter_id: int
    balance: float

    class Config:
        from_attributes = True
        # orm_mode = True


class UserCreate(_UserBase):
    password: str
    join_code: str

    class Config:
        from_attributes = True
        # orm_mode = True


class TokenBase(BaseModel):
    access_token: str
    token_type: str


class ClientAdd(BaseModel):
    name: str
    phone_number: str
    city: str
    start_time: datetime.datetime
    from_who: str
    call: str
    link: str
    manager_id: int


class ClientEdit(BaseModel):
    id:int
    name: str = None
    phone_number: str = None
    city: str = None
    start_time: datetime.datetime = None
    from_who: str = None
    call: str = None
    link: str = None
    manager_id: int = None


class ClientComment(BaseModel):
    id: int
    comment: str


class TicketBase(BaseModel):
    mentor_id: int
    user_id: int


class TicketClose(BaseModel):
    id: int


class PaymentCheck(BaseModel):
    value: str


class PaymentClose(BaseModel):
    id: int
    state: str


class UserAccept(BaseModel):
    id: int
    access: str


class UserChangeField(BaseModel):
    real_name: str = None
    username: str = None
    email: str = None
    new_password_1: str = None
    new_password_2: str = None
    payment_type: str = None
    payment_details: str = None


class AcceptClient(BaseModel):
    id: int
    status: str


class MentorTask(BaseModel):
    aim: str
    award: float
    category: str
    username: str = ''


class MentorTaskEdit(BaseModel):
    task_id: int
    aim: str = ''
    award: float = 0
    category: str = ""
    username: str = ''


class MentorTaskSubmit(BaseModel):
    request_id: int
    comment: str = ''
    status: str


class MissionRequest(BaseModel):
    task_id: int
    status: str


class MissionSubmit(BaseModel):
    task_id: int
    status: str


class MentorMissionSubmit(BaseModel):
    request_id: int
    status: str
    comment: str = ''


class AddManager(BaseModel):
    worker_id: int
    manager_id: int


class AddDeposit(BaseModel):
    client_id: int


class AddCall(BaseModel):
    client_id: int


class PasswordChange(BaseModel):
    email:str
