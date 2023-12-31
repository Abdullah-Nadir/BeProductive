from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import apology, login_required


# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies) and set session timeout to 365 days (1 year)
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=365)
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///BeProductive.db")


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Show home page with current day progress
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Store ending_note in a variable
        ending_note = request.form.get("endingNote")

        # Server side validation for ending_note
        if not ending_note:
            return apology("Missing Ending Note")

        # Get current date and time
        ending_datetime = datetime.datetime.now()

        # Format date and time in specific formats
        formatted_time = ending_datetime.strftime("%I:%M %p")  # Example: "03:30 PM"
        formatted_day = ending_datetime.strftime("%a, %d %b %Y")  # Example: "Tue, 14 Dec 2023"

        # Get the id of last associated day with user
        row_for_day_id = db.execute("SELECT day_id FROM relation WHERE user_id = ? ORDER BY day_id DESC LIMIT 1", session["user_id"])
        day_id = row_for_day_id[0]["day_id"]

        # Update days table
        db.execute("UPDATE days SET endingNote = ?, endingTime = ?, endingDay = ?, status = ? WHERE id = ?", ending_note, formatted_time, formatted_day, 1, day_id)

        # Redirect user to Report page
        return redirect("/report")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Check if user has started a new day or not
        row_for_status = db.execute("SELECT status FROM days WHERE id = (SELECT day_id FROM relation WHERE user_id = ? ORDER BY day_id DESC LIMIT 1)", session["user_id"])
        if len(row_for_status) > 0: # Check if previous day exists
            status = row_for_status[0]["status"]
            if status == 1:
                return apology("Kindly Start Your Day Before Checking Your Current Day's Progress")
        else:
            return apology("Kindly Start Your Day Before Checking Your Current Day's Progress")

        # Show home template
        row_for_starting_note = db.execute("SELECT startingNote FROM days WHERE id = (SELECT day_id FROM relation WHERE user_id = ? ORDER BY day_id DESC LIMIT 1)", session["user_id"])
        starting_note = row_for_starting_note[0]["startingNote"]
        rows_for_tasks = db.execute("SELECT id, task, status FROM tasks WHERE day_id = (SELECT day_id FROM relation WHERE user_id = ? ORDER BY day_id DESC LIMIT 1)", session["user_id"])
        return render_template("index.html", starting_note=starting_note, tasks=rows_for_tasks)


# Show help page for guidelines and information
@app.route("/help")
@login_required
def help():
    return render_template("help.html")


# Show history of previous days
@app.route("/history")
@login_required
def history():
    rows_for_days = db.execute("SELECT * FROM days WHERE id IN (SELECT day_id FROM relation WHERE user_id = ?) ORDER BY id DESC", session["user_id"])
    if len(rows_for_days) > 0:
        rows_for_tasks = db.execute("SELECT day_id, task, status FROM tasks WHERE day_id IN (SELECT day_id FROM relation WHERE user_id = ?) ORDER BY day_id DESC", session["user_id"])
        return render_template("history.html", days=rows_for_days, tasks=rows_for_tasks)
    else:
        return apology("You Have No Recorded History Yet!")



# Endpoint to handle incoming tasks from home page
@app.route("/home-task", methods=["POST"])
@login_required
def home_task():
    try:
        task = request.json["task"]
        # Get the id of last associated day with user
        row_for_id = db.execute("SELECT day_id FROM relation WHERE user_id = ? ORDER BY day_id DESC LIMIT 1", session["user_id"])
        id = row_for_id[0]["day_id"]
        # Update tasks table
        db.execute("INSERT INTO tasks (day_id, task, status) VALUES (?, ?, ?)", id, task, 0)
        return jsonify({"message": "Task added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Log user in
@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Must Provide Username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must Provide Password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid Username and/or Password", 403)

        # Remember which user has logged in and assign user an empty list for storing tasks
        session["user_id"] = rows[0]["id"]
        session["tasks"] = []

        # Redirect user to start page
        return redirect("/start")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


# Log user out
@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# Register user
@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Store username in variable
        username = request.form.get("username")

        # Ensure username was submitted
        if not username:
            return apology("Must Provide Username")

        # Ensure username was unique
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) > 0:
            return apology("Username Already Exists")

        # Store password and confirmation in variables
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure password was submitted
        if not password:
            return apology("Missing Password")

        # Ensure password and confirmation match
        if password != confirmation:
            return apology("Passwords Don't Match")

        # Register the new user (store in the database users table)
        hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)

        # Remember which user has Registered
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = user[0]["id"]
        session["tasks"] = []

        # Redirect user to start page
        return redirect("/start")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


# Show report of the most recent completed day to the user
@app.route("/report")
@login_required
def report():
    # Check if the most recent day is completed
    rows_for_days = db.execute("SELECT * FROM days WHERE id IN (SELECT day_id FROM relation WHERE user_id = ? ORDER BY day_id DESC LIMIT 2) ORDER BY id DESC", session["user_id"])
    if len(rows_for_days) > 0: # Check if atleast one day exists
        # Show report of last associated day
        status = rows_for_days[0]["status"]
        if status == 1:
            day = rows_for_days[0]
            day_id = day["id"]
            rows_for_tasks = db.execute("SELECT status, task FROM tasks WHERE day_id = ?", day_id)
            return render_template("report.html", day=day, tasks=rows_for_tasks)
        else:
            # Show report of 2nd last associated day
            if len(rows_for_days) > 1: # Check if 2nd last day exists
                status = rows_for_days[1]["status"]
                if status == 1:
                    day = rows_for_days[1]
                    day_id = day["id"]
                    rows_for_tasks = db.execute("SELECT status, task FROM tasks WHERE day_id = ?", day_id)
                    return render_template("report.html", day=day, tasks=rows_for_tasks)
                else:
                    return apology("We apologize for the inconvenience. Something unexpected happened, and we're working to fix it")
            else:
                return apology("Wrap Up Your Day To View The Report")
    else:
        return apology("Initiate Your Day To Pave The Way Forward!")


# Show start page for starting the day
@app.route("/start", methods=["GET", "POST"])
@login_required
def start():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Check if previous day is completed
        row_for_status = db.execute("SELECT status FROM days WHERE id = (SELECT day_id FROM relation WHERE user_id = ? ORDER BY day_id DESC LIMIT 1)", session["user_id"])
        if len(row_for_status) > 0: # Check if previous day exists
            status = row_for_status[0]["status"]
            if status == 0:
                session["tasks"].clear()
                return apology("You Haven't Wrapped Up Your Prior Day Yet!")

        # Store starting_note in a variable
        starting_note = request.form.get("startingNote")

        # Server side validation for starting_note
        if not starting_note:
            return apology("Missing Starting Note")

        # Server side validation for tasks
        if not len(session["tasks"]) > 0:
            return apology("Add 1 Or More Tasks Before Proceeding")

        # Get current date and time
        starting_datetime = datetime.datetime.now()

        # Format date and time in specific formats
        formatted_time = starting_datetime.strftime("%I:%M %p")  # Example: "03:30 PM"
        formatted_day = starting_datetime.strftime("%a, %d %b %Y")  # Example: "Tue, 14 Dec 2023"

        # Update days table
        db.execute("INSERT INTO days (startingNote, startingTime, startingDay, status) VALUES (?, ?, ?, ?)", starting_note, formatted_time, formatted_day, 0)

        # Get the ID of the last inserted row in days table
        row = db.execute("SELECT last_insert_rowid() AS id")
        day_id = row[0]["id"]

        # Update tasks table
        for task in session["tasks"]:
            db.execute("INSERT INTO tasks (day_id, task, status) VALUES (?, ?, ?)", day_id, task, 0)

        # Update relation table
        db.execute("INSERT INTO relation (user_id, day_id) VALUES (?, ?)", session["user_id"], day_id)

        # Clear tasks list of session
        session["tasks"].clear()

        # Redirect user to Home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("start.html")


# Endpoint to handle incoming tasks from start page
@app.route("/start-task", methods=["POST"])
@login_required
def start_task():
    try:
        task = request.json["task"]
        session["tasks"].append(task)
        return jsonify({"message": "Task added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Endpoint to handle tasks status
@app.route('/task-status', methods=['POST'])
def task_status():
    try:
        data = request.get_json()
        task_id = data.get('taskId')
        is_checked = data.get('isChecked')
        if is_checked == True:
            is_checked = 1
        else:
            is_checked = 0
        db.execute("UPDATE tasks SET status = ? WHERE id = ?", is_checked, task_id)
        return jsonify({"message": "Task status updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500




