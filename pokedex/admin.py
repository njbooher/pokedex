from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
import django.forms
import django.db.models
from django.http import HttpResponseRedirect
from django.db.models import Count
from . import forms, models
import datetime
from bbprograms import scopeutils
from pokebase.admin import PokedexModelAdmin, PokedexReadonlyTabularInline, PokedexTabularInline, VulnerabilityAdmin as BaseVulnerabilityAdmin
# Register your models here.

class ResponseContentTypeFilter(admin.AllValuesFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        parent_model, reverse_path = admin.utils.reverse_field_path(model, field_path)
        # Obey parent ModelAdmin queryset when deciding which options to show
        if model == parent_model:
            queryset = model_admin.get_queryset(request)
        else:
            queryset = parent_model._default_manager.all()
        self.lookup_choices = queryset.filter(response_message_type__regex=r'^[^A-Z].*$').distinct().order_by(field.name).values_list(field.name, flat=True)


# helpers


# real model admins

# class DeploymentHostTabularInline(PokedexTabularInline):

#     form = forms.DeploymentHostAdminInlineForm
#     model = models.Deployment
#     raw_id_fields = ('host',)
#     fields = ('asset', 'protocol', 'base_path', 'environment', 'quirks', 'notes')
#     autocomplete_fields = ['quirks']
#     extra = 0
#     show_change_link = True



class EnvironmentAdmin(PokedexModelAdmin):
    search_fields = ['name']
    autocomplete_fields = ['quirks']
    list_display = ['name', 'short_notes']

class DeploymentAssetTabularInline(PokedexTabularInline):

    form = forms.DeploymentAssetAdminInlineForm
    model = models.Deployment
    raw_id_fields = ('asset',)
    fields = ('protocol', 'host', 'get_host_reachable', 'base_path', 'environment', 'quirks', 'notes')
    autocomplete_fields = ['quirks']
    readonly_fields = ['get_host_reachable']
    extra = 0
    show_change_link = True

    def get_host_reachable(self, obj):
        return self._boolean_icon(obj.host.reachable)

    get_host_reachable.admin_order_field  = 'host__reachable'  #Allows column order sorting
    get_host_reachable.short_description = 'Reachable'  #Renames column head

class AssetAdmin(PokedexModelAdmin):

    inlines = [
        DeploymentAssetTabularInline
    ]

    def get_queryset(self, request):
        qs = super(AssetAdmin, self).get_queryset(request)
        qs = qs.prefetch_related('quirks')
        qs = qs.annotate(deployments_count=(Count('deployment', distinct=True)))
        qs = qs.annotate(interfaces_count=(Count('interface', distinct=True)))
        qs = qs.annotate(vulnerabilities_count=(Count('vulnerability', distinct=True)))
        return qs

    def get_quirks(self, obj):
        return ",".join([p.tag for p in obj.quirks.all()])
    get_quirks.short_description = "Quirks"

    def mark_s3(self, request, queryset):
        queryset.update(type=models.Asset.AssetType.S3)
    mark_s3.short_description = "Mark selected assets as s3 buckets"

    def mark_microservice(self, request, queryset):
        queryset.update(type=models.Asset.AssetType.MICROSERVICE)
    mark_microservice.short_description = "Mark selected deployments as microservices"

    def mark_site(self, request, queryset):
        queryset.update(type=models.Asset.AssetType.SITE)
    mark_site.short_description = "Mark selected deployments as sites"

    def deployment_count(self, obj):
        return obj.deployments_count
    deployment_count.short_description = "# Deployments"
    deployment_count.admin_order_field = 'deployments_count'

    def interface_count(self, obj):
        return obj.interfaces_count
    interface_count.short_description = "# Interfaces"
    interface_count.admin_order_field = 'interfaces_count'

    def vulnerability_count(self, obj):
        return obj.vulnerabilities_count
    vulnerability_count.short_description = "# Vulns"
    vulnerability_count.admin_order_field = 'vulnerabilities_count'

    change_form_template = 'admin/pokedex/asset_change_form.html'

    autocomplete_fields = ['quirks']
    search_fields = ['name']

    ordering = ['name']
    list_display = ['name', 'type', 'deployment_count', 'interface_count', 'vulnerability_count', 'get_quirks', 'short_notes']
    list_filter = [
        'type',
        ('quirks', admin.RelatedOnlyFieldListFilter),
        'deployment__host__reachable',
    ]
    actions = ['mark_s3', 'mark_microservice', 'mark_site']

    save_as = True

class DeploymentAdmin(PokedexModelAdmin):

    def mark_prod(self, request, queryset):
        queryset.update(environment=models.Environment.objects.get(name='prod'))
    mark_prod.short_description = "Mark selected deployments as prod environment"

    def mark_stage(self, request, queryset):
        queryset.update(environment=models.Environment.objects.get(name='stage'))
    mark_stage.short_description = "Mark selected deployments as stage environment"

    def get_host_aliased_by(self, obj):
        return format_html("<br />".join([p.name for p in obj.host.aliases.all()]))
    get_host_aliased_by.short_description = "Host Aliased By"

    def get_host_alias_to(self, obj):
        return obj.host.alias_to
    get_host_alias_to.short_description = "Host Alias To"

    autocomplete_fields = ['asset','environment','quirks']
    list_display = ['asset','protocol', 'host', 'get_host_aliased_by', 'get_host_alias_to', 'base_path', 'environment', 'short_notes']
    list_filter = [
        'protocol',
        'environment',
        #('asset', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['asset__name', 'base_path', 'host__name', 'notes']
    actions = ['mark_prod', 'mark_stage']
    ordering = ['asset__name']

class InterfaceAdmin(PokedexModelAdmin):

    def get_queryset(self, request):
        qs = super(InterfaceAdmin, self).get_queryset(request)
        qs = qs.select_related('asset')
        qs = qs.annotate(methods_count=(Count('method', distinct=True)))
        qs = qs.annotate(vulnerabilities_count=(Count('vulnerability', distinct=True)))
        return qs

    def get_asset(self, obj):
        return obj.asset.name
    get_asset.admin_order_field  = 'asset__name'  #Allows column order sorting
    get_asset.short_description = 'Asset'  #Renames column head

    def method_count(self, obj):
        return format_html('<a href="{}?q={}">{}</a>', reverse('admin:pokedex_method_changelist'), obj.name, obj.methods_count)
    method_count.short_description = "# Methods"
    method_count.admin_order_field = 'methods_count'

    def vulnerability_count(self, obj):
        return obj.vulnerabilities_count
    vulnerability_count.short_description = "# Vulns"
    vulnerability_count.admin_order_field = 'vulnerabilities_count'

    def reset_last_scanned(self, request, queryset):
        queryset.update(last_scanned_for_methods=datetime.datetime(1970, 1, 1, 0, 0, 1))
    reset_last_scanned.short_description = "Queue for method scanning"

    autocomplete_fields = ['quirks']
    search_fields = ['asset__name', 'name']

    ordering = ['asset', 'name']
    list_display = ['get_asset', 'name', 'method_count', 'last_scanned_for_methods', 'last_scanned_for_templates', 'vulnerability_count', 'short_notes']
    list_filter = ['asset']
    actions = ['reset_last_scanned']

class MethodAdmin(PokedexModelAdmin):

    def get_queryset(self, request):
        qs = super(MethodAdmin, self).get_queryset(request)
        qs = qs.select_related('interface__asset', 'interface')
        qs = qs.annotate(routes_count=(Count('route', distinct=True)))
        qs = qs.annotate(vulnerabilities_count=(Count('vulnerability', distinct=True)))
        return qs

    def get_asset(self, obj):
        return obj.interface.asset.name
    get_asset.admin_order_field  = 'interface__asset__name'  #Allows column order sorting
    get_asset.short_description = 'Asset'  #Renames column head

    def get_interface(self, obj):
        return obj.interface.name
    get_interface.admin_order_field  = 'interface__name'  #Allows column order sorting
    get_interface.short_description = 'Interface'  #Renames column head

    def route_count(self, obj):
        return obj.routes_count
    route_count.short_description = "# Routes"
    route_count.admin_order_field = 'routes_count'

    def vulnerability_count(self, obj):
        return obj.vulnerabilities_count
    vulnerability_count.short_description = "# Vulns"
    vulnerability_count.admin_order_field = 'vulnerabilities_count'

    autocomplete_fields = ['interface', 'quirks']
    search_fields = ['interface__asset__name', 'interface__name', 'name']

    ordering = ['interface__asset', 'interface', 'name']
    list_display = ['get_asset', 'get_interface', 'name', 'route_count', 'vulnerability_count', 'short_notes']
    list_filter = ['interface__asset']

class ParameterTabularInline(PokedexTabularInline):
    model = models.Parameter
    fields = ['name','route','location','value_encoding','param_type','message_type','repeated','required','quirks','notes']
    raw_id_fields = ('route',)
    autocomplete_fields = ['quirks']
    extra = 0
    ordering = ['location', 'value_encoding', 'name']
    show_change_link = True

class VulnerabilityRouteTabularInline(PokedexReadonlyTabularInline):
    exclude = ['graphql_type', 'graphql_field', 'graphql_arg']
    model = models.Vulnerability
    extra = 0
    show_change_link = True

class RouteAdmin(PokedexModelAdmin):
    inlines = [
        #RouteGraphQLFieldTabularInline,
        VulnerabilityRouteTabularInline,
        ParameterTabularInline
    ]

    def get_queryset(self, request):
        qs = super(RouteAdmin, self).get_queryset(request)
        qs = qs.select_related('method__interface__asset', 'method__interface', 'method')
        qs = qs.annotate(parameters_count=(Count('parameter', distinct=True)))
        qs = qs.annotate(parameters_with_notes_count=(Count('parameter', distinct=True, filter=~django.db.models.Q(parameter__notes__exact=''))))
        qs = qs.annotate(vulnerabilities_count=(Count('vulnerability', distinct=True)))
        qs = qs.annotate(quirks_count=(Count('quirks', distinct=True)))
        return qs

    def get_asset(self, obj):
        return obj.method.interface.asset.name
    get_asset.admin_order_field  = 'method__interface__asset__name'  #Allows column order sorting
    get_asset.short_description = 'Asset'  #Renames column head

    def get_interface(self, obj):
        return format_html('<a href="{}?q={}">{}</a>', reverse('admin:pokedex_route_changelist'), obj.method.interface.name, obj.method.interface.name)
    get_interface.admin_order_field  = 'method__interface__name'  #Allows column order sorting
    get_interface.short_description = 'Interface'  #Renames column head

    def get_method(self, obj):
        return obj.method.name
    get_method.admin_order_field  = 'method__name'  #Allows column order sorting
    get_method.short_description = 'Method'  #Renames column head

    def parameter_count(self, obj):
        return obj.parameters_count
    parameter_count.short_description = "# Params"
    parameter_count.admin_order_field = 'parameters_count'

    def parameters_with_notes_count(self, obj):
        return obj.parameters_with_notes_count
    parameters_with_notes_count.short_description = "# Params w/ Notes"
    parameters_with_notes_count.admin_order_field = 'parameters_with_notes_count'

    def vulnerability_count(self, obj):
        return obj.vulnerabilities_count
    vulnerability_count.short_description = "# Vulns"
    vulnerability_count.admin_order_field = 'vulnerabilities_count'

    def quirk_count(self, obj):
        return obj.quirks_count
    quirk_count.short_description = "# Quirks"
    quirk_count.admin_order_field = 'quirks_count'

    def mark_usable(self, request, queryset):
        queryset.update(usable=True)
    mark_usable.short_description = "Mark selected routes as usable"

    def mark_unusable(self, request, queryset):
        queryset.update(usable=False)
    mark_unusable.short_description = "Mark selected routes as unusable"

    def mark_get(self, request, queryset):
        queryset.update(http_method=models.Route.HTTPMethod['GET'])
    mark_get.short_description = "Mark selected routes as GET"

    def mark_post(self, request, queryset):
        queryset.update(http_method=models.Route.HTTPMethod['POST'])
    mark_post.short_description = "Mark selected routes as POST"

    def bulk_add_param(self, request, queryset):
        selected = queryset.values_list('pk', flat=True)
        return HttpResponseRedirect("/admin/pokedex/route/bulkaddparam?routeids={}".format(','.join(str(pk) for pk in selected)))
    bulk_add_param.short_description = "Add parameter to selected routes"

    def reset_last_scanned(self, request, queryset):
        queryset.update(last_scanned=datetime.datetime(1970, 1, 1, 0, 0, 1))
    reset_last_scanned.short_description = "Queue for scanning"

    change_form_template = 'admin/pokedex/route_change_form.html'
    autocomplete_fields = ['method', 'quirks']

    list_display = ['id', 'get_asset', 'get_interface', 'get_method', 'slug', 'http_method', 'action', 'usable', 'parameter_count', 'parameters_with_notes_count', 'vulnerability_count', 'quirk_count', 'response_message_type', 'short_notes']

    list_filter = [
        ('method__interface__asset', admin.RelatedOnlyFieldListFilter),
        'http_method',
        'usable',
        'source',
        ('response_message_type', ResponseContentTypeFilter),
        ('notes', admin.EmptyFieldListFilter),
        ('action', admin.EmptyFieldListFilter),
    ]

    fields = ['get_asset', 'get_interface', 'method', 'slug', 'http_method', 'action', 'required_permission', 'usable', 'response_message_type', 'source', 'quirks', 'notes', 'scan_results']
    search_fields = ['method__interface__asset__name', 'method__interface__name', 'method__name', 'http_method', 'action', 'slug','notes', 'scan_results']
    readonly_fields = ['get_asset', 'get_interface', 'get_method']

    ordering = ['method__interface', 'method']

    actions = ['mark_usable', 'mark_unusable', 'mark_get', 'mark_post', 'bulk_add_param', 'reset_last_scanned']

    save_as = True

class ParameterAdmin(PokedexModelAdmin):

    def get_asset(self, obj):
        return obj.route.method.interface.asset.name
    get_asset.admin_order_field  = 'route__method__interface__asset__name'  #Allows column order sorting
    get_asset.short_description = 'Asset'  #Renames column head

    autocomplete_fields = ['quirks']
    search_fields = ['name', 'notes', 'route__slug']
    raw_id_fields = ('route',)
    list_display = ['get_asset', 'route', 'name', 'location', 'param_type', 'message_type', 'repeated', 'required', 'value_encoding', 'short_notes']
    list_filter = [
        ('route__method__interface__asset', admin.RelatedOnlyFieldListFilter),
        'location',
        'param_type',
        'value_encoding',
        ('notes', admin.EmptyFieldListFilter),
        'route__http_method',
        'route__usable'
    ]
    ordering = ['route__method__interface__asset__name','route', 'name']

class VulnerabilityAdmin(BaseVulnerabilityAdmin):

    def get_host_or_asset(self, obj):
        value = ""
        if obj.host is not None:
            value = obj.host.name
        elif obj.asset is not None:
            value = obj.asset.name
        return value
    get_host_or_asset.short_description = 'Host / Asset'  #Renames column head

    form = forms.VulnerabilityAdminForm
    autocomplete_fields = ['host', 'asset', 'weakness']

    list_display = ['id', 'get_host_or_asset','interface', 'method','parameter','weakness','confirmation_level','severity','reportid','fixed','false_alarm','short_description']