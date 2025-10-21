import os
import sys
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, url_for, redirect, flash
import click
from sqlalchemy import select
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
from sqlalchemy.orm import DeclarativeBase
from pathlib import Path
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import login_required, logout_user,current_user

SQLITE_PREFIX = 'sqlite:///' if sys.platform.startswith('win') else 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLITE_PREFIX + str(Path(app.root_path) / 'data.db')
app.config['SECRET_KEY'] = 'dev'  # 等同于 app.secret_key = 'dev'
class Base(DeclarativeBase):
    pass
db = SQLAlchemy(app, model_class=Base)

class User(db.Model,UserMixin):
    __tablename__ = 'user' # 定义表名称
    id: Mapped[int] = mapped_column(primary_key=True)  # 主键
    name: Mapped[str] = mapped_column(String(20))  # 名字
    username: Mapped[str] = mapped_column(String(20))  # 用户名
    password_hash: Mapped[Optional[str]] = mapped_column(String(128))  # 密码散列值

    def set_password(self, password):  # 用来设置密码的方法，接受密码作为参数
        self.password_hash = generate_password_hash(password)  # 将生成的密码保持到对应字段

    def validate_password(self, password):  # 用于验证密码的方法，接受密码作为参数
        return check_password_hash(self.password_hash, password)  # 返回布尔值
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
    user = User(name=name, username='admin')
    user.set_password('helloflask')
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')
@app.cli.command()
@click.option('--username',prompt=True,help='The username used to login.')
@click.option('--password',prompt=True,hide_input=True,confirmation_prompt=True,help="The password used to login.")
def admin(username,password):
    db.create_all()
    user=db.session.execute(select(User)).scalar()
    if user is not None:
        click.echo('Upadating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user=User(username=username,name='Admin')
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    click.echo('Done.')

login_manager=LoginManager(app)
login_manager.login_view='login'
@login_manager.user_loader
def load_user(user_id):# 创建用户加载回调函数，接受用户 ID 作为参数
    user=db.session.get(User,int(user_id))
    return user
@app.route('/',methods=['GET','POST'])
# def hello():
#     return '<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('index'))
        title = request.form.get('title')
        year = request.form.get('year')
        if not title or not year or len(title) > 60 or len(year) > 4:
            flash('Invalid input.')
            return redirect(url_for('index'))
        movie=Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))

    user=db.session.execute(select(User)).scalar()
    movies=db.session.execute(select(Movie)).scalars().all()
    return render_template('index.html', user=user, movies=movies)
@app.route('/movie/edit/<int:movie_id>',methods=['GET','POST'])
@login_required
def edit(movie_id):
    movie=db.get_or_404(Movie,movie_id)
    if request.method == 'POST':
        title=request.form.get('title')
        year=request.form.get('year')
        if not title or not year or len(title) > 60 or len(year)!=4:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面
        movie.title=title
        movie.year=year
        db.session.commit()
        flash('Item Updated.')
        return redirect(url_for('index'))
    return render_template('edit.html',movie=movie)
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
@login_required
def delete(movie_id):
    movie = db.get_or_404(Movie, movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = db.session.execute(select(User).filter_by(username=username)).scalar()
        # 验证密码是否一致
        if user is not None and user.validate_password(password):
            login_user(user)  # 登入用户
            flash('Login success.')
            return redirect(url_for('index'))  # 重定向到主页

        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect(url_for('login'))  # 重定向回登录页面

    return render_template('login.html')
@app.route('/logout')
@login_required # 用于视图保护，后面会详细介绍
def logout():
    logout_user()
    flash('Goodbye')
    return redirect(url_for('index'))

@app.route('/settings',methods =['GET','POST'])
@login_required
def settings():
     if request.method == 'POST':
         name=request.form.get('name')
         if not name or len(name) > 20:
             flash('Invalid input.')
             return redirect(url_for('settings'))
         current_user.name=name
         db.session.commit()
         flash('Settings updated.')
         return redirect(url_for('index'))
     return render_template('settings.html')
@app.context_processor
def inject_user():  # 函数名可以随意修改
    user = db.session.execute(select(User)).scalar()
    return dict(user=user)  # 需要返回字典，等同于 return {'user': user}
#这个函数返回的变量（以字典键值对的形式）将会统一注入到每一个模板的上下文环境中，因此可以直接在模板中使用。
@app.errorhandler(404)
def page_not_found(error):
    #user=db.session.execute(select(User)).scalar()
    return render_template('404.html')
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