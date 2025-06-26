from django.urls import reverse
from admin_tools.menu import items, Menu

from kanto.menu import KantoBaseMenu

class MotherbrainMenu(KantoBaseMenu):
    def __init__(self, **kwargs):
        KantoBaseMenu.__init__(self, **kwargs)
        self.children += [
            items.ModelList(
                'Cloud',
                models=('pokecloud.*',)
            ),
            items.ModelList(
                'Pokedex',
                models=('pokedex.*',)
            ),
            items.ModelList(
                'OAuth',
                models=('pokeoauth.*',)
            ),
        ]