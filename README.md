# pokedex

note taking app for bug bounty

## dev environment set up

create a file set_env.sh in this directory like the following:

```bash
export DJANGO_SETTINGS_MODULE='motherbrain.settings'
export POKEDEX_SECRET_KEY='randomstringgoeshere'
export POKEDEX_DEBUG_ACTIVE='IM_REALLY_SURE_THIS_ISNT_PRODUCTION'
export POKEDEX_DB_FILE='db.sqlite3'
# used to sync reports from hackerone
export BBPROGRAMS_HACKERONE_API_USERNAME=''
export BBPROGRAMS_HACKERONE_API_KEY=''
# used by frontend routes in pokedex
export POKEDEX_API_KEY=''
# used to send slack notifications
export POKEDEX_SLACK_URL=''
```

then run:

```bash
python3 -mvenv env
. env/bin/activate
. set_env.sh
pip install -r requirements.txt
python manage.py migrate
echo 'from django.contrib.auth.models import User; User.objects.create_superuser(username="admin", password="password", email="asdf@localhost")' | python manage.py shell
python manage.py runserver
```

