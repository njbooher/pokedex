from django.views.generic.edit import FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from pokedex import forms, models

class ImportRouteParams(PermissionRequiredMixin, FormView):
    form_class = forms.RouteParamImportForm
    permission_required = 'pokedex.change_route'
    template_name = "admin/pokedex/import_route_params.html"

    def get_success_url(self):
        return '/admin/pokedex/route/{}'.format(self.kwargs['routeid'])

    def form_valid(self, form):
        route = models.Route.objects.get(id=self.kwargs['routeid'])
        params = form.cleaned_data['param_string']
        results = form.import_params(route, params)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Manually plugging in context variables needed
        # to display necessary links and blocks in the
        # django admin.
        context['title'] = 'Import Params'
        #context['has_permission'] = True

        return context

class ImportAssetDeployments(PermissionRequiredMixin, FormView):
    form_class = forms.AssetDeploymentImportForm
    permission_required = 'pokedex.change_asset'
    template_name = "admin/pokedex/import_asset_deployments.html"

    def get_success_url(self):
        return '/admin/pokedex/asset/{}'.format(self.kwargs['assetid'])

    def form_valid(self, form):
        asset = models.Asset.objects.get(id=self.kwargs['assetid'])
        deployments = form.cleaned_data['deployments']
        results = form.import_deployments(asset, deployments)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Manually plugging in context variables needed
        # to display necessary links and blocks in the
        # django admin.
        context['title'] = 'Import Deployments'
        #context['has_permission'] = True

        return context

class BulkAddParamToRoute(PermissionRequiredMixin, FormView):
    form_class = forms.BulkParameterForm
    permission_required = 'pokedex.change_parameter'
    template_name = "admin/pokedex/bulk_add_param.html"
    success_url = '/admin/pokedex/route/'

    def form_valid(self, form):
        routeids = map(int, self.request.GET.get('routeids', '').split(','))
        param = form.save(commit=False)
        for routeid in routeids:
            route = models.Route.objects.get(id=routeid)
            param.pk = None
            param.id = None
            param.route = route
            param.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Manually plugging in context variables needed
        # to display necessary links and blocks in the
        # django admin.
        context['title'] = 'Bulk Add Parameter'
        #context['has_permission'] = True

        return context


