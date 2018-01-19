from flask import Flask, request, redirect, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:thisisapassword@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'QNtEDZjNsjvBYpZY'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    content = db.Column(db.String(1000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, content, owner):
        self.title = title
        self.content = content
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    password = db.Column(db.String(32))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'index', 'blog_page']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/', methods=['POST', 'GET'])
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/blog', methods=['POST', 'GET'])
def blog_page():
    blog_id = request.args.get('id')
    user_id = request.args.get('user')

    if user_id is not None:
        user = User.query.get(user_id)
        blogs = Blog.query.filter_by(owner_id=user_id)
        return render_template('singleuser.html', user=user, blogs=blogs)

    if blog_id is not None:
        blog = Blog.query.get(blog_id)
        user = User.query.filter_by(id=blog.owner_id).first()
        return render_template('blogpost.html', blog=blog, user=user) 
    users = User.query.all()
    blogs = Blog.query.all()
    return render_template("blog.html", blogs=blogs, users=users)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            flash("Logged in")
            return redirect('/newpost')
            
        if user is None:
            flash('User does not exist', 'error')
        elif user.password != password:
            flash('Password is incorrect', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        if password == '':
            flash('Password cannot be left blank.')
        elif password != verify:
            flash("Passwords do not match.")
        if username == '':
            flash('Username cannot be left blank.')
        if verify == '':
            flash('You must verify your password.')
        if len(password) < 3:
            flash('Your password must be at least 3 characters long.')
        if len(username) < 3:
            flash('Your username must be at least 3 characters long.')

        existing_user = User.query.filter_by(username=username).first()

        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        else:
            flash('That username is already taken.')

    return render_template('signup.html')

@app.route('/newpost', methods=['POST', 'GET'])
def add_blog():

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        owner = User.query.filter_by(username=session['username']).first()
        
        title_error = ""
        content_error = ""

        if title == "" or content == "":
            if title == "":
                title_error += "You can not leave the title blank."
            if content == "":
                content_error += "You can not leave the content blank."
            return render_template("newpost.html", title_error=title_error, content_error=content_error, content_val=content, title_val=title)
        new_blog = Blog(title, content, owner)
        db.session.add(new_blog)
        db.session.commit()
        new_id = new_blog.id
        return redirect("/blog?id={0}".format(new_id))

    return render_template('newpost.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    del session['username']
    return redirect('/blog')

if __name__ == '__main__':
    app.run()