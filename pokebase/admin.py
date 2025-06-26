from django.contrib import admin
from django.utils.html import format_html
import django.forms
import django.db.models
from django.db.models import Count
from django.templatetags.static import static
from django.urls import reverse
from . import models, widgets
from bbprograms import scopeutils
from pokedex import models as pdmodels
#import nested_admin
import datetime

# Register your models here.
# Quirks

class PokedexBaseModelAdmin:
    formfield_overrides = {
        django.db.models.JSONField: {'widget': widgets.MonospaceAdminTextareaWidget},
        django.db.models.TextField: {'widget': widgets.MonospaceAdminTextareaWidget},
    }

    # move quirks and notes to the end
    def get_form(self, request, obj=None, **kwargs):
        form = super(PokedexBaseModelAdmin, self).get_form(request, obj, **kwargs)
        if 'quirks' in form.base_fields:
            quirks = form.base_fields.pop('quirks')
            form.base_fields['quirks'] = quirks
        if 'notes' in form.base_fields:
            notes = form.base_fields.pop('notes')
            form.base_fields['notes'] = notes
        return form

    def _boolean_icon(self, field_val):
        icon_url = static('admin/img/icon-%s.svg' % {True: 'yes', False: 'no', None: 'unknown'}[field_val])
        return format_html('<img src="{}" alt="{}">', icon_url, field_val)

class PokedexModelAdmin(PokedexBaseModelAdmin, admin.ModelAdmin):
    pass

# class PokedexNestedModelAdmin(PokedexBaseModelAdmin, nested_admin.NestedModelAdmin):
#     pass

class PokedexBaseInline:
    formfield_overrides = {
        django.db.models.TextField: {'widget': widgets.MonospaceAdminTextareaWidget},
    }

    def _boolean_icon(self, field_val):
        icon_url = static('admin/img/icon-%s.svg' % {True: 'yes', False: 'no', None: 'unknown'}[field_val])
        return format_html('<img src="{}" alt="{}">', icon_url, field_val)

class PokedexTabularInline(PokedexBaseInline, admin.TabularInline):
    pass

# class PokedexNestedStackedInline(PokedexBaseInline, nested_admin.NestedStackedInline):
#     pass

# class PokedexNestedTabularInline(PokedexBaseInline, nested_admin.NestedTabularInline):
#     pass

class PokedexReadonlyTabularInline(PokedexTabularInline):

    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def _boolean_icon(self, field_val):
        icon_url = static('admin/img/icon-%s.svg' % {True: 'yes', False: 'no', None: 'unknown'}[field_val])
        return format_html('<img src="{}" alt="{}">', icon_url, field_val)

class QuirksAssetTabularInline(PokedexReadonlyTabularInline):

    def get_name(self, obj):
        link_url = reverse('admin:pokedex_asset_change', args=(admin.utils.quote(obj.asset.id),), current_app='pokedex')
        return format_html('<a href="{}">{}</a>', link_url, obj.asset.name)
    get_name.short_description = 'Asset'  #Renames column head

    model = pdmodels.Asset.quirks.through
    exclude = ['asset']
    readonly_fields = ['get_name']

class QuirksDeploymentTabularInline(PokedexReadonlyTabularInline):
    model = pdmodels.Deployment.quirks.through

class QuirksHostTabularInline(PokedexReadonlyTabularInline):
    model = models.Host.quirks.through

class QuirksInterfaceTabularInline(PokedexReadonlyTabularInline):
    model = pdmodels.Interface.quirks.through

class QuirksMethodTabularInline(PokedexReadonlyTabularInline):
    model = pdmodels.Method.quirks.through

class QuirksRouteTabularInline(PokedexReadonlyTabularInline):

    def get_asset(self, obj):
        link_url = reverse('admin:pokedex_route_change', args=(admin.utils.quote(obj.route.id),), current_app='pokedex')
        return format_html('<a href="{}">{}</a>', link_url, obj.route.method.interface.asset.name)
    get_asset.short_description = 'Asset'  #Renames column head

    def get_interface(self, obj):
        return obj.route.method.interface.name
    get_interface.short_description = 'Interface'  #Renames column head

    def get_method(self, obj):
        return obj.route.method.name
    get_method.short_description = 'Method'  #Renames column head

    def get_http_method(self, obj):
        return pdmodels.Route.HTTPMethod(obj.route.http_method).label
    get_http_method.short_description = 'HTTP Method'  #Renames column head

    def get_slug(self, obj):
        return obj.route.slug
    get_slug.short_description = 'Slug'  #Renames column head

    def get_action(self, obj):
        return obj.route.action
    get_action.short_description = 'Action'  #Renames column head

    def get_short_notes(self, obj):
        return obj.route.short_notes
    get_short_notes.short_description = 'Notes'  #Renames column head

    model = pdmodels.Route.quirks.through
    exclude = ['route']
    readonly_fields = ['get_asset', 'get_interface', 'get_method', 'get_http_method', 'get_action', 'get_slug', 'get_short_notes']

class QuirksParameterTabularInline(PokedexReadonlyTabularInline):

    def get_asset(self, obj):
        link_url = reverse('admin:pokedex_parameter_change', args=(admin.utils.quote(obj.parameter.id),), current_app='pokedex')
        return format_html('<a href="{}">{}</a>', link_url, obj.parameter.route.method.interface.asset.name)
    get_asset.short_description = 'Asset'  #Renames column head

    def get_route(self, obj):
        return str(obj.parameter.route)
    get_route.short_description = 'Route'  #Renames column head

    def get_name(self, obj):
        return obj.parameter.name
    get_name.short_description = 'Name'  #Renames column head

    def get_location(self, obj):
        return pdmodels.Parameter.Location(obj.parameter.location).label
    get_location.short_description = 'Location'  #Renames column head

    def get_param_type(self, obj):
        return pdmodels.Parameter.ParamType(obj.parameter.param_type).label
    get_param_type.short_description = 'Type'  #Renames column head

    def get_value_encoding(self, obj):
        return pdmodels.Parameter.ValueEncoding(obj.parameter.value_encoding).label
    get_value_encoding.short_description = 'Value Encoding'  #Renames column head

    def get_short_notes(self, obj):
        return obj.parameter.short_notes
    get_short_notes.short_description = 'Notes'  #Renames column head

    model = pdmodels.Parameter.quirks.through
    exclude = ['parameter']
    readonly_fields = ['get_asset', 'get_route', 'get_name', 'get_location', 'get_param_type', 'get_value_encoding', 'get_short_notes']

class QuirkAdmin(PokedexModelAdmin):

    def get_queryset(self, request):
        qs = super(QuirkAdmin, self).get_queryset(request)
        qs = qs.annotate(assets_count=(Count('asset', distinct=True)))
        qs = qs.annotate(deployments_count=(Count('deployment', distinct=True)))
        qs = qs.annotate(hosts_count=(Count('host', distinct=True)))
        qs = qs.annotate(interfaces_count=(Count('interface', distinct=True)))
        qs = qs.annotate(methods_count=(Count('method', distinct=True)))
        qs = qs.annotate(routes_count=(Count('route', distinct=True)))
        qs = qs.annotate(parameters_count=(Count('parameter', distinct=True)))
        return qs

    def asset_count(self, obj):
        return obj.assets_count
    asset_count.short_description = "# Assets"
    asset_count.admin_order_field = 'assets_count'

    def deployment_count(self, obj):
        return obj.deployments_count
    deployment_count.short_description = "# Deployments"
    deployment_count.admin_order_field = 'deployments_count'

    def host_count(self, obj):
        return obj.hosts_count
    host_count.short_description = "# Hosts"
    host_count.admin_order_field = 'hosts_count'

    def interface_count(self, obj):
        return obj.interfaces_count
    interface_count.short_description = "# Interfaces"
    interface_count.admin_order_field = 'interfaces_count'

    def method_count(self, obj):
        return obj.methods_count
    method_count.short_description = "# Methods"
    method_count.admin_order_field = 'methods_count'

    def route_count(self, obj):
        return obj.routes_count
    route_count.short_description = "# Routes"
    route_count.admin_order_field = 'routes_count'

    def parameter_count(self, obj):
        return obj.parameters_count
    parameter_count.short_description = "# Params"
    parameter_count.admin_order_field = 'parameters_count'

    search_fields = ['tag']
    inlines = [
        QuirksParameterTabularInline,
        QuirksRouteTabularInline,
        QuirksAssetTabularInline,
        QuirksDeploymentTabularInline,
        QuirksHostTabularInline,
        QuirksInterfaceTabularInline,
        QuirksMethodTabularInline,
    ]
    ordering = ['tag']

    list_display = ['tag', 'asset_count', 'deployment_count', 'host_count', 'interface_count', 'method_count', 'route_count', 'parameter_count']
    #list_display = ['tag']

class WeaknessAdmin(PokedexModelAdmin):
    search_fields = ['name']
    ordering = ['name']

class VulnerabilityAdmin(PokedexModelAdmin):

    def mark_false_alarm(self, request, queryset):
        queryset.update(false_alarm=True)
    mark_false_alarm.short_description = "Mark selected as false alarm"

    def mark_wip(self, request, queryset):
        queryset.update(confirmation_level=models.Vulnerability.ConfirmationLevel.WIP)
    mark_wip.short_description = "Mark selected as WIP"

    def mark_scanner(self, request, queryset):
        queryset.update(confirmation_level=models.Vulnerability.ConfirmationLevel.SCANNER)
    mark_scanner.short_description = "Mark selected as Scanner"

    def mark_confirmed(self, request, queryset):
        queryset.update(confirmation_level=models.Vulnerability.ConfirmationLevel.CONFIRMED)
    mark_confirmed.short_description = "Mark selected as Confirmed"

    autocomplete_fields = ['weakness']

    list_display = ['id', 'weakness','confirmation_level','severity','reportid','fixed','false_alarm','short_description']
    ordering = ['-id']
    actions = ['mark_false_alarm', 'mark_wip', 'mark_scanner', 'mark_confirmed']

    list_filter = [
        ('reportid', admin.EmptyFieldListFilter),
        'confirmation_level',
        'fixed',
        'false_alarm',
        'severity',
        ('weakness', admin.RelatedOnlyFieldListFilter),
    ]

    save_as = True

class NotificationAdmin(PokedexModelAdmin):
    list_display = ['id', 'created_at', 'notification_type', 'title']
    ordering = ['-id']

    list_filter = [
        'notification_type'
    ]

class HostAliasTabularInline(PokedexTabularInline):

    model = models.Host
    verbose_name = "Alias"
    verbose_name_plural = "Aliases"
    fk_name = 'alias_to'
    raw_id_fields = ('alias_to',)
    fields = ('name', 'reachable', 'quirks', 'notes')
    autocomplete_fields = ['quirks']
    extra = 0
    show_change_link = True

class HostHeadersTabularInline(PokedexTabularInline):
    formfield_overrides = {
        django.db.models.TextField: {'widget': widgets.ShortMonospaceAdminTextareaWidget},
    }

    model = models.Header
    fields = ('name', 'value')
    extra = 0

class HostDNSRecordsTabularInline(PokedexTabularInline):
    formfield_overrides = {
        django.db.models.TextField: {'widget': widgets.ShortMonospaceAdminTextareaWidget},
    }

    model = models.DNSRecord
    fields = ('record_type', 'value')
    extra = 0

class DNSRecordAdmin(PokedexModelAdmin):
    list_display = ['host', 'record_type', 'value']
    list_filter = [
        'record_type',
    ]
    search_fields = ['host__name', 'value']

class HeaderAdmin(PokedexModelAdmin):
    list_display = ['host', 'name', 'value']
    list_filter = [
        #HeaderDomainListFilter,
        'name',
    ]
    search_fields = ['name', 'value']

class TechnologyAdmin(PokedexModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class HostAdmin(PokedexModelAdmin):

    inlines = [
        HostDNSRecordsTabularInline,
        HostHeadersTabularInline,
        HostAliasTabularInline,
        #DeploymentHostTabularInline
    ]

    def get_queryset(self, request):
        qs = super(HostAdmin, self).get_queryset(request)
        #qs = qs.annotate(deployments_count=(Count('deployment', distinct=True)))
        qs = qs.annotate(quirks_count=(Count('quirks', distinct=True)))
        qs = qs.annotate(aliases_count=(Count('alias', distinct=True)))
        return qs

    # def deployment_count(self, obj):
    #     return obj.deployments_count
    # deployment_count.short_description = "# Deployments"
    # deployment_count.admin_order_field = 'deployments_count'

    def quirk_count(self, obj):
        return obj.quirks_count
    quirk_count.short_description = "# Quirks"

    def has_aliases(self, obj):
        return self._boolean_icon(obj.aliases_count > 0)
    has_aliases.short_description = "Has Aliases"

    # Actions

    def reset_last_scanned_for_cloudfront_decloak(self, request, queryset):
        queryset.update(last_scanned_for_cloudfront_decloak=datetime.datetime(1970, 1, 1, 0, 0, 1))
    reset_last_scanned_for_cloudfront_decloak.short_description = "Queue for cloudfront decloak"

    change_list_template = 'admin/pokebase/host_change_list.html'
    #search_fields = ['name', 'alias_to__name', 'bucket_pointed_to__name', 'notes']
    search_fields = ['name', 'alias_to__name', 'notes']
    #autocomplete_fields = ['bucket_pointed_to', 'alias_to', 'quirks', 'technologies', 'teams']
    autocomplete_fields = ['alias_to', 'quirks', 'technologies']
    list_display = ['id', 'name', 'in_scope', 'name_resolves', 'reachable', 'has_aliases', 'is_alias', 'quirk_count', 'status', 'title', 'short_notes']
    list_filter = [
        #DomainListFilter,
        'status',
        #('bucket_pointed_to', admin.EmptyFieldListFilter),
        ('technologies', admin.RelatedOnlyFieldListFilter),
        #('deployment', admin.EmptyFieldListFilter),
        'in_scope',
        'name_resolves',
        'reachable',
        ('quirks', admin.RelatedOnlyFieldListFilter),

    ]
    ordering = ['name']
    actions = ['reset_last_scanned_for_cloudfront_decloak']
    save_as = True

class DomainListFilter(admin.SimpleListFilter):

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "Domain"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'domain'

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(name__endswith=self.value())
        else:
            return queryset

    def lookups(self, request, model_admin):
        return [(domain, domain) for domain in sorted(scopeutils.get_wildcards_in_scope())]
        # domains = set()
        # for host in model_admin.model.objects.filter(in_scope=True):
        #     tld_info = tldextract.extract(host.name)
        #     domain = '.'.join([tld_info.domain, tld_info.suffix])
        #     domains.add(domain)
        # return [(domain, domain) for domain in sorted(domains)]

class HeaderDomainListFilter(admin.SimpleListFilter):

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "Domain"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'domain'

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(host__name__endswith=self.value())
        else:
            return queryset

    def lookups(self, request, model_admin):
        return [(domain, domain) for domain in sorted(scopeutils.get_wildcards_in_scope())]
        # domains = set()
        # for host in model_admin.model.objects.filter(in_scope=True):
        #     tld_info = tldextract.extract(host.name)
        #     domain = '.'.join([tld_info.domain, tld_info.suffix])
        #     domains.add(domain)
        # return [(domain, domain) for domain in sorted(domains)]