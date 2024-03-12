from aiogram import Router, F
from aiogram.types import Message

from src.database.pymongoAPI import users_db
from src.utils import kb

router = Router()


@router.message(F.text.lower() == kb.BT_PROFILE.lower())
async def get_profile(msg: Message):
    user_id = msg.from_user.id
    user = users_db.find_by_user_id(user_id)
    answer_text = f'''E-mail: {user['email']}
Username: {user['username']} 
'''
    await msg.answer(answer_text, reply_markup=kb.main_menu())
