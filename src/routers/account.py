from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.utils import kb
from src.users import users

router = Router()


@router.message(F.text.lower() == kb.BT_PROFILE.lower())
async def get_profile(msg: Message):
    user_id = msg.from_user.id
    user = users[user_id]
    answer_text = f'''E-mail: {user['email']}
Username: {user['username']} 
'''
    await msg.answer(answer_text, reply_markup=kb.main_menu())
