from flask import Flask, render_template
from data.users import User
from data.users import RegisterForm, LoginForm, MeaningForm, TextAnalysisForm, CompositionForm, PasswordForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import Flask, redirect, request, make_response, abort
from flask import render_template
from data import db_session
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField
from wtforms.validators import DataRequired
from flask import jsonify
import openai
from requests import get
import re
from data import db_session, users_api
import os

# импортировали нужные нам библиотеки

# api-ключ для использования искуственного интеллекта
openai.api_key = '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'

# создание flask-приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


login_manager = LoginManager()
login_manager.init_app(app)


# декоратор для загрузки пользователя
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# добавление и создание главной страницы
@app.route('/')
@app.route('/index')
def index():
    param = {}
    param['username'] = "Ученик Яндекс.Лицея"
    param['title'] = 'О нас'
    return render_template('index.html', **param)


# добавление и создание страницы для регистрации пользователей
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    # создание формы для регистрации
    form = RegisterForm()
    # проверка нажатия submit
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        # создание нового userа
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


# добавление и создание страницы для входа пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    # создание формы для входа
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        # проверка на совпадение паролей
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


# создание обработки выхода пользователя из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# добавление и создание страницы с написанием сочинения
@app.route('/composition', methods=['GET', 'POST'])
def composition():
    form = CompositionForm()
    if form.validate_on_submit():

        if str(form.composition.data) == '-':
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": f'Напиши сочинение на тему {form.theme.data}. Сочинение должно быть от {form.word_count_from.data} до {form.word_count_to.data} слов'},
                ]
            )
            answer = completion.choices[0].message.content
            with open("results.txt", "a", encoding='utf-8') as file:
                file.write(f'''\nЗапрос:
            Тема: {form.theme.data}, произведение: -, кол-во слов: от {form.word_count_from.data} до {form.word_count_to}.
            Результат:
            {answer}''')
            return render_template('composition.html', title='Сочинения', form=form, answer=answer)
        else:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": f'Напиши сочинение по произведению "{form.composition.data}" на тему {form.theme.data}. Сочинение должно быть от {form.word_count_from.data} до {form.word_count_to.data} слов'},
                ]
            )
            answer = completion.choices[0].message.content
            with open("results.txt", "a", encoding='utf-8') as file:
                file.write(f'''\nЗапрос:
            Тема: {form.theme.data}, произведение: {form.composition.data}, кол-во слов: от {form.word_count_from.data} до {form.word_count_to}.
            Результат:
            {answer}''')
            return render_template('composition.html', title='Сочинения', form=form, answer=answer)

    return render_template('composition.html', title='Сочинения', form=form)


# добавление и создание страницы со словарём
@app.route('/meaning', methods=['GET', 'POST'])
def meaning():
    form = MeaningForm()
    if form.validate_on_submit():
        if not form.word.data:
            return render_template('meaning.html', message="Введите слово", form=form, title='Словарь')
        elif len(str(form.word.data).split()) > 1:
            return render_template('meaning.html', message="Вы ввели больше одного слова", form=form, title='Словарь')
        else:
            rus_lang = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
            en_lang = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
            en_flag = True
            ru_flag = False
            for elem in str(form.word.data):
                if elem not in en_lang:
                    ru_flag = True
                    en_flag = False
                    break
            if en_flag and not ru_flag:
                # "Что значит слово {form.word.data}?"

                answ = get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{form.word.data}').json()
                answer = answ[0]['meanings'][0]["definitions"][0]["definition"]
                with open("results.txt", "a", encoding='utf-8') as file:
                    file.write(f'''\nЗапрос:
                Слово: {form.word.data}.
                Значение:
                {answer}''')
                return render_template('meaning.html', form=form, answer=answer, title='Словарь')
            else:
                content = f"Что значит слово '{form.word.data}'?"
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system",
                         "content": content},
                    ]
                )
                answer = completion.choices[0].message.content
                with open("results.txt", "a", encoding='utf-8') as file:
                    file.write(f'''\nЗапрос:
                Слово: {form.word.data}.
                Значение:
                {answer}''')
                return render_template('meaning.html', form=form, answer=answer, title='Словарь')

    return render_template('meaning.html', form=form, title='Словарь')


# добавление и создание страницы с анализом текста
@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    form = TextAnalysisForm()
    if form.validate_on_submit():
        if not form.text.data:
            return render_template('analysis.html', message="Введите текст", form=form, title='Анализ текста')
        else:
            answer = {}
            rus_lang = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
            en_lang = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
            text = str(form.text.data).strip()
            text1 = re.sub(r'[^\w\s]', '', text)
            answer['all_words'] = len(text1.split())
            answer['all_symbs'] = len(text)
            answer['all_symbs_w_o_spaces'] = len(''.join((text.split())))
            answer['spaces'] = text.count(' ')
            ru_symbs = 0
            en_symbs = 0
            nums = 0
            other_symbs = 0
            for elem in text:
                if str(elem) in rus_lang:
                    ru_symbs += 1
                elif str(elem) in en_lang:
                    en_symbs += 1
                elif str(elem) in '0123456789':
                    nums += 1
                elif str(elem) == ' ':
                    continue
                else:
                    other_symbs += 1
            answer['ru_symbs'] = ru_symbs
            answer['en_symbs'] = en_symbs
            answer['nums'] = nums
            answer['other_symbs'] = other_symbs
            with open("results.txt", "a", encoding='utf-8') as file:
                file.write(f'''\nЗапрос:
            Текст: {form.text.data}.
            Результат:
            Всего слов: {answer['all_words']};
            Всего символов: {answer['all_symbs']};
            Всего символов без пробелов: {answer['all_symbs_w_o_spaces']};
            Пробелов: {answer['spaces']};
            Всего кириллических символов: {answer['ru_symbs']};
            Всего латинских символов: {answer['en_symbs']};
            Всего цифр: {answer['nums']};
            Остальных символов: {answer['other_symbs']}.''')

            return render_template('analysis.html', form=form, title='Анализ текста', all_words=answer['all_words'],
                                   all_symbs=answer['all_symbs'], all_symbs_w_o_spaces=answer['all_symbs_w_o_spaces'],
                                   spaces=answer['spaces'], ru_symbs=answer['ru_symbs'], en_symbs=answer['en_symbs'],
                                   nums=answer['nums'], other_symbs=answer['other_symbs'])
    return render_template('analysis.html', form=form, title='Анализ текста')


# добавление и создание страницы с генерацией пароля
@app.route('/password', methods=['GET', 'POST'])
def password():
    form = PasswordForm()
    if form.validate_on_submit():
        if form.length_pass.data <= 0:
            return render_template('password.html', form=form, title='Генерация пароля',
                                   message='Введено отрицательно число')
        else:
            content = f"write a strong password {form.length_pass.data} characters long"
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": content},
                ]
            )
            answer = completion.choices[0].message.content
            with open("results.txt", "a", encoding='utf-8') as file:
                file.write(f'''\nЗапрос:
                Длина пароля: {form.length_pass.data};
                Результат: {answer}.''')
            return render_template('password.html', form=form, title='Генерация пароля', answer=answer)

    return render_template('password.html', form=form, title='Генерация пароля')


@app.route('/projects')
def projects():
    return render_template('projects.html', title='Проекты')


@app.route('/help')
def help():
    return render_template('help.html', title='Помощь')


# обработка ошибки 404
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


# обработка ошибки 400
@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


# запуск приложения
if __name__ == '__main__':
    db_session.global_init("db/base.db")
    app.register_blueprint(users_api.blueprint)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
