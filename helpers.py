import requests
import random

BASE_URL = "https://pokeapi.co/api/v2/pokemon-species"
IMG_URL = "https://pokeapi.co/api/v2/pokemon"

def get_pokemon_info(name):
    """Get all the info for a pokemon"""
    url = f"{BASE_URL}/{name}"
    response = requests.get(url, timeout = 5)
    if response.status_code == 200:
        pokemon_data = response.json()
        return pokemon_data
    else:
        return None

def get_pokemon_count():
    """Get the number of pokemon currently in the series"""
    poke_Response = requests.get(BASE_URL, timeout = 5)
    if poke_Response.status_code == 200:
        poke_length = poke_Response.json()

    else:
        poke_length = None

    if not poke_length:
        return None

    pokemonCount = int(poke_length["count"])
    return pokemonCount

def get_random_pokemon():
    """Get a random pokemon number from 1 to the number of pokemon"""
    pokemon_count = get_pokemon_count()

    if not pokemon_count:
        return None
    return random.randint(1, pokemon_count)


def get_pokemon_sprite(name):
    """Get the link to the main artwork for a specific pokemon using the PokeApi"""
    url = f"{IMG_URL}/{name}"
    response = requests.get(url, timeout = 5)
    if response.status_code == 200:
        pokemon_data = response.json()
        return pokemon_data["sprites"]["other"]["official-artwork"]["front_default"]
    else:
        return None

def calculate_points(guess, answer):
    """Calculate how far everyones guesses were this round"""
    return abs(int(guess) - int(answer))
