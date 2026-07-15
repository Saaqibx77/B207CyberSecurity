from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
import random
import string

app = Flask(__name__)
app.secret_key = "passwordmanager123"

conn = sqlite3.connect("password_manager.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS passwords(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
website TEXT,
site_username TEXT,
site_password TEXT
)
""")

conn.commit()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$%"
    password = ""

    for i in range(10):
        password += random.choice(chars)

    return password


def password_strength(password):

    score = 0

    if len(password) >= 8:
        score += 1

    if any(c.isupper() for c in password):
        score += 1

    if any(c.islower() for c in password):
        score += 1

    if any(c.isdigit() for c in password):
        score += 1

    if any(c in "!@#$%^&*" for c in password):
        score += 1

    if score <= 2:
        return "Weak"

    elif score == 3 or score == 4:
        return "Medium"

    else:
        return "Strong"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        try:

            cur.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username, hash_password(password))
            )

            conn.commit()

            message = "Registration Successful"

        except:
            message = "Username Already Exists"

    return render_template("register.html", message=message)


@app.route("/login", methods=["GET", "POST"])
def login():

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hash_password(password))
        )

        user = cur.fetchone()

        if user:

            session["user_id"] = user[0]
            session["username"] = user[1]

            return redirect("/dashboard")

        else:

            message = "Invalid Username or Password"

    return render_template("login.html", message=message)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    message = ""
    generated = ""
    strength = ""

    if request.method == "POST":

        website = request.form["website"]
        site_user = request.form["site_user"]
        site_password = request.form["site_password"]

        strength = password_strength(site_password)

        cur.execute(
            """INSERT INTO passwords
            (user_id,website,site_username,site_password)
            VALUES(?,?,?,?)""",
            (session["user_id"], website, site_user, site_password)
        )

        conn.commit()

        message = "Password Saved Successfully"

    cur.execute(
        "SELECT website,site_username,site_password FROM passwords WHERE user_id=?",
        (session["user_id"],)
    )

    data = cur.fetchall()

    return render_template(
        "dashboard.html",
        username=session["username"],
        passwords=data,
        message=message,
        generated=generated,
        strength=strength
    )


@app.route("/generate")
def generate():

    if "user_id" not in session:
        return redirect("/login")

    generated = generate_password()

    cur.execute(
        "SELECT website,site_username,site_password FROM passwords WHERE user_id=?",
        (session["user_id"],)
    )

    data = cur.fetchall()

    return render_template(
        "dashboard.html",
        username=session["username"],
        passwords=data,
        generated=generated,
        message="Generated Password",
        strength=password_strength(generated)
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
