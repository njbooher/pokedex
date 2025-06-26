from django import forms
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelect
import json
import urllib
from . import models
from pokebase import models as pbmodels

class RouteParamImportForm(forms.Form):

    param_string = forms.CharField(widget=forms.Textarea)

    def clean_param_string(self):

        self.cleaned_data['param_string'] = self.cleaned_data['param_string'].strip()

        try:
            parsed_data = json.loads(self.cleaned_data['param_string'])

        except json.JSONDecodeError:
            try:
                parsed_data = {key: value for (key, value) in urllib.parse.parse_qsl(self.cleaned_data['param_string'], keep_blank_values=True, strict_parsing=True)}
            except ValueError:
                raise ValidationError(
                    'Could not parse string as json or query params',
                    code='invalid',
                )

        data = {}

        for key in parsed_data:
            data[key] = type(parsed_data[key])

        self.cleaned_data['param_string'] = data

        return self.cleaned_data['param_string']

    def import_params(self, route, params):

        if route.http_method == models.Route.HTTPMethod['POST']:
            param_location = models.Parameter.Location['BODY']
        else:
            param_location = models.Parameter.Location['QUERY']

        for param_name, param_type in params.items():
            if param_type == list or param_type == dict:
                param_type = models.Parameter.ParamType['ARRAY']
            elif param_type == int:
                param_type = models.Parameter.ParamType['INT']
            else:
                param_type = models.Parameter.ParamType['UNKNOWN']

            try:
                param = models.Parameter()
                param.route = route
                param.location = param_location
                param.value_encoding = models.Parameter.ValueEncoding['URL']
                param.param_type = param_type
                param.name = param_name
                param.notes = ""
                param.save()
            except IntegrityError:
                pass

class AssetDeploymentImportForm(forms.Form):

    deployments = forms.CharField(widget=forms.Textarea)

    def clean_deployments(self):

        self.cleaned_data['deployments'] = self.cleaned_data['deployments'].strip()

        parsed_data = []

        try:
            for l in self.cleaned_data['deployments'].split():
                u = urllib.parse.urlparse(l.strip())
                parsed_data.append((u.scheme, u.netloc, u.path))
        except ValueError:
            raise ValidationError(
                'Could not parse deployments',
                code='invalid',
            )

        self.cleaned_data['deployments'] = parsed_data

        return self.cleaned_data['deployments']

    def import_deployments(self, asset, deployments):

        for protocol, hostname, path in deployments:

            try:
                deployment = models.Deployment()
                deployment.asset = asset
                deployment.protocol = models.Deployment.Protocol[protocol.upper()]
                deployment.host, created = pbmodels.Host.objects.get_or_create(name=hostname)
                deployment.base_path = path
                if "-stage" in hostname:
                    deployment.environment = models.Environment.objects.get(name="stage")
                elif "-lt" in hostname:
                    deployment.environment = models.Environment.objects.get(name="lt")
                elif "-loadtest" in hostname:
                    deployment.environment = models.Environment.objects.get(name="lt")
                elif "-prod" in hostname:
                    deployment.environment = models.Environment.objects.get(name="prod")
                elif "-lt" in hostname:
                    deployment.environment = models.Environment.objects.get(name="lt")
                elif "-ci" in hostname:
                    deployment.environment = models.Environment.objects.get(name="ci")
                elif "-gamedev" in hostname:
                    deployment.environment = models.Environment.objects.get(name="gamedev")
                deployment.notes = ""
                deployment.save()
            except IntegrityError:
                pass

class BulkParameterForm(forms.ModelForm):

    class Meta:
        model = models.Parameter
        fields = ['location', 'value_encoding', 'param_type', 'name', 'notes']

class VulnerabilityAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self.instance, 'bucket'):
            if hasattr(self.instance, 'asset'):
                self.fields['interface'].queryset = models.Interface.objects.filter(asset=self.instance.asset)
            if hasattr(self.instance, 'interface'):
                self.fields['method'].queryset = models.Method.objects.filter(interface=self.instance.interface)
            if hasattr(self.instance, 'method'):
                self.fields['route'].queryset = models.Route.objects.filter(method=self.instance.method)
            if hasattr(self.instance, 'route'):
                self.fields['parameter'].queryset = models.Parameter.objects.filter(route=self.instance.route)


class DeploymentAssetAdminInlineForm(forms.ModelForm):
    class Meta:
        widgets = {
            'host': AutocompleteSelect(
                models.Deployment._meta.get_field('host'),
                admin.site,
                attrs={
                    'data-dropdown-auto-width': 'true',
                    'data-width': 'auto'
                }
            ),
        }

class DeploymentHostAdminInlineForm(forms.ModelForm):
    class Meta:
        widgets = {
            'asset': AutocompleteSelect(
                models.Deployment._meta.get_field('asset'),
                admin.site,
                attrs={
                    'data-dropdown-auto-width': 'true',
                    'data-width': 'auto'
                }
            ),
        }

