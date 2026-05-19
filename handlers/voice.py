import io
import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states import VoiceConfirm
from keyboards import main_menu_kb
from loader import bot
from handlers.oars import process_situation, process_emotion, process_body, process_thought, process_behavior
from handlers.diary import diary_entry

router = Router()

OARS_HANDLERS = {
    "OARS:waiting_situation": process_situation,
    "OARS:waiting_emotion": process_emotion,
    "OARS:waiting_body": process_body,
    "OARS:waiting_thought": process_thought,
    "OARS:waiting_behavior": process_behavior,
}


async def transcribe_audio(ogg_data) -> str:
    import speech_recognition as sr
    from pydub import AudioSegment
    r = sr.Recognizer()
    ogg_data.seek(0)
    audio = AudioSegment.from_file(ogg_data, format="ogg")
    wav_buf = io.BytesIO()
    audio.export(wav_buf, format="wav")
    wav_buf.seek(0)
    with sr.AudioFile(wav_buf) as source:
        audio_data = r.record(source)
    return r.recognize_google(audio_data, language="ru-RU")


@router.message(F.voice)
async def handle_voice(message: types.Message, state: FSMContext):
    try:
        file_info = await bot.get_file(message.voice.file_id)
        ogg_data = await bot.download_file(file_info.file_path)
        text = await transcribe_audio(ogg_data)
    except Exception as e:
        logging.error(f"Voice transcription error: {e}")
        await message.answer("Не удалось распознать голос. Убедись, что на сервере установлен ffmpeg, или напиши текстом.")
        return
    current_state = await state.get_state()
    await state.update_data(voice_text=text, original_state=current_state)
    await state.set_state(VoiceConfirm.waiting)
    await message.answer(f"🎤 Распознано: {text}\n\nВсё верно? (да/нет)")


@router.message(VoiceConfirm.waiting)
async def voice_confirm(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = data.get("voice_text", "")
    original_state = data.get("original_state")
    if message.text.lower().strip() in ("да", "да.", "yes", "y", "yeah", "+", "верно", "правильно"):
        new_msg = message.model_copy(update={"text": text})
        if original_state is None:
            await state.clear()
            await diary_entry(new_msg)
        elif "OARS:" in original_state:
            handler = OARS_HANDLERS.get(original_state)
            if handler:
                await handler(new_msg, state)
        elif "Diagnosis:" in original_state:
            await state.clear()
            await message.answer("Пожалуйста, выбери вариант из кнопок ниже 👇")
        else:
            await state.clear()
    else:
        if original_state:
            await state.set_state(original_state)
        else:
            await state.clear()
        await message.answer("Напиши текстом:")
