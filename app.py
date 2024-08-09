from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///movies.db")

@app.route('/favorites')
def home():
    movies = db.execute("SELECT * FROM favorites")
    return render_template("favorites.html", movies=movies)

@app.route('/login', methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            error = "Both username and password are required."
            return render_template("login.html", error=error)
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            error = "invalid username and/or password"
            return render_template("login.html", error=error)

        session["user_id"] = rows[0]["id"]
        return redirect("/favorites")

    else:
         return render_template("login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not username or not password:
            error = "Both username and password are required."
            return render_template("register.html", error=error)
        if not confirmation:
            error = "Must provide password again."
            return render_template("register.html", error=error)
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) != 0:
            error = "Username is taken."
            return render_template("register.html", error=error)
        if not password == confirmation:
            error = "password and confirmation are not the same"
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = rows[0]["id"]
        return redirect("/login")
    else:
        return render_template("register.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("search.html")
    else:
        q =  request.form.get("q")
        if not q:
            return render_template("search.html", error="Must input a movie title")
        rows = db.execute("SELECT * FROM movies WHERE title LIKE ?", "%" + q + "%")
        return render_template('search.html', rows=rows)

@app.route('/insert', methods=['POST'])
def add():
    title = request.form.get('add')
    rows = db.execute("SELECT title FROM favorites WHERE title = ?", title)
    if len(rows) != 0 and title == rows[0]['title']:
        return render_template("search.html", message="You added this movie before")
    year = db.execute("SELECT year FROM movies WHERE title = ?", title)
    director = db.execute("SELECT name FROM people WHERE id = (SELECT person_id FROM directors WHERE movie_id = (SELECT id FROM movies WHERE title = ?))", title)
    ratings = db.execute("SELECT *  FROM ratings WHERE movie_id = (SELECT id FROM movies WHERE title = ?)", title)
    if len(year) == 0 or len(director) == 0 or len(ratings) == 0:
        return redirect("/search")
    db.execute("INSERT INTO favorites (title, year, director, votes, rating) VALUES (?, ?, ?, ?, ?)", title, year[0]['year'], director[0]['name'], ratings[0]['votes'], ratings[0]['rating'])
    return render_template("search.html", message="Movie added to favorites!")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")

@app.route("/delete", methods=["POST"])
def remove():
    title = request.form.get("remove")
    db.execute("DELETE FROM favorites WHERE title = ?", title)
    return redirect("/favorites")

@app.route("/password", methods=["GET", "POST"])
def change():
    if request.method == "POST":
        old = request.form.get("old")
        new = request.form.get("new")
        confirmation = request.form.get("confirmation")
        if not old or not new:
            error = "Both old password and new password are required."
            return render_template("password.html", error=error)
        if not confirmation:
            error = "Must provide confirmation again."
            return render_template("password.html", error=error)
        if new != confirmation:
            error = "New password and confirmation password do not match."
            return render_template("password.html", error=error)
        id = session["user_id"]
        hash = db.execute("SELECT hash FROM users WHERE id = ?", id)
        if not check_password_hash(hash[0]["hash"], old):
            return render_template("password.html", error="Old Password is not correct")
        db.execute("UPDATE users SET hash = ?", generate_password_hash(new))
        return redirect("/login")
    else:
        return render_template("password.html")
