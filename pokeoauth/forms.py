from django import forms
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelect
from . import models

class OAuthClientImportForm(forms.Form):

    clients = forms.CharField(widget=forms.Textarea)

    def clean_clients(self):

        self.cleaned_data['clients'] = self.cleaned_data['clients'].strip()

        parsed_data = []

        try:
            for l in self.cleaned_data['clients'].split("\n"):
                l = l.strip().split("\t")
                print(l)
                if len(l) > 1:
                    parsed_data.append((l[0], l[1]))
                else:
                    parsed_data.append((l[0], ''))
        except ValueError:
            raise ValidationError(
                'Could not parse clients',
                code='invalid',
            )

        self.cleaned_data['clients'] = parsed_data

        return self.cleaned_data['clients']

    def import_clients(self, clients):

        for client_id, client_secret in clients:

            try:

                try:
                    client = models.OAuthClient.objects.get(client_id=client_id)
                except models.OAuthClient.DoesNotExist:
                    client = models.OAuthClient()
                    client.name = "placeholder"
                    client.client_id = client_id
                    client.internal = False
                    client.native = False
                if len(client_secret) > 0:
                    client.secret = client_secret
                client.save()
            except IntegrityError:
                pass

class OAuthClientPermissionsGrantResourceAdminInlineForm(forms.ModelForm):
    class Meta:
        widgets = {
            'resource': AutocompleteSelect(
                models.OAuthPermissionsGrant._meta.get_field('resource'),
                admin.site,
                attrs={
                    'data-dropdown-auto-width': 'true',
                    'data-width': 'auto'
                }
            ),
        }
