from django.core.management.base import BaseCommand
from pokebase import models

class Command(BaseCommand):
    help = 'Delete unresolvable hosts'

    def handle(self, *args, **options):

        models.Host.objects.filter(name_resolves=False).delete()