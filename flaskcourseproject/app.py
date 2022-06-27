from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from datetime import datetime
from persiantools import digits
from flask_login import current_user, login_required, login_user, logout_user, UserMixin, LoginManager
from khayyam import JalaliDate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
@login_manager.user_loader

def load_user(user):
    return User.get(user)

def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    return user
 
class RegistrationForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('ایمیل: ', validators=[DataRequired(), Email()])
    password = PasswordField('رمز عبور: ', validators=[DataRequired()])
    confirm_password = PasswordField('تکرار رمز عبور: ', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('ثبت نام')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('نام کاربری انتخاب شده تکراری است.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('این ایمیل قبلا ثبت شده است.')

class LoginForm(FlaskForm):
    email = StringField('ایمیل: ', validators=[DataRequired(), Email()])
    password = PasswordField('رمز عبور: ', validators=[DataRequired()])
    remember = BooleanField('مرا به خاطر بسپار')
    submit = SubmitField('ورود')

class PostForm(FlaskForm):
    title = StringField('عنوان: ', validators=[DataRequired()])
    content = TextAreaField('محتوا: ', validators=[DataRequired()])
    submit = SubmitField('ایجاد')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    
    def get(user_id):
        user = User.query.filter_by(id=user_id).first()
        return user
    def __repr__(self):
        return f"{self.username}"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_posted = db.Column(db.String, nullable=False, default=digits.en_to_fa(str(JalaliDate.today().strftime('%A %d %B %Y'))))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

@app.route('/')
def index():
    posts = Post.query.order_by(Post.date.desc()).all()
    # posts = [
    #     {
    #         'author': 'علی اصلانی',
    #         'title': 'پست شماره یک',
    #         'content': 'این یک پست ساده برای شما هست',
    #         'date_posted': '۲۰ خرداد ۱۳۹۷'
    #     },
    #     {
    #         'author': 'حمید امیری',
    #         'title': 'پست شماره دو',
    #         'content': 'این یک پست ساده برای شما هست',
    #         'date_posted': '۲۰ فروردین ۱۳۹۹'
    #     },
    #     {
    #         'author': 'بهار عظیمی',
    #         'title': 'پست شماره سه',
    #         'content': 'این یک پست ساده برای شما هست',
    #         'date_posted': '۲۰ اردیبهشت ۱۴۰۰'
    #     },
    #     {
    #         'author': 'علی اصلانی',
    #         'title': 'پست شماره چهار',
    #         'content': 'این یک پست ساده برای شما هست',
    #         'date_posted': '۱۱ تیر ۱۴۰۱'
    #     }
    # ]
    content = {'posts': posts, 'title': 'خانه'}
    return render_template('index.html', content = content)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    else:

        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data, method='sha256')
            new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('حساب کاربری شما با موفقیت ساخته شد', 'success')
            return redirect(url_for('login'))
        return render_template('signup.html', form=form, content = {'title': 'ثبت نام', 'ValidationError': form.errors})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    else:

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('index'))
            else:
                flash('اطلاعات وارد شده اشتباه است', 'danger')
        return render_template('login.html', form=form, content={'title': 'ورود'})


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/account')
@login_required
def account():
    return render_template('account.html', content={'title': 'حساب کاربری'})

@app.route('/newpost', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        print('validate')
        post = Post(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('پست شما با موفقیت ثبت شد', 'success')
        return redirect(url_for('index'))
    print(current_user.email)
    return render_template('create_post.html', form=form, content={'title': 'ایجاد پست'})

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id == current_user.id:
        return render_template('post.html', content={'title': 'پست'}, post=post, user=current_user)
    return render_template('post.html', content={'title': post.title}, post=post)




if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
    