import telebot
import wikipedia
from telebot import types
from gtts import gTTS
import io
import requests
import random
from PIL import Image, ImageFilter

bot = telebot.TeleBot('YOUR TOKEN')
wikipedia.set_lang("ru")

@bot.message_handler(commands=['start'])
def start_command(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    wiki_button = types.KeyboardButton(text='Поиск в Википедии📝')
    voice_button = types.KeyboardButton(text='Преобразовать текст в голос🗣')
    cat_button = types.KeyboardButton(text='Случайная картинка котиков🐈')
    effects_button = types.KeyboardButton(text='Эффекты на фото📸')
    keyboard.add(wiki_button, voice_button, cat_button, effects_button)
    bot.send_message(
        message.chat.id,
        'Привет, я бот для поиска информации в Википедии, преобразования текста в голос, отправки случайной картинки котиков и добавления эффектов на фото. Что бы вы хотели сделать?',
        reply_markup=keyboard
    )

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == 'Поиск в Википедии📝':
        bot.send_message(message.chat.id, 'Введите запрос для поиска на Википедии:')
        bot.register_next_step_handler(message, search_wiki)
    elif message.text == 'Преобразовать текст в голос🗣':
        bot.send_message(message.chat.id, 'Введите текст, который нужно преобразовать в голос:')
        bot.register_next_step_handler(message, convert_to_voice)
    elif message.text == 'Случайная картинка котиков🐈':
        send_random_cat(message)
    elif message.text == 'Эффекты на фото📸':
        bot.send_message(message.chat.id, 'Отправьте фото, которое нужно обработать:')
        bot.register_next_step_handler(message, apply_effects_to_photo)
    else:
        bot.send_message(message.chat.id, 'Я не знаю, что ответить на это...')

def search_wiki(message):
    try:
        page = wikipedia.page(message.text)
        summary = wikipedia.summary(message.text, sentences=3)
        bot.send_message(message.chat.id, f'Название статьи: {page.title}\n\n{summary}\n\nСсылка на статью: {page.url}')
    except wikipedia.exceptions.PageError:
        bot.send_message(message.chat.id, 'Страница не найдена в Википедии.')
    except wikipedia.exceptions.DisambiguationError as e:
        options = '\n\n'.join(e.options[:5])
        bot.send_message(message.chat.id, f'Найдено несколько страниц, уточните запрос:\n\n{options}')

def convert_to_voice(message):
    try:
        voice = gTTS(text=message.text, lang='en')
        voice_bytes = io.BytesIO()
        voice.write_to_fp(voice_bytes)
        voice_bytes.seek(0)
        response = requests.post(
            url='https://api.telegram.org/bot{0}/sendVoice'.format(bot.token),
            data={
                'chat_id': message.chat.id
            },
            files={
                'voice': ('voice.mp3', voice_bytes, 'audio/mpeg')
            }
        )
        response.raise_for_status()
    except Exception as e:
        bot.send_message(message.chat.id, 'Не удалось преобразовать текст в голос.')

def send_random_cat(message):
    try:
        response = requests.get('https://api.thecatapi.com/v1/images/search')
        data = response.json()
        image_url = data[0]['url']
        bot.send_photo(message.chat.id, image_url)
    except Exception as e:
        bot.send_message(message.chat.id, 'Не удалось получить картинку котика.')

def apply_effects_to_photo(message):
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(bot.token, file_info.file_path))
        img = Image.open(io.BytesIO(file.content))
        img_with_effects = apply_random_effect(img)
        img_buffered = io.BytesIO()
        img_with_effects.save(img_buffered, format='JPEG')
        img_buffered.seek(0)
        bot.send_photo(message.chat.id, photo=img_buffered)
    except Exception as e:
        bot.send_message(message.chat.id, 'Не удалось обработать фото.')


def apply_random_effect(image):
    effect_number = random.randint(1, 3)
    if effect_number == 1:
        return image.filter(ImageFilter.BLUR)
    elif effect_number == 2:
        return image.filter(ImageFilter.CONTOUR)
    elif effect_number == 3:
        return image.filter(ImageFilter.SHARPEN)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)