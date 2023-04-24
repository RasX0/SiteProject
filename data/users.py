import datetime
import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, UserMixin
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField, IntegerField
from wtforms.validators import DataRequired


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return "<Colonist> %s %s %s" % (
            self.id, self.surname, self.name)


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField('Зарегестрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class MeaningForm(FlaskForm):
    word = StringField('Введите слово', validators=[DataRequired()])
    submit = SubmitField('Найти значение')


class TextAnalysisForm(FlaskForm):
    text = TextAreaField("Введите текст", validators=[DataRequired()])
    submit = SubmitField('Проанализровать')


class CompositionForm(FlaskForm):
    theme = StringField('Введите тему', validators=[DataRequired()])
    composition = StringField('Введите произведение', validators=[DataRequired()])
    word_count_from = IntegerField('От', validators=[DataRequired()])
    word_count_to = IntegerField('До', validators=[DataRequired()])
    submit = SubmitField('Написать')


class PasswordForm(FlaskForm):
    length_pass = IntegerField('Длина пароля', validators=[DataRequired()])
    submit = SubmitField('Сгенерировать')