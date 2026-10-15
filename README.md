# DexGuess.io
A real-time multiplayer Pokémon guessing game built using Python, Flask, JavaScript, HTML and CSS. This is a final project for the Harvard CS50 Course. The web-application is currently available to be played at:  [https://pokedexguess-production.up.railway.app/](https://pokedexguess-production.up.railway.app/)

<img width="454" height="528" alt="DexGuess Screenshot" src="https://github.com/user-attachments/assets/ef82bdb3-a7ce-4dc1-a35e-e06c7695d0e4" />

## About the Project

DexGuess.io is a browser-based multiplayer guessing game inspired by the Pokémon franchise. The objective is simple: players are given a randomly generated Pokédex number (a unique ID value given to every Pokemon in the series) and must guess which Pokémon corresponds to that number.

Players can create private rooms or join existing ones using a four-digit room code. Each player submits their guess, and once everyone is ready, the host can end the round to reveal the correct Pokémon.

Points are calculated based on the numerical difference between the guessed Pokémon's Pokédex number and the correct answer. The closer the guess, the fewer points the player receives. Scores accumulate across rounds, and the player with the lowest total score is winning.

The game also features a live leaderboard, host-controlled rounds, Pokémon artwork and the ability to reroll Pokémon between or during rounds.

## How I Made It

DexGuess.io was developed as my final project for Harvard's CS50 Introduction to Computer Science course, allowing me to apply the programming concepts I had learned to a complete web application.

I chose Python and Flask for the backend, which handles room creation, player sessions, Pokémon selection, guess validation and score calculations. The application integrates PokéAPI, a publicly available REST API, to retrieve Pokémon information and artwork.

The frontend was built using HTML, CSS and JavaScript, with Flask's Jinja templating engine used to generate dynamic pages. JavaScript Fetch requests allow parts of the interface to update without requiring a complete page reload.

One of the more challenging aspects was implementing real-time multiplayer functionality. Initially, the application relied on traditional HTTP requests, but I wanted players to see changes immediately without refreshing their browsers.

To achieve this, I incorporated Flask-SocketIO, which enables event-driven communication between the server and connected clients. This allows player lists, submitted guesses and game states to remain synchronised across multiple devices.

Another challenge involved websockets disconnecting when navigating between different pages, this was minimised by reducing the site to a single page architecture with sub-pages changing depending on the state value supplied by the backend.

Finally, I deployed the application using Railway, gaining practical experience with cloud hosting, environment variables, dependency management and troubleshooting deployment issues.

## AI use

Throughout development, I used AI as a digital tutor, primarily to explain unfamiliar concepts, discuss implementation approaches and help troubleshoot errors.

Rather than using AI to generate or copy code, I focused on understanding the underlying concepts and writing the implementation myself. This allowed me to develop my problem-solving abilities while learning technologies beyond the original CS50 curriculum, particularly WebSockets, asynchronous JavaScript and deployment.

*DexGuess.io is an unofficial fan project and is not affiliated with or endorsed by Nintendo, Game Freak or The Pokémon Company*
