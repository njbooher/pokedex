from django.apps import AppConfig
import os

class BBProgramsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bbprograms'
    verbose_name = 'Bug Bounty Programs'
    hackerone_api_username = os.getenv('BBPROGRAMS_HACKERONE_API_USERNAME')
    hackerone_api_key = os.getenv('BBPROGRAMS_HACKERONE_API_KEY')