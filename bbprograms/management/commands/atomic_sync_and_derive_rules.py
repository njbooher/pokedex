from django.core import management
from django.core.management.base import BaseCommand
from django.db import transaction

class Command(BaseCommand):
    help = 'Sync data for one team from hackerone api and derive scope rules'

    def add_arguments(self, parser):
        parser.add_argument('PROGRAM', help='program to sync data for')

    def handle(self, *args, **options):
        with transaction.atomic():
            management.call_command('sync_hackerone', program=options['PROGRAM'])
            management.call_command('derive_scope_rules')