"""
This file was generated with the custommenu management command, it contains
the classes for the admin menu, you can customize this class as you want.

To activate your custom menu add the following to your settings.py::
    ADMIN_TOOLS_MENU = 'pokedex.menu.CustomMenu'
"""

from django.urls import reverse
from admin_tools.menu import items, Menu

class KantoBaseMenu(Menu):
    """
    Custom Menu for pokedex admin site.
    """
    def __init__(self, **kwargs):
        Menu.__init__(self, **kwargs)
        self.children += [
            items.MenuItem('Dashboard', reverse('admin:index')),
            items.Bookmarks(),
            items.ModelList(
                'BB Programs',
                models=('bbprograms.*',)
            ),
            items.ModelList(
                'Base',
                models=('pokebase.*',)
            ),
        ]

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        return super(KantoBaseMenu, self).init_with_context(context)
