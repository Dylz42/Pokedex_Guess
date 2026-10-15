import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_socketio import join_room, leave_room, send, SocketIO
import random
import helpers
from string import ascii_uppercase

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
socketio = SocketIO(app, logger=True, engineio_logger=True)

games = {}
connections = {}
disconnections = {}

@socketio.on("connect")
def connect(auth):
    """Connect a user to a room or create the room"""
    # Get room and name
    room_code = session.get("game")
    name = session.get("name")
    # Validate the room and name
    if room_code is None or name is None or room_code not in games:
        return False
    
    if name not in games[room_code]["members"]:
        return False
    # Join room on socketio
    join_room(room_code)

    player_key = (room_code, name)
    connections.setdefault(player_key, set()).add(request.sid)
    disconnections.pop(player_key, None)

    print(f"{name} joined Socket.IO room {room_code}")

@socketio.on("disconnect")
def disconnect():
    """Disconnect the user from a room"""

    # Get name and user
    room_code = session.get("game")
    name = session.get("name")

    # Validate room and user
    if room_code is None or name is None:
        return

    # Check if the connection exists
    player_key = (room_code, name)

    if player_key in connections:
        connections[player_key].discard(request.sid)

        if not connections[player_key]:
            del connections[player_key]

            # Record the disconnect
            token = object()
            disconnections[player_key] = token

            # Remove the player and notify
            socketio.start_background_task(remove_disconnected_player, room_code,name,token)

    print(f"{name} disconnected from Socket.IO")



@app.route("/", methods=["POST", "GET"])
def index():
    """ GET gets the page and POST gives the information to GAME"""
    # Start fresh, clear the session
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        # Validate the name and code
        if not name:
            return render_template("index.html", error="No name submitted", code=code, name=name)

        if join is not False and not code:
            return render_template("index.html", error="No code submitted", code=code, name=name)

        

        # If create room is pressed, then create the room and add it to the list
        room = code
        if create is not False:
            room = generate_room_code(4)
            players = dict()
            # add the current player
            players[name] = {"guess": None, "score": None, "host": True, "round_points": None}
            games[room] = {"members": players, "dex_number": helpers.get_random_pokemon(), "status": "game"}
        
        # If the code written isnt valid
        elif code not in games:
            return render_template("index.html", error="Invalid Code", code=code, name=name)

        # If there is a code and join is pressed
        if join is not False and code:
            # Check if the name given is unique
            if name.lower() in (player_name.lower() for player_name in games[room]["members"]):
                return render_template("index.html", error="Name already in game", code=code, name=name)

            # Add the user to the room
            player = {"guess": None, "score": None, "host": False, "round_points": None}
            games[room]["members"][name] = player
            socketio.emit("players_updated", to=room)
        
        # Store the session info
        session["game"] = room
        session["name"] = name
        return redirect(url_for("game"))
    else:
        return render_template("index.html")



@app.route("/leaderboard")
def leaderboard():
    """Update the leaderboard, it is GET only for viewing"""

    # Get the name and roomcode for  the player and validate
    room_code = session.get("game")
    name = session.get("name")

    if room_code not in games:
        return "", 404
    
    players = games[room_code]["members"]

    if name not in players:
        return "", 403

    # sort the players in the order of score
    sorted_players = sort_players(players)
    
    return render_template("leaderboard.html", players=sorted_players, current_player=name)


@app.route("/game-controls")
def game_controls():
    """Update game controls, it does POST requests but for the game page only so GET is only needed here"""
    # Get details and validate them
    room_code = session.get("game")
    name = session.get("name")

    if room_code not in games:
        return "", 404
    
    players = games[room_code]["members"]

    if name not in players:
        return "", 403

    # Return the game controls and ensure the host gets their special buttons
    is_host = players[name]["host"]
    status = games[room_code]["status"]

    return render_template("game_controls.html", is_host=is_host, status=status)

@app.route("/game", methods=["POST", "GET"])
def game():
    """GET gets the game room and POST gives the information to RESULTS"""

    # Get the game room and validate
    room_code = session.get("game")
    
    if room_code is None or session.get("name") is None or room_code not in games:
        return redirect(url_for("index"))

    # Get all the details for this game room
    dex_number = games[room_code]["dex_number"]
    players = games[room_code]["members"]
    name = session.get("name")
    status=games[room_code]["status"]
    
    # Order the players
    players = sort_players(players)
    if name not in players:
        return redirect(url_for("index"))

    is_host = players[name]["host"]

    if request.method == "POST":
        # Check if the status is valid
        if status != "game":
            return jsonify({"message": "This round has already ended"}), 409

        # Get the pokemon submitted
        guess = request.form.get("guess")
        if not guess or not guess.strip():
            return jsonify({"message": "Make a guess"}), 400
        
        # Process the input for guess
        guess = guess.lower().strip()
        pkmn_guess = helpers.get_pokemon_info(guess)

        # Handle mispelled pokemon or invalid pokemon
        if not pkmn_guess:
            return jsonify({"message": "Invalid Pokemon, Try Again"}), 400
        
        games[room_code]["members"][name]["guess"] = pkmn_guess["id"]

        # Emit the guess to all players
        socketio.emit("guess_submitted", to=room_code)
        return jsonify({"message": "Guess Submitted!"}), 200

    # If the request is game then run guessing but if its results then run results
    else:
        if status == "game":
            content = render_template("guessing.html", room_code=room_code, dex_number=dex_number)
        else:
            content = results_content(room_code)

        return render_template("game.html", room_code=room_code, players=players, is_host=is_host, status=status, content=content, current_player=name)

@app.route("/end", methods=["POST"])
def end():
    """End the round and put up the results page"""
    # Get the room code
    room_code = session.get("game")
    name = session.get("name")

     # Make sure there is a room and valid name
    if room_code is None or name is None or room_code not in games:
        return redirect(url_for("index"))

    # Get the player who pressed the button
    members = games[room_code]["members"]
    if name not in members:
        return redirect(url_for("index"))

    is_host = members[name]["host"]
    
    # Check if the player is the host
    # Redirect the game to results.html
    if is_host:
        # get the pokedex number from game
        answer_id = games[room_code]["dex_number"]

        if games[room_code]["status"] != "game":
            return jsonify({"message": "Round already ended"}), 409
        
        # calculate the score for each player and add it to the scores
        for player in members.values():
            player_guess = player["guess"]

            if player_guess is None:
                continue

            points = helpers.calculate_points(player_guess,answer_id)

            player["round_points"] = points
            if player["score"] is None:
                player["score"] = points

            else:
                player["score"] += points

        # set status as result
        games[room_code]["status"] = "results"

        # Notify everyone in the room
        socketio.emit("round_ended", to=room_code)

        return "", 204

    else:
        return jsonify({"message": "Only host can end the round"}), 403

    

@app.route("/leave", methods=["POST"])
def leave():
    """Handle a player pressing the leave button, move host privledges and close a room if empty"""
    # Get the room
    room_code = session.get("game")
    
    # Get the user
    name = session.get("name")

    # Make sure there is a room and valid name
    if room_code is None or name is None or room_code not in games:
        return redirect(url_for("index"))

    # check if the user was a host
    members = games[room_code]["members"]

    if name not in members:
        session.clear()
        return redirect(url_for("index"))

    is_host = members[name]["host"]
    
    # remove the user
    del games[room_code]["members"][name]
    connections.pop((room_code, name), None)
    disconnections.pop((room_code, name), None)
    # # If the host left a populated room, promote the next player
    if members and is_host:
        new_host = next(iter(members))
        members[new_host]["host"] = True
    
    elif not members:
    # if no then delete the room
        del games[room_code]

    if room_code in games:
        socketio.emit("players_updated", to=room_code)
    # clear session
    session.clear()
    # redirect to /
    return redirect(url_for("index"))

@app.route("/reset", methods=["POST"])
def reset():
    """Reroll a new pokemon guess and move the players to a new guessing page"""

     # Get the room
    room_code = session.get("game")
      # Get the user
    name = session.get("name")
    if room_code is None or name is None or room_code not in games:
        return redirect(url_for("index"))
     # check if the person who pressed was the host
    members = games[room_code]["members"]

    if name not in members:
        return redirect(url_for("index"))

    is_host = members[name]["host"]


    # Change the pokemon guess for the room if the user who pressed it is the host
    if is_host:
        old_poke = games[room_code]["dex_number"]
        new_poke = helpers.get_random_pokemon()

        # Keep getting a new guess until the guess is different from the old guess
        while new_poke == old_poke:
            new_poke = helpers.get_random_pokemon()
            
        games[room_code]["dex_number"] = new_poke
        games[room_code]["status"] = "game"


        # Reset the guesses for the user
        for player in members.values():
            player["guess"] = None
            player["round_points"] = None

        socketio.emit("round_reset", to=room_code)
        return "", 204

    else:
        return jsonify({"message": "Only host can reset the game"}), 403

@app.route("/game-content")
def game_content():
    """Handle the main content page of games.html, reroute between guessing and results depending on status"""
    # Get the users and game room and validate
    room_code = session.get("game")
    name = session.get("name")

    if room_code not in games:
        return "", 403
    
    members = games[room_code]["members"]

    if name not in members:
        return "", 403

    status = games[room_code]["status"]

    # Check the status of the game and move the page depending on the status
    if status == "game":
        return render_template("guessing.html", room_code=room_code, dex_number=games[room_code]["dex_number"])
    
    return results_content(room_code)

def results_content(room_code):
    """Manage and return the content for the results subpage"""
    players = sort_players(games[room_code]["members"])

    # Get details about the guess for the game
    answer_id = games[room_code]["dex_number"]
    answer_name = helpers.get_pokemon_info(answer_id)["name"].title()
    answer_sprite = helpers.get_pokemon_sprite(answer_id)

    # Get the answers and process them for each user
    round_guesses = []

    for player_name, player in players.items():
        guess_id = player["guess"]

        if guess_id is None:
            round_guesses.append({"name": player_name,"pokemon": None,"sprite": None,"dex_number": None, "points": None})
            continue

        pokemon_name = helpers.get_pokemon_info(guess_id)["name"].title()
        pokemon_sprite = helpers.get_pokemon_sprite(guess_id)

        round_guesses.append({"name": player_name,"pokemon": pokemon_name,"sprite": pokemon_sprite,"dex_number": guess_id, "points": player["round_points"]})

    return render_template("results.html",room_code=room_code,dex_number=answer_id,pokemon=answer_name, answer_sprite=answer_sprite, round_guesses=round_guesses)


def remove_disconnected_player(room_code, name, token):
    """Manage disconnected players after 30 seconds"""
    socketio.sleep(30)

    player_key = (room_code, name)

    # Ignore outdated disconnect tasks
    if disconnections.get(player_key) is not token:
        return

    # Don't remove someone who reconnected
    if player_key in connections:
        return

    # Check the room still exists
    if room_code not in games:
        return

    members = games[room_code]["members"]

    # Make sure the user is in the members list
    if name not in members:
        return

    # Check if the disconnected member is the host
    is_host = members[name]["host"]

    # Delete the player and move the host privileges if the user was the host
    del members[name]
    disconnections.pop(player_key, None)

    if members and is_host:
        new_host = next(iter(members))
        members[new_host]["host"] = True

    elif not members:
        del games[room_code]
        return

    # Let all players in the room know the player list is updated
    socketio.emit("players_updated", to=room_code)

    print(f"{name} removed after disconnecting for 30 seconds")


def generate_room_code(length):
    """Generate a random unique 4 digit room code"""
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in games:
            break
    
    return code

def sort_players(players):
    """Sort players in ascending order and ensure users with None points are put last"""
    sorted_players = dict(sorted(
    players.items(),
    key=lambda item: (
        item[1]["score"] is None,
        item[1]["score"] if item[1]["score"] is not None else 0
    )
))
    return sorted_players



if __name__ == "__main__":
    socketio.run(app,debug=False)
    