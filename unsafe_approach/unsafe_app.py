# -*- coding: utf-8 -*-
import os
import sqlite3

from flask import Flask, render_template
from flask import redirect
from flask import request
from flask import session
from jinja2 import Template

app = Flask(__name__)

app.secret_key = 'TDSDI3'

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def connect_db():
    return sqlite3.connect(DATABASE_PATH)


def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
            CREATE TABLE IF NOT EXISTS user(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(32),
            password VARCHAR(32)
            )''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS time_line(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
        )''')
    conn.commit()
    conn.close()


def init_data():
    users = [
        ('Andre', '123456'),
        ('Matheus', '123456')
    ]
    lines = [
        (1, 'Boa tarde'),
        (2, 'Boa tarde Andre'),
        (1, ':D'),
        (2, ':3')
    ]
    conn = connect_db()
    cur = conn.cursor()
    cur.executemany('INSERT INTO `user` VALUES(NULL,?,?)', users)
    cur.executemany('INSERT INTO `time_line` VALUES(NULL,?,?)', lines)
    conn.commit()
    conn.close()


def init():
    create_tables()
    init_data()


def get_user_from_username_and_password(username, password):
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, username FROM `user` WHERE username=\'%s\' AND password=\'%s\'' % (username, password))
    except:
        init()
        cur.execute('SELECT id, username FROM `user` WHERE username=\'%s\' AND password=\'%s\'' % (username, password))
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return {'id': row[0], 'username': row[1]} if row is not None else None


def get_user_from_id(uid):
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, username FROM `user` WHERE id=%d' % uid)
    except:
        init()
        cur.execute('SELECT id, username FROM `user` WHERE id=%d' % uid)
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return {'id': row[0], 'username': row[1]}


def create_time_line(uid, content):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO `time_line` VALUES (NULL, %d, \'%s\')' % (uid, content))
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return row


def get_time_lines():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, user_id, content FROM `time_line` ORDER BY id DESC')
    rows = cur.fetchall()
    conn.commit()
    conn.close()

    return map(lambda row: {'id': row[0],
                            'user_id': row[1],
                            'content': row[2],
                            'username': get_user_from_id(row[1])['username']
                            }, rows)


def user_delete_time_line_of_id(uid, tid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM `time_line` WHERE  user_id=%s AND id=%s' % (uid, tid))
    conn.commit()
    conn.close()


def render_login_page():
    return render_template('login.html', erro='0')


def get_usernames(time_lines):
    usernames = []
    for lines in time_lines:
        print(lines)
        print(get_user_from_id(lines)['username'])
    return usernames


def render_home_page(uid):
    user = get_user_from_id(uid)
    time_lines = get_time_lines()
    template = Template('''
<div style="width: 400px; margin-top: 123x; margin: auto;  ">


        <h4>Usuário: {{ user['username'] }}</h4>
        <a style="margin-bottom:100px" href="\login">Sair </a>

    <form method="POST" action="/create_time_line" style="margin-top=60px">
         Comentário:
         <input name="content" type="text" required >
         <button class="btn btn-primary" type="submit" style="margin-left:20px">Publicar</button>
    </form>

    <ul style="border-top: 1px solid #ccc; margin-top:10px" class="list-group">
        {% for line in time_lines %}
        <li style="border-top: 1px solid #efefef;" class="list-group-item">
            <p><b>{{line['username']}}</b> {{ line['content']  }} </p>
            {% if line['user_id'] == user['id'] %}
            <a href="/delete/time_line/{{ line['id'] }}" style="margin-left:220px" >Apagar comentário</a>
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
            return render_template('login.html', erro='1')


@app.route('/create_time_line', methods=['POST'])
def time_line():
    if 'uid' in session:
        uid = session['uid']
        create_time_line(uid, request.form['content'])
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
    app.run(debug=False, port=5001)
