from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "wubbalubbadubdub"
socketio = SocketIO(app)

games = {}
# GET gets the page and POST gives the information to GAME
@app.route("/", methods=["POST", "GET"])
def index():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("index.html", error="No name submitted", code=code, name=name)

        if join != False and not code:
            return render_template("index.html", error="No code submitted", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_room_code(4)
            games[room] = {"members": 0, "guesses": []}
        
        elif code not in games:
            return render_template("index.html", error="Invalid Code", code=code, name=name)

        session["game"] = room
        session["name"] = name
        return redirect(url_for("game"))
    else:
        return render_template("index.html")

# GET gets the game room and POST gives the information to RESULTS
@app.route("/game", methods=["POST", "GET"])
def game():
    game = session.get("room")
    if game is None or session.get("name") is None or game not in games:
        return redirect(url_for("index"))

    return render_template("game.html")

# GET gets the results of the game after calculation
@app.route("/results")
def results():
    return render_template("results.html")

def generate_room_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in games:
            break
    
    return code

if __name__ == "__main__":
    socketio.run(app,debug=True)
