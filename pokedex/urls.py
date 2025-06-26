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

from .views import api, admin, frontend

urlpatterns = [
    path('routes/<asset>', frontend.RoutesView.as_view()),
    path('api/routes/<asset>.json', api.RoutesExportView.as_view(), name='api_routes_export'),
    path('api/routes/<asset>/importbyslug', api.RoutesBySlugImportView.as_view(), name='api_routes_importbyslug'),
    path('api/routes/<asset>/importbycontrollermethod', api.RoutesByControllerMethodImportView.as_view(), name='api_routes_importbycontrollermethod'),
    path('admin/pokedex/route/<int:routeid>/importparams', admin.ImportRouteParams.as_view(), name='import_route_params'),
    path('admin/pokedex/asset/<int:assetid>/importdeployments', admin.ImportAssetDeployments.as_view(), name='import_asset_deployments'),
    path('admin/pokedex/route/bulkaddparam', admin.BulkAddParamToRoute.as_view(), name='bulk_add_params'),
    path('api/deployments.json', api.DeploymentsExportView.as_view(), name='api_deployments_export'),
    path('api/interfaces.json', api.InterfacesExportView.as_view(), name='api_interfaces_export'),
    path('api/methods.json', api.MethodsExportView.as_view(), name='api_methods_export'),
    path('api/slugs.json', api.SlugsExportView.as_view(), name='api_slugs_export'),
    path('api/parameters.json', api.ParametersExportView.as_view(), name='api_parameters_export'),
    path('api/domains/inscope.json', api.DomainsInScopeExportView.as_view(), name='api_domains_inscope_export'),
    # path('api/domains/outofscope.json', api.DomainsOutOfScopeExportView.as_view(), name='api_domains_outofscope_export'),
]
