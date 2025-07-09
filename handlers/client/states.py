from utils.Imports import *

class buystars(StatesGroup):
    buystars = State()

class checks(StatesGroup):
    check_op1 = State()
    check_op = State()
    add_activation = State()
    check_password = State()
    single_check_create = State()
    multi_check_quantity = State()
    multi_check_amount = State()
    check_discription = State()
    check_lock_user = State()
    check_password1 = State()
    ref_fund_quantity = State()
    refill_ref_fund_quantity = State()
    set_ref_fund = State()
    refill_ref_fund = State()
    reffer_id = State()

class convertation(StatesGroup):
    mittorub = State()

class output(StatesGroup):
    rub1 = State()
    usdt1 = State()
    usdt = State()
    rub = State()

class ReportStates(StatesGroup):
    waiting_description = State()

class EditTaskState(StatesGroup):
    waiting_for_amount = State()  # Состояние ожидания ввода нового количества

class Info(StatesGroup):
    forward = State()