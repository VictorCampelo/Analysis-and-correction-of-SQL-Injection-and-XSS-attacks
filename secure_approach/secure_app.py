# -*- coding: utf-8 -*-
import os
import sqlite3

from flask import Flask
from flask import redirect
from flask import request
from flask import session
from flask import escape
from jinja2 import Template

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = 'schrodinger cat'

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

basedir = os.path.dirname(__file__)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
app.secret_key = 'schrodinger cat'
db = SQLAlchemy(app)

    
class Time_line(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)
    user = db.relationship('User',
        backref=db.backref('time_line', lazy=True))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(32), unique=False, nullable=False)


def init_data():
    u1 = User(username='user1', password='123456')
    Time_line(content='Hello!', user=u1)
    db.session.add(u1)
    
    u2 = User(username='user2', password='123456')
    Time_line(content='Hello!', user=u2)
    db.session.add(u2)
    
    db.session.commit()

def init():
    db.create_all()
    init_data()

def connect_db():
    return sqlite3.connect(DATABASE_PATH)

def get_user_from_username_and_password(username, password):
    # conn = connect_db()
    # cur = conn.cursor()
    # cur.execute('SELECT id, username FROM `user` WHERE username=\'%s\' AND password=\'%s\'' % (username, password))
    user = User.query.filter_by(username=username, password=password).first()
    # row = cur.fetchone()
    # conn.commit()
    # conn.close()

    return {'id': user.id, 'username': user.username} if user is not None else None


def get_user_from_id(uid):
    user = User.query.filter_by(id=uid).first()
    
    return {'id': user.id, 'username': user.username} if user is not None else None


def create_time_line(uid, content):
    user = User.query.filter_by(id=uid).first()
    tl = Time_line(content=content, user=user)
    
    db.session.add(tl)
    
    db.session.commit()
    
    return tl


def get_time_lines():
    tl = Time_line.query.order_by(Time_line.id.desc()).all()

    return map(lambda tl: {'id': tl.id, 'user_id': tl.user_id, 'content': tl.content}, tl)



def user_delete_time_line_of_id(uid, tid):
    tl = Time_line.query.filter_by(id=tid).first()
    db.session.delete(tl)
    db.session.commit()

def render_login_page():
    return '''
<form method="POST" style="margin: 60px auto; width: 140px;">
    <p><input name="username" type="text" /></p>
    <p><input name="password" type="password" /></p>
    <p><input value="Login" type="submit" /></p>
</form>
    '''


def render_home_page(uid):
    user = get_user_from_id(uid)
    time_lines = get_time_lines()
    template = Template('''
<div style="width: 400px; margin: 80px auto; ">
    <h4>I am: {{ user['username'] }}</h4>

    <form method="POST" action="/create_time_line">
        Add time line:
        <input type="text" name="content" />
        <input type="submit" value="Submit" />
    </form>

    <ul style="border-top: 1px solid #ccc;">
        {% for line in time_lines %}
        <li style="border-top: 1px solid #efefef;">
            <p>{{ line['content'] }}</p>

            {% if line['user_id'] == user['id'] %}
            <a href="/delete/time_line/{{ line['id'] }}">Delete</a>
            {% endif %}

        </li>
        {% endfor %}
    </ul>
</div>
    ''')
    return template.render(user=user, time_lines=time_lines)


@app.route('/')
def index():
    if 'uid' in session:
        return render_home_page(session['uid'])
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_login_page()
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_from_username_and_password(username, password)
        if user is not None:
            session['uid'] = user['id']
            return redirect('/')
        else:
            return redirect('/login')


@app.route('/create_time_line', methods=['POST'])
def time_line():
    if 'uid' in session:
        uid = session['uid']
        req = escape(request.form['content'])
        print(req)
        create_time_line(uid, req)
    return redirect('/')


@app.route('/delete/time_line/<tid>')
def delete_time_line(tid):
    if 'uid' in session:
        user_delete_time_line_of_id(session['uid'], tid)
    return redirect('/')


@app.route('/logout')
def logout():
    if 'uid' in session:
        session.pop('uid')
    return redirect('/login')


if __name__ == '__main__':
    # init()
    app.run(debug=False, port=5000)
