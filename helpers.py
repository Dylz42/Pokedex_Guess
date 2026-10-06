import requests
import random

BASE_URL = "https://pokeapi.co/api/v2/pokemon-species/"
POKEMON_COUNT = 0

def get_pokemon_info(name):
    url = f"{BASE_URL}/{name}"
    response = requests.get(url, timeout = 5)
    if response.status_code == 200:
        pokemon_data = response.json()
        return pokemon_data
    else:
        return None

def set_pokemon_count():
    poke_Response = requests.get(BASE_URL, timeout = 5)
    if poke_Response.status_code == 200:
        poke_length = poke_Response.json()

    else:
        poke_length = None

    global POKEMON_COUNT
    POKEMON_COUNT = int(poke_length["count"])

def get_random_pokemon():
    return random.randint(1, POKEMON_COUNT)

def guess_pokemon(pokemon_guess, pokemon_answer):
    if get_pokemon_info(pokemon_guess) != None:
        guess_info =  get_pokemon_info(pokemon_guess)['name']

    else:
        return False

    answer_info = get_pokemon_info(pokemon_answer)['name']

    return guess_info == answer_info



def generate_hints(name):
    pokemon_data = get_pokemon_info(name)
    pokemon_hints = [pokemon_data['generation']['name'], pokemon_data['habitat']['name']]
    return pokemon_hints


