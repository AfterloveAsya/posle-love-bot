"""
Мониторинг прогресса и регресса пациента
"""
from datetime import datetime, timedelta
import db


def analyze_progress(user_id: int) -> dict:
    """
    Анализирует прогресс пациента между диагностиками
    
    Возвращает:
    {
        "trend": "прогресс" | "стабильно" | "регресс",
        "details": "описание",
        "recommendation": "рекомендация",
        "days_since_diagnosis": int,
        "score_change": int,
        "state_history": [...],
        "test_improvements": {...}
    }
    """
    
    # Получаем последние 2 диагноза
    history = db.get_diagnosis_history(user_id, limit=2)
    
    if len(history) < 2:
        return {
            "trend": "неизвестно",
            "details": "Недостаточно данных для анализа (нужны минимум 2 диагностики)",
            "days_since_diagnosis": 0,
            "state_history": history
        }
    
    prev_diagnosis = history[0]  # Старый
    curr_diagnosis = history[1]  # Новый
    
    # Вычисляем дни между диагностиками
    try:
        prev_time = datetime.fromisoformat(prev_diagnosis["timestamp"])
        curr_time = datetime.fromisoformat(curr_diagnosis["timestamp"])
        days_diff = (curr_time - prev_time).days
    except:
        days_diff = 0
    
    # Сравниваем баллы
    prev_score = prev_diagnosis.get("score", 0)
    curr_score = curr_diagnosis.get("score", 0)
    score_diff = prev_score - curr_score  # Положительное значение = улучшение
    
    # Анализируем тренд
    state_prev = prev_diagnosis.get("state", "")
    state_curr = curr_diagnosis.get("state", "")
    
    # Порядок улучшения: кризис -> стабилизация -> восстановление -> здоров
    state_order = ["кризис", "стабилизация", "восстановление", "здоров"]
    try:
        prev_idx = state_order.index(state_prev)
        curr_idx = state_order.index(state_curr)
        state_change = curr_idx - prev_idx
    except:
        state_change = 0
    
    # Определяем тренд
    if score_diff >= 10 or state_change > 0:  # Улучшение хотя бы на 10 баллов или переход в лучшее состояние
        trend = "прогресс"
        details = (
            f"🌱 Вы движетесь в правильном направлении!\n\n"
            f"• Баллы улучшились на {score_diff} (было {prev_score}, стало {curr_score})\n"
            f"• Состояние изменилось: {state_prev} → {state_curr}\n"
            f"• Дней с последней диагностики: {days_diff}"
        )
        recommendation = (
            "Продолжайте в том же темпе. Поддерживайте регулярность с техниками и дневником. "
            "Если есть возможность, обсудите прогресс с терапевтом."
        )
    elif score_diff < -10 or state_change < 0:  # Ухудшение на 10+ баллов или переход в более тяжёлое состояние
        trend = "регресс"
        details = (
            f"⚠️ Заметно ухудшение.\n\n"
            f"• Баллы изменились на {score_diff} (было {prev_score}, стало {curr_score})\n"
            f"• Состояние: {state_prev} → {state_curr}\n"
            f"• Дней с последней диагностики: {days_diff}"
        )
        recommendation = (
            "Требуется увеличить частоту занятий и обратить внимание на триггеры. "
            "Настоятельно рекомендуем обратиться к психологу для коррекции плана. "
            "Если есть суицидальные мысли — обратитесь на кризисную линию."
        )
    else:
        trend = "стабильно"
        details = (
            f"➡️ Состояние относительно стабильно.\n\n"
            f"• Баллы изменились на {score_diff} (было {prev_score}, стало {curr_score})\n"
            f"• Состояние остаётся: {state_curr}\n"
            f"• Дней с последней диагностики: {days_diff}"
        )
        recommendation = (
            "Это нормальный этап. Иногда прогресс идёт волнообразно. "
            "Продолжайте придерживаться плана и обращайте внимание на маленькие улучшения."
        )
    
    # Анализируем тесты
    test_improvements = analyze_test_scores(user_id)
    
    return {
        "trend": trend,
        "details": details,
        "recommendation": recommendation,
        "days_since_diagnosis": days_diff,
        "score_change": score_diff,
        "state_history": history,
        "test_improvements": test_improvements
    }


def analyze_test_scores(user_id: int) -> dict:
    """
    Анализирует изменения в тестах
    """
    tests = db.get_test_results(user_id, limit=20)
    
    # Группируем по типам тестов
    test_groups = {}
    for test in tests:
        test_id = test.get("test_id", "unknown")
        if test_id not in test_groups:
            test_groups[test_id] = []
        test_groups[test_id].append(test)
    
    improvements = {}
    for test_id, results in test_groups.items():
        if len(results) >= 2:
            # Сортируем по времени (новые в конце)
            results_sorted = sorted(results, key=lambda x: x.get("timestamp", ""))
            first_score = results_sorted[0].get("score", 0)
            last_score = results_sorted[-1].get("score", 0)
            
            test_names = {
                "bdi": "Депрессия (BDI)",
                "bai": "Тревога (BAI)",
                "bhs": "Безнадёжность (BHS)",
                "gad7": "Тревога (GAD-7)",
                "ptgi": "Рост после травмы (PTGI)",
                "dass21": "Стресс (DASS-21)",
                "luscher": "Люшер"
            }
            
            score_change = first_score - last_score  # Для большинства тестов, меньше = лучше
            improvements[test_id] = {
                "name": test_names.get(test_id, test_id),
                "first_score": first_score,
                "last_score": last_score,
                "change": score_change,
                "num_attempts": len(results)
            }
    
    return improvements


def should_check_progress(user_id: int, days_threshold: int = 7) -> bool:
    """
    Определяет, пора ли повторить диагностику
    """
    last_diagnosis = db.get_last_diagnosis_report(user_id)
    
    if not last_diagnosis:
        return True
    
    try:
        last_time = datetime.fromisoformat(last_diagnosis["timestamp"])
        days_since = (datetime.now() - last_time).days
        return days_since >= days_threshold
    except:
        return True


def get_progress_report_text(user_id: int) -> str:
    """
    Генерирует текстовый отчёт о прогрессе
    """
    progress = analyze_progress(user_id)
    
    emoji_map = {
        "прогресс": "🌱",
        "стабильно": "➡️",
        "регресс": "⚠️",
        "неизвестно": "❓"
    }
    
    emoji = emoji_map.get(progress["trend"], "❓")
    
    report = (
        f"{emoji} **ОТЧЁТ О ПРОГРЕССЕ**\n\n"
        f"{progress['details']}\n\n"
        f"**Рекомендация:**\n"
        f"{progress['recommendation']}"
    )
    
    if progress.get("test_improvements"):
        report += "\n\n**Изменения в тестах:**\n"
        for test_id, imp in progress["test_improvements"].items():
            if imp["change"] > 0:
                direction = "↓"  # Улучшение (если меньше = лучше)
            else:
                direction = "↑"  # Ухудшение
            report += f"• {imp['name']}: {direction} {abs(imp['change'])} баллов\n"
    
    return report
