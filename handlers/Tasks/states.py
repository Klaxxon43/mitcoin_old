from aiogram.fsm.state import State, StatesGroup

class ChannelPromotionStates(StatesGroup):
    awaiting_subscribers_count = State()
    awaiting_channel_message = State()
    awaiting_members_count = State()
    awaiting_post_message = State()
    awaiting_channel_selection = State()

class ChatPromotionStates(StatesGroup):
    awaiting_members_count = State()
    awaiting_chat_code = State()
    awaiting_chat_selection=State()

class PostPromotionStates(StatesGroup):
    awaiting_views_count = State()
    awaiting_post_message = State()

class CommentPromotionStates(StatesGroup):
    awaiting_comments_count = State()
    awaiting_post_for_comments = State()

class LinkPromotionStates(StatesGroup):
    link_task_create = State()
    link_task_create2 = State()
    link_task_create3 = State()
    link_task_create4 = State()
    performing_task = State()

class BoostPromotionStates(StatesGroup):
    boost_task_create = State()
    boost_task_create2 = State()
    boost_task_create3 = State()

class ReactionPromotionStates(StatesGroup):
    reaction_task_create = State()
    reaction_task_create2 = State()
    reaction_task_create3 = State()
    reaction_task_create4 = State()

class CommentProof(StatesGroup):
    waiting_for_screenshot = State()

class ReactionProof(StatesGroup):
    waiting_for_screenshot = State()

class BoostProof(StatesGroup):
    waiting_for_screenshot = State()