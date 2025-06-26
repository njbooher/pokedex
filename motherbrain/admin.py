from django.contrib import admin

from bbprograms import admin as bbadmin, models as bbmodels
from pokebase import admin as pbadmin, models as pbmodels
from pokecloud import admin as pcadmin, models as pcmodels
from pokedex import admin as pokeadmin, models as pokemodels
from pokeoauth import admin as poadmin, models as pomodels

# Register your models here.
admin.site.register(pbmodels.DNSRecord, pbadmin.DNSRecordAdmin)
admin.site.register(pbmodels.Header, pbadmin.HeaderAdmin)
admin.site.register(pbmodels.Technology, pbadmin.TechnologyAdmin)
admin.site.register(pcmodels.Bucket, pcadmin.BucketAdmin)
admin.site.register(pcmodels.CloudKey, pcadmin.CloudKeyAdmin)
admin.site.register(pcmodels.CloudAccount, pcadmin.CloudAccountAdmin)
admin.site.register(pcmodels.Vulnerability, pcadmin.VulnerabilityAdmin)
admin.site.register(pbmodels.Host, pbadmin.HostAdmin)
admin.site.register(pbmodels.Notification, pbadmin.NotificationAdmin)
admin.site.register(pbmodels.Quirk, pbadmin.QuirkAdmin)
admin.site.register(pbmodels.Weakness, pbadmin.WeaknessAdmin)

admin.site.register(pokemodels.Environment, pokeadmin.EnvironmentAdmin)
admin.site.register(pokemodels.Asset, pokeadmin.AssetAdmin)
admin.site.register(pokemodels.Deployment, pokeadmin.DeploymentAdmin)
admin.site.register(pokemodels.Interface, pokeadmin.InterfaceAdmin)
admin.site.register(pokemodels.Method, pokeadmin.MethodAdmin)

@admin.register(pokemodels.Route)
class RouteAdmin(pokeadmin.RouteAdmin):
    inlines = [
        pokeadmin.VulnerabilityRouteTabularInline,
        pokeadmin.ParameterTabularInline
    ]
    list_filter = [
        ('method__interface__asset', admin.RelatedOnlyFieldListFilter),
        'http_method',
        'usable',
        ('response_message_type', pokeadmin.ResponseContentTypeFilter),
        ('notes', admin.EmptyFieldListFilter),
        ('action', admin.EmptyFieldListFilter),
    ]
    fields = ['get_asset', 'get_interface', 'method', 'slug', 'http_method', 'action', 'required_permission', 'usable', 'response_message_type', 'source', 'quirks', 'notes', 'scan_results']
    list_display = ['id', 'get_asset', 'get_interface', 'get_method', 'slug', 'http_method', 'action', 'usable', 'parameter_count', 'parameters_with_notes_count', 'vulnerability_count', 'quirk_count', 'response_message_type', 'short_notes']

admin.site.register(pokemodels.Parameter, pokeadmin.ParameterAdmin)

@admin.register(pokemodels.Vulnerability)
class VulnerabilityAdmin(pokeadmin.VulnerabilityAdmin):
    list_display = ['id', 'get_host_or_asset','weakness','confirmation_level','severity','reportid','fixed','false_alarm','short_description']
    autocomplete_fields = ['host', 'weakness']

admin.site.register(pomodels.OAuthResource, poadmin.OAuthResourceAdmin)

@admin.register(pomodels.OAuthClient)
class OAuthClientAdmin(poadmin.OAuthClientAdmin):
    list_display = ['client_id', 'name', 'product', 'client_service', 'app', 'enabled', 'internal', 'native', 'has_secret', 'perm_grant_count', 'redirect_url']
    list_filter = [
        'internal',
        ('secret', admin.EmptyFieldListFilter),
    ]

admin.site.register(pomodels.OAuthPermissionsGrant, poadmin.OAuthPermissionsGrantAdmin)

admin.site.register(bbmodels.Team, bbadmin.TeamAdmin)
admin.site.register(bbmodels.Asset, bbadmin.AssetAdmin)
admin.site.register(bbmodels.ScopeRule, bbadmin.ScopeRuleAdmin)
admin.site.register(bbmodels.Report, bbadmin.ReportAdmin)
admin.site.register(bbmodels.Earning, bbadmin.EarningAdmin)