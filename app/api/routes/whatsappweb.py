from fastapi import APIRouter

from app.core.actions import RepeatedTimer
from app.core.global_vars import timers


router = APIRouter()



# x = 0
# def func(y):
#     global x
#     print('x'*50)
#     x += 1
#
#
# timers['timer_1'] = RepeatedTimer(2, func, 'customized_counteer')
#
# timers['timer_1'].start()



@router.get('/')
def timer():
    print(timers)
    return {'current': '0'}
