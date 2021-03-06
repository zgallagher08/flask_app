from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
# from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from config import mysql_rootpassword
from functools import wraps

app = Flask(__name__);

# Config MySQL
app.config['MySQL_HOST'] = 'localhost'
app.config['MySQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = mysql_rootpassword
app.config['MySQL_DB'] = 'flaskapp'
app.config['MySQL_CURSORCLASS'] = 'DictCursor'
# init MySQL
# mysql = MySQL(app)

# Index
@app.route('/')
def index():
  return render_template('home.html')

# About
@app.route('/about')
def about():
  return render_template('about.html')

# Articles
@app.route('/articles')
def articles():
  cur = mysql.connection.cursor()

  result = cur.execute('SELECT * FROM articles')

  articles = cur.fetchall()

  if result > 0:
    return render_template('articles.html', articles=articles)
  else:
    msg = 'No articles found'
    return render_template('articles.html', msg=msg)
    
  cur.close()

# Single Article
@app.route('/article/<string:id>')
def article(id):
  cur = mysql.connection.cursor()

  result = cur.execute('SELECT * FROM articles WHERE id = %s', [id])

  article = cur.fetchone()

  return render_template('article.html', article=article)

# Register User Form
class RegisterForm(Form):
  name = StringField('Name', [validators.Length(min=1, max=50)])
  username = StringField('Username', [validators.Length(min=4, max=25)])
  email = StringField('Email', [validators.Length(min=6, max=50)])
  password = PasswordField('Password', [
    validators.DataRequired(),
    validators.equal_to('confirm', message='Passwords do not match')
  ])
  confirm = PasswordField('Confirm Password')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
  form = RegisterForm(request.form)
  if request.method == 'POST' and form.validate():
    name = form.name.data
    email = form.email.data
    username = form.username.data
    password = sha256_crypt.encrypt(str(form.password.data))

    # Create cursor
    cur = mysql.connection.cursor()

    # Execute query
    cur.execute('INSERT INTO users(name, email, username, password) VALUES (%s, %s, %s, %s)', (name, email, username, password))

    # Commit to DB
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('You are now registered.', 'success')

    return redirect(url_for('login'))
  return render_template('register.html', form=form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    # Get form fields
    username = request.form['username']
    password_attempt = request.form['password']

    # Create cursor
    cur = mysql.connection.cursor()

    # Get user by username
    result = cur.execute('SELECT * FROM users WHERE username = %s', [username])

    if result > 0:
      # Get stored hash
      data = cur.fetchone()
      password = data['password']

      # Compare passwords
      if sha256_crypt.verify(password_attempt, password):
        # Successful login
        session['logged_in'] = True
        session['username'] = username

        flash('You are now logged in', 'success')
        return redirect(url_for('dashboard'))
      else:
        error = 'Invalid login'
        return render_template('login.html', error=error)
      # Close connection
      cur.close()
    else:
      error = 'Username not found.'
      return render_template('login.html', error=error)

  return render_template('login.html')

# Check if user is logged in
def is_logged_in(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else:
      flash('Unauthorized. Please log in.', 'danger')
      return redirect(url_for('login'))
    return wrap

# Logout
app.route('/logout')
# @is_logged_in
def logout():
  session.clear()
  flash('You are now logged out', 'success')
  return redirect('url_for'('login'))

# Dashboard
app.route('/dashboard')
# @is_logged_in
def dashboard():
  cur = mysql.connection.cursor()

  result = cur.execute('SELECT * FROM articles')

  articles = cur.fetchall()

  if result > 0:
    return render_template('dashboard.html', articles=articles)
  else:
    msg = 'No articles found'
    return render_template('dashboard.html', msg=msg)

  cur.close()

# Add Article Form
class ArticleForm(Form):
  title = StringField('Title', [validators.Length(min=1, max=200)])
  body = TextAreaField('Body', [validators.Length(min=30)])

# Dashboard
app.route('/add_article', methods=['GET', 'POST'])
# @is_logged_in
def add_article():
  form = ArticleForm(request.form)
  if request.method == 'POST' and form.validate():
    title = form.title.data
    body = form.body.data

    cur = mysql.connection.cursor()

    cur.execute('INSERT INTO articles(title, body, author) VALUES (%s, %s, %s)', (title, body, session['username']))

    mysql.connection.commit()

    cur.close()

    flash('Article created', 'success')
    return redirect(url_for('dashboard'))
  return render_template('add_article.html', form=form)

# Edit Article Form
class ArticleForm(Form):
  title = StringField('Title', [validators.Length(min=1, max=200)])
  body = TextAreaField('Body', [validators.Length(min=30)])

# Dashboard
app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
# @is_logged_in
def edit_article(id):
  cur = mysql.connection.cursor()

  # Get Article by ID
  result = cur.execute('SELECT * FROM articles WHERE id = %s', [id])

  article = cur.fetchone()

  form = ArticleForm(request.form)

  form.title.data = article['title']
  form.title.data = article['body']

  if request.method == 'POST' and form.validate():
    title = request.form['title']
    body = request.form['body']

    cur.execute("UPDATE articles SET title=%s, body=%S WHERE id=%s", (title, body, id))

    mysql.connection.commit()

    cur.close()

    flash('Article created', 'success')
    return redirect(url_for('dashboard'))
  return render_template('edit_article.html', form=form)

@app.route('/delete_article/<string:id>', methods=['POST'])
# @is_logged_in
def delete_article(id):
  cur = mysql.connection.cursor()

  cur.execute('DELETE FROM articles WHERE id=%s', [id])

  mysql.connection.commit()

  cur.close()

  flash('Article Deleted', 'success')
  return redirect(url_for('dashboard'))


if __name__ == '__main__':
  app.secret_key='temp'
  app.run(debug=True)