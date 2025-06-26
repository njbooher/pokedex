from django.views.generic.edit import FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from pokeoauth import forms

class ImportOAuthClient(PermissionRequiredMixin, FormView):
    form_class = forms.OAuthClientImportForm
    permission_required = 'pokeoauth.change_oauthclient'
    template_name = "admin/pokeoauth/import_oauth_clients.html"

    def get_success_url(self):
        return '/admin/pokeoauth/oauthclient/'

    def form_valid(self, form):
        clients = form.cleaned_data['clients']
        results = form.import_clients(clients)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Manually plugging in context variables needed
        # to display necessary links and blocks in the
        # django admin.
        context['title'] = 'Import OAuth Clients'
        #context['has_permission'] = True

        return context