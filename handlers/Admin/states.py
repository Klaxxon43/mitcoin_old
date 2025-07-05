from aiogram.fsm.state import StatesGroup, State

class MailingStates(StatesGroup):
    message = State()
    progress = State()

class AdminActions(StatesGroup):
    update_rub_balance = State()
    view_user_profile = State()
    update_balance = State()

class create_chating_tasks(StatesGroup):
    create_task = State()
    create_task2 = State()

class create_op_tasks(StatesGroup):
    create_op_task = State()
    create_op_task2 = State()

class create_opbonus_tasks(StatesGroup):
    create_op = State()
    create_op2 = State()

class EditChannelStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_username = State()

class PromoStates(StatesGroup):
    waiting_amount = State()
    waiting_name = State()
    waiting_name_manual = State()
    waiting_where = State()
    waiting_count = State()
    waiting_days = State()

class edit_sell_currency(StatesGroup):
    amount = State()

class add_mining(StatesGroup):
    id = State()
    id2 = State()

class AddChannelStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_name = State()

class CreateContest(StatesGroup):
    channel_url = State()
    winners_count = State()
    set_prizes = State()
    set_prize_amounts = State()
    start_date_choice = State()
    end_date = State()
    start_date_input = State()
    
    # Условия участия (каждое — отдельное состояние)
    condition_sub_channel = State()  # Подписаться на канал
    condition_is_bot_user = State()  # Быть пользователем бота
    condition_is_active_user = State()  # Быть активным пользователем
    
    additional_conditions = State()
    contest_content = State()
    contest_text = State()
    conditions = State()
    channel_sub_input = State()