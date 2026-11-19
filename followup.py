"""
Система фоллоу-апа (проверки в 1, 3, 6 месяцев)
"""
from datetime import datetime, timedelta
import db


def schedule_followup(user_id: int, creation_time: str = None):
    """
    Планирует фоллоу-апы для пользователя на 1, 3 и 6 месяцев
    """
    if not creation_time:
        creation_time = datetime.now().isoformat()
    
    try:
        base_time = datetime.fromisoformat(creation_time)
    except:
        base_time = datetime.now()
    
    followups = [
        {
            "schedule_date": (base_time + timedelta(days=30)).isoformat(),
            "days": 30,
            "name": "1 месяц",
            "message": (
                "🔔 **Проверка через 1 месяц**\n\n"
                "Привет! Как дела? Как ты справляешься с расставанием?\n\n"
                "Давай пройдём обновлённую диагностику, чтобы оценить прогресс.\n"
                "Нажми /start, чтобы начать."
            )
        },
        {
            "schedule_date": (base_time + timedelta(days=90)).isoformat(),
            "days": 90,
            "name": "3 месяца",
            "message": (
                "🔔 **Проверка через 3 месяца**\n\n"
                "Отлично, что ты всё ещё здесь! Много воды утекло за эти три месяца.\n\n"
                "Пришла пора оценить, где ты сейчас и какой путь ты уже прошёл.\n"
                "Нажми /start для новой диагностики."
            )
        },
        {
            "schedule_date": (base_time + timedelta(days=180)).isoformat(),
            "days": 180,
            "name": "6 месяцев",
            "message": (
                "🔔 **Проверка через 6 месяцев**\n\n"
                "Полгода! Ты проделал(а) огромную работу. Пора подвести итоги.\n\n"
                "Как ты думаешь, изменилось ли что-то коренным образом? "
                "Давай это проверим диагностикой.\n"
                "Нажми /start."
            )
        }
    ]
    
    return followups


def get_pending_followups(user_id: int) -> list:
    """
    Получает запланированные фоллоу-апы, которые пора проводить
    """
    user = db.get_user_state(user_id)
    if not user or not user.get("created_at"):
        return []
    
    creation_time = user.get("created_at")
    followups = schedule_followup(user_id, creation_time)
    
    now = datetime.now().isoformat()
    pending = []
    
    for fu in followups:
        try:
            schedule_dt = datetime.fromisoformat(fu["schedule_date"])
            now_dt = datetime.fromisoformat(now)
            
            # Если время пришло и фоллоу-ап ещё не проводился
            if schedule_dt <= now_dt:
                # Проверяем, есть ли диагноз после этого времени
                diag = db.get_last_diagnosis_report(user_id)
                if diag:
                    diag_time = datetime.fromisoformat(diag["timestamp"])
                    if diag_time < schedule_dt:
                        pending.append(fu)
                else:
                    pending.append(fu)
        except:
            pass
    
    return pending


def get_days_to_next_followup(user_id: int) -> int:
    """
    Возвращает дни до следующего фоллоу-апа
    """
    user = db.get_user_state(user_id)
    if not user or not user.get("created_at"):
        return None
    
    creation_time = user.get("created_at")
    followups = schedule_followup(user_id, creation_time)
    
    now = datetime.now()
    
    for fu in followups:
        try:
            schedule_dt = datetime.fromisoformat(fu["schedule_date"])
            diag = db.get_last_diagnosis_report(user_id)
            
            # Если диагноз старше, чем запланированный фоллоу-ап
            if diag:
                diag_time = datetime.fromisoformat(diag["timestamp"])
                if diag_time < schedule_dt and schedule_dt > now:
                    days = (schedule_dt - now).days
                    return days
            else:
                if schedule_dt > now:
                    days = (schedule_dt - now).days
                    return days
        except:
            pass
    
    return None


def get_followup_status_text(user_id: int) -> str:
    """
    Генерирует текст о статусе фоллоу-апов
    """
    pending = get_pending_followups(user_id)
    days = get_days_to_next_followup(user_id)
    
    if pending:
        text = "🔔 **Пора на проверку!**\n\n"
        for fu in pending:
            text += f"• {fu['name']}\n"
        text += "\nНажми /start для диагностики."
        return text
    elif days is not None:
        if days <= 7:
            text = f"🔔 Через {days} дней планируется проверка. Скоро!"
        else:
            weeks = days // 7
            text = f"📅 Следующая проверка через ~{weeks} недель."
        return text
    else:
        return "📅 Расписание проверок будет установлено после первой диагностики."
