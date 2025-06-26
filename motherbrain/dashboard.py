from django.urls import reverse
from admin_tools.dashboard import modules, Dashboard, AppIndexDashboard
from admin_tools.utils import get_admin_site_name

from kanto.dashboard import KantoBaseAppIndexDashboard, KantoBaseIndexDashboard

class MotherbrainIndexDashboard(KantoBaseIndexDashboard):
    pass

class MotherbrainAppIndexDashboard(KantoBaseAppIndexDashboard):
    pass