from django.contrib import admin

class AdminSite(admin.AdminSite):
    enable_nav_sidebar = False