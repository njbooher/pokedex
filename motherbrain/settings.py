from kanto.base_settings import *

INSTALLED_APPS += [
    'motherbrain',
    'pokecloud.apps.PokecloudConfig',
    'pokeoauth.apps.PokeoauthConfig'
]

ROOT_URLCONF = 'motherbrain.urls'

ALLOWED_HOSTS += [
    'localhost',
    'localhost:8000',
    '127.0.0.1',
    '127.0.0.1:8000'
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000"
]

OPENSHIFT_ENABLED = False
OPENSHIFT_NAMESPACE = 'motherbrain'

POKEDEX_NEW_HOST_NOTIFICATIONS = False
POKEDEX_STATUS_CODE_CHANGE_NOTIFICATIONS = False
POKEDEX_NEW_BUCKET_NOTIFICATIONS = False

# Admin site

ADMIN_TOOLS_MENU = 'motherbrain.menu.MotherbrainMenu'
ADMIN_TOOLS_INDEX_DASHBOARD = 'motherbrain.dashboard.MotherbrainIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'motherbrain.dashboard.MotherbrainAppIndexDashboard'
