from flask import redirect, render_template, session
from functools import wraps

# Render message as an apology to user
def apology(message, code=400):
    return render_template("apology.html", top=code, bottom=message), code


# Decorate routes to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
