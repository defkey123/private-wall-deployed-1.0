from flask import Flask, render_template, request, session, redirect, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re

app = Flask(__name__)
app.secret_key = "lmao this is a cool key"
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt = Bcrypt(app)

@app.route("/")
def index():
    if "userid" in session:
        return redirect('/wall')
    return render_template("login.html")

@app.route('/wall')
def display_wall():
    if not "userid" in session:
        return redirect('/')
    mysql = connectToMySQL('private_wall')
    users = mysql.query_db('SELECT * FROM users ORDER BY id DESC;')
    mysql = connectToMySQL('private_wall')
    messages = 'SELECT * FROM messages WHERE recipient = %(uid)s'
    recipient_id = { "uid" : session['userid'] }
    messages_query = mysql.query_db(messages, recipient_id)
    print(session['userid'])
    print(messages_query)
    return render_template("wall.html", users_on_template=users, messages_on_template=messages_query, sessionuserid=session["userid"])

@app.route('/register', methods=["post"])
def register():
    mysql = connectToMySQL('private_wall')

    user = {
    "first": request.form["fname"],
    "last": request.form["lname"],
    "email": request.form["email"],
    "pw": request.form["password"],
    "cpw": request.form["confirmpassword"],
    }
    print(user)
    errors = []

    if len(user['first']) < 3:
        errors.append("Please enter a longer first name")
    if len(user['last']) < 3:
        errors.append("Please enter a longer last name")
    if not user['first'].isalpha():
        errors.append("Make sure your first name is only letters")
    if not user['last'].isalpha():
        errors.append("Make sure your last name is only letters")
    if not EMAIL_REGEX.match(request.form['email']):
        errors.append("Invalid email address")
    if user['pw'] != user['cpw']:
        errors.append("Passwords do not match")
    if len(user['pw']) < 8:
        errors.append("Please enter a password with at least 8 characters")
        if len(errors) > 0:
            print("input not valid")
            url = '/'
            for err in errors:
                flash(err)
    else:
        user["pw_hash"] = bcrypt.generate_password_hash(request.form['password'])
        query = "INSERT INTO users (first_name, last_name, email, password_hash, created_at, updated_at) VALUES (%(first)s, %(last)s, %(email)s, %(pw_hash)s, NOW(), NOW());"
        print("input valid")
        url = '/wall'
        session['userid'] = mysql.query_db(query, user)
        session['name'] = user["first"]
    return redirect(url)

@app.route('/login', methods=["post"])
def login():
    mysql = connectToMySQL('private_wall')

    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form['email'], "password" : request.form['password']}
    print(data)
    result = mysql.query_db(query, data)
    if result:
        if bcrypt.check_password_hash(result[0]['password_hash'], request.form['password']):
            session['userid'] = result[0]['id']
            session['name'] = result[0]["first_name"]
            return redirect('/wall')

    flash("Login failed. Please check your credentials.")
    return redirect('/')

@app.route('/log_out', methods=["post"])
def log_out():
    print("logging out...")
    session.clear()
    return redirect('/')

@app.route('/send_message', methods=["post"])
def send_message():
    mysql = connectToMySQL('private_wall')
    query = "INSERT INTO messages (content, created_at, updated_at, author, recipient, author_name) VALUES ( %(cont)s, NOW(), NOW(), %(from)s, %(to)s, %(from_name)s )"
    data = {
    "cont" : request.form['message_text'],
    "to" : request.form['recipient'],
    "from" : session['userid'],
    "from_name" : session['name']
    }
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/delete_message', methods=["post"])
def delete_message():
    mysql=connectToMySQL('private_wall')
    message = "DELETE FROM messages WHERE id = %(msg_id)s"
    msg_id = { "msg_id" : int(request.form['message_to_delete']) }
    messages_query = mysql.query_db(message, msg_id)
    return redirect('/wall')

if __name__ == "__main__":
    app.run(debug=True)
