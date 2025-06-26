from django.apps import apps

def api_key(request):
    return {'pokedex_api_key': apps.get_app_config('pokebase').api_key}