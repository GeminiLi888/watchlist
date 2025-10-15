import os
import sys
from tkinter.tix import Select

import click
from sqlalchemy import select
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
from sqlalchemy.orm import DeclarativeBase
from pathlib import Path
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
SQLITE_PREFIX = 'sqlite:///' if sys.platform.startswith('win') else 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLITE_PREFIX + str(Path(app.root_path) / 'data.db')
class Base(DeclarativeBase):
    pass
db = SQLAlchemy(app, model_class=Base)

class User(db.Model):
    __tablename__ = 'user'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(20))
class Movie(db.Model):  # 表名将会是 movie
    __tablename__ = 'movie'
    id: Mapped[int] = mapped_column(primary_key=True)  # 主键
    title: Mapped[str] = mapped_column(String(60))  # 电影标题
    year: Mapped[str] = mapped_column(String(4))  # 电影年份
@app.cli.command('init-db')  # 注册为命令，传入自定义命令名
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def init_database(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息
import click


@app.cli.command()
def forge():
    """Generate fake data."""
    db.drop_all()
    db.create_all()

    # 全局的两个变量移动到这个函数内
    name = 'Jenny Li'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')
@app.route('/')
# def hello():
#     return '<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'
def index():
    user=db.session.execute(select(User)).scalar()
    movies=db.session.execute(select(Movie)).scalars().all()
    return render_template('index.html', user=user, movies=movies)


if __name__ == '__main__':
    app.run(debug=True)

#测试URL_for
# from flask import url_for
# from markupsafe import escape
#
# # ...
#
# @app.route('/')
# def hello():
#     return 'Hello'
#
# @app.route('/user/<name>')
# def user_page(name):
#     return f'User: {escape(name)}'
#
# @app.route('/test')
# def test_url_for():
#     # 下面是一些调用示例（访问 http://localhost:5000/test 后在命令行窗口查看输出的 URL）：
#     print(url_for('hello'))  # 生成 hello 视图函数对应的 URL，将会输出：/
#     # 注意下面两个调用是如何生成包含 URL 变量的 URL 的
#     print(url_for('user_page', name='greyli'))  # 输出：/user/greyli
#     print(url_for('user_page', name='peter'))  # 输出：/user/peter
#     print(url_for('test_url_for'))  # 输出：/test
#     # 下面这个调用传入了多余的关键字参数，它们会被作为查询字符串附加到 URL 后面。
#     print(url_for('test_url_for', num=2))  # 输出：/test?num=2
#     return 'Test page'
# if __name__ == '__main__':
#     app.run(debug=True)
# 输出/
# /user/greyli
# /user/peter
# /test
# /test?num=2