from flask import Flask, render_template, request, redirect, flash, url_for, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from datetime import timedelta


#Database connection
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_DB'] = 'todo_db'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] =  'root'
app.config['SECRET_KEY'] = 'thisismysecretkey'
mysql = MySQL(app)


#flask-login user class
class User(UserMixin):
    def __init__(self, name, id):
        self.name = name
        self.id = id

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = 'Please login.'


#Ask user to login if session expired already
@login_manager.unauthorized_handler
def unauthorized():
    flash("Please login.")
    return render_template('login.html')


@app.route("/update", methods=['POST','GET'])
def update():
    cur = mysql.connection.cursor()
    newTask = request.form['updated-task']
    old_id = request.form["old_id"]
    cur.execute('UPDATE user_task SET task=%s WHERE id=%s',[newTask,int(old_id)])
    mysql.connection.commit()
    return redirect(url_for("index"))

#queries the database and load user at every request
@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute(""" SELECT * FROM users WHERE id=%s """,[int(user_id)])
    currentUser =  cur.fetchone()
    if currentUser:
        return User(id=currentUser[0],name=currentUser[1])
    else:
        return


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        cur = mysql.connection.cursor()

        username = request.form['username']
        password = request.form['password']

        #Queries the database and check if user is registered in the database
        cur.execute(""" SELECT * FROM users
                        WHERE name=%s""",[username])
        newUser = cur.fetchone()

        if newUser:
            password_check = check_password_hash(newUser[2], password)

            if  password_check:
                user = User(id=newUser[0],name=newUser[1])
                login_user(user, remember=True, duration=timedelta(seconds=10))
                return redirect(url_for("index"))

            flash('Incorrect password! Please try again')
            return render_template('login.html')

        flash("Invalid username! Please try again")
        return render_template('login.html')


@app.route("/signup", methods=["GET", "POST"])
def signUp():
    cur = mysql.connection.cursor()
    if request.method == "GET":
        return render_template("signup.html")

    elif request.method == "POST":
        username = request.form['username']
        mail = request.form['mail']
        password = generate_password_hash(request.form['password'])

        #confirm if user exist, if not add to database and redirect to login page
        cur.execute(""" SELECT * FROM users WHERE name=%s OR email=%s """,[username, mail])
        user_exist = cur.fetchall()

        if user_exist:

            #Username or email taken already, Prompt for another
            flash("Username or mail taken already, Try again")
            return redirect(url_for('signUp'))

        else:
            #On successful registration, user is redirected to the login page and ask to login the new details
            flash("You have been registered! Kindly log in")
            cur.execute(""" INSERT INTO users (name, password, email)
                                VALUES(%s,%s,%s) """,[username,password,mail])
            mysql.connection.commit()
            return redirect(url_for('login'))


@app.route("/", methods=["POST","GET"])
@login_required
def index():
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute('SELECT id,task FROM user_task WHERE user_id=%s',[int(current_user.id)])
        return render_template("index.html",tasklist=cur.fetchall())

    task = request.form['newtask']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO user_task(task, user_id) VALUES(%s,%s)",[task,current_user.id])
    mysql.connection.commit()
    return redirect(url_for('index'))

@app.route('/logout',methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/delete/<string:task>",methods=['GET'])
@login_required
def delete(task):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM user_task WHERE task=%s',[task])
    mysql.connection.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)