from django.views.generic.edit import FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from pokebase import forms

class ImportHosts(PermissionRequiredMixin, FormView):
    form_class = forms.HostImportForm
    permission_required = 'pokebase.change_host'
    template_name = "admin/pokebase/import_hosts.html"

    def get_success_url(self):
        return '/admin/pokebase/host/'

    def form_valid(self, form):
        hosts = form.cleaned_data['hosts']
        in_scope = form.cleaned_data['in_scope']
        results = form.import_hosts(hosts, in_scope)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Manually plugging in context variables needed
        # to display necessary links and blocks in the
        # django admin.
        context['title'] = 'Import Hosts'
        #context['has_permission'] = True

        return context