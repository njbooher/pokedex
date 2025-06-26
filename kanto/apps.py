from django.contrib.admin.apps import AdminConfig

class AdminConfig(AdminConfig):
    default_site = 'kanto.admin.AdminSite'