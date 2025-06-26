"""pokedex URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from .views import api, admin

urlpatterns = [
    path('api/hosts/import', api.HostsImportView.as_view(), name='api_hosts_import'),
    path('api/hosts.json', api.HostsExportView.as_view(), name='api_hosts_export'),
    path('api/notification/create', api.CreateNotificationView.as_view(), name='api_notification_create'),
    path('admin/pokedex/host/import', admin.ImportHosts.as_view(), name='import_hosts'),
]