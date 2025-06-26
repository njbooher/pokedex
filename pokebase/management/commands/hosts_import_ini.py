from django.core.management.base import BaseCommand
import argparse
import json
import configparser

from pokedex import models

class Command(BaseCommand):
    help = 'Import hostnames from ini file values'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('FILE', type=argparse.FileType('r'))
        parser.add_argument('pattern')

    def clean_hostname(self, name):
        if '://' in name:
            name = name[name.find('://')+3:]
        name = name.split('/')[0].split(':')[0].strip('"')
        return name

    def handle(self, *args, **options):
        config = configparser.ConfigParser()
        config.read_file(options['FILE'])
        for section in config:
            for key in config[section]:
                if options['pattern'] in config[section][key]:
                    host, created = models.Host.objects.get_or_create(name=self.clean_hostname(config[section][key]))

