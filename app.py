from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
import helpers
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

        if join is not False and not code:
            return render_template("index.html", error="No code submitted", code=code, name=name)

        

        
        room = code
        if create is not False:
            room = generate_room_code(4)
            players = dict()
            # add the current player
            players[name] = {"guess": None, "score": 0, "host": True}
            games[room] = {"members": players, "dex_number": helpers.get_random_pokemon()}
        
        elif code not in games:
            return render_template("index.html", error="Invalid Code", code=code, name=name)

        if join is not False and code:
            player = {"guess": None, "score": 0, "host": False}
            games[room]["members"][name] = player
        session["game"] = room
        session["name"] = name
        return redirect(url_for("game"))
    else:
        return render_template("index.html")

# GET gets the game room and POST gives the information to RESULTS
@app.route("/game", methods=["POST", "GET"])
def game():
    room_code = session.get("game")
    
    if room_code is None or session.get("name") is None or room_code not in games:
        return redirect(url_for("index"))

    dex_number = games[room_code]["dex_number"]
    players = games[room_code]["members"]
    if request.method == "POST":
        name = session.get("name")
        # Get the pokemon submitted
        guess = request.form.get("guess").lower().strip()
        if not guess:
            return render_template("game.html",room_code=room_code, dex_number=dex_number, players=players, error = "Make a guess!")

        pkmn_guess = helpers.get_pokemon_info(guess)
        if not pkmn_guess:
            return render_template("game.html",room_code=room_code, dex_number=dex_number, players=players, error = "Invalid Pokemon, Try Again")
        games[room_code]["members"][name]["guess"] = pkmn_guess["id"]
        return render_template("game.html",room_code=room_code, dex_number=dex_number, players=players, error = "Guess Submitted")

    else:
        return render_template("game.html",room_code=room_code, dex_number=dex_number, players=players)

# GET gets the results of the game after calculation
@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/leave", methods=["POST"])
def leave():
    # Get the room
    room_code = session.get("game")
    
    # Get the user
    name = session.get("name")
    # check if the user was a host
    members = games[room_code]["members"]
    is_host = members[name]["host"]
    
    # remove the user
    del games[room_code]["members"][name]
    # # If the host left a populated room, promote the next player
    if members and is_host:
        new_host = next(iter(members))
        members[new_host]["host"] = True
    
    elif not members:
    # if no then delete the room
        del games[room_code]

    # clear session
    session.clear()
    # redirect to /
    return redirect(url_for("index"))

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
