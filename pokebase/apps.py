from django.apps import AppConfig
import os

class PokebaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pokebase'
    api_key = os.getenv('POKEDEX_API_KEY')