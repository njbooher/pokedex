from django.contrib import admin
import django.forms
import django.db.models
from django.db.models import Count
from . import forms, models
from pokebase.admin import PokedexModelAdmin, PokedexTabularInline

class OAuthPermPrefixListFilter(admin.SimpleListFilter):

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "Perm Prefix"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'perm_prefix'

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(name__startswith=self.value())
        else:
            return queryset

    def lookups(self, request, model_admin):
        prefixes = set()
        for resource in model_admin.model.objects.all():
            prefixes.add(resource.name.split(':')[0])
        return [(prefix, prefix) for prefix in sorted(prefixes)]


# Register your models here.
class OAuthPermissionsGrantResourceTabularInline(PokedexTabularInline):
    model = models.OAuthPermissionsGrant
    raw_id_fields = ('resource',)
    fields = ('resource', 'client', 'grant_type', 'can_create', 'can_read', 'can_update', 'can_delete')
    extra = 0

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class OAuthResourceAdmin(PokedexModelAdmin):

    def get_queryset(self, request):
        qs = super(OAuthResourceAdmin, self).get_queryset(request)
        qs = qs.annotate(ref_count=(Count('grant', distinct=True)))
        qs = qs.annotate(noperm_count=(Count('grant', distinct=True, filter=django.db.models.Q(grant__can_create=False, grant__can_read=False, grant__can_update=False, grant__can_delete=False))))
        qs = qs.annotate(create_count=(Count('grant', distinct=True, filter=django.db.models.Q(grant__can_create=True))))
        qs = qs.annotate(read_count=(Count('grant', distinct=True, filter=django.db.models.Q(grant__can_read=True))))
        qs = qs.annotate(update_count=(Count('grant', distinct=True, filter=django.db.models.Q(grant__can_update=True))))
        qs = qs.annotate(delete_count=(Count('grant', distinct=True, filter=django.db.models.Q(grant__can_delete=True))))
        return qs

    def ref_count(self, obj):
        return obj.ref_count
    ref_count.short_description = "# REF"
    ref_count.admin_order_field = 'ref_count'

    def noperm_count(self, obj):
        return obj.noperm_count
    noperm_count.short_description = "# NOPERM"
    noperm_count.admin_order_field = 'noperm_count'

    def create_count(self, obj):
        return obj.create_count
    create_count.short_description = "# CREATE"
    create_count.admin_order_field = 'create_count'

    def read_count(self, obj):
        return obj.read_count
    read_count.short_description = "# READ"
    read_count.admin_order_field = 'read_count'

    def update_count(self, obj):
        return obj.update_count
    update_count.short_description = "# UPDATE"
    update_count.admin_order_field = 'update_count'

    def delete_count(self, obj):
        return obj.delete_count
    delete_count.short_description = "# DELETE"
    delete_count.admin_order_field = 'delete_count'

    inlines = [
        OAuthPermissionsGrantResourceTabularInline
    ]
    list_display = ['name', 'ref_count', 'noperm_count', 'create_count', 'read_count', 'update_count', 'delete_count']
    list_filter = [
        OAuthPermPrefixListFilter
    ]
    autocomplete_fields = ['quirks']
    search_fields = ['name']

class OAuthPermissionsGrantClientTabularInline(PokedexTabularInline):
    form = forms.OAuthClientPermissionsGrantResourceAdminInlineForm
    model = models.OAuthPermissionsGrant
    raw_id_fields = ('client',)
    fields = ('client', 'resource', 'grant_type', 'can_create', 'can_read', 'can_update', 'can_delete')
    autocomplete_fields = ['resource']
    extra = 0
    show_change_link = True

class OAuthClientAdmin(PokedexModelAdmin):

    @admin.display(boolean=True)
    def has_secret(self, obj):
        return len(obj.secret) > 0
    has_secret.short_description = "Has Secret"
    has_secret.admin_order_field = 'secret'

    def get_queryset(self, request):
        qs = super(OAuthClientAdmin, self).get_queryset(request)
        qs = qs.annotate(perm_grant_count=(Count('grant', distinct=True)))
        return qs

    def perm_grant_count(self, obj):
        return obj.perm_grant_count
    perm_grant_count.short_description = "# Perms"
    perm_grant_count.admin_order_field = 'perm_grant_count'

    change_list_template = 'admin/pokeoauth/oauthclient_change_list.html'

    inlines = [
        OAuthPermissionsGrantClientTabularInline
    ]
    list_display = ['id', 'client_id', 'name', 'product', 'client_service', 'app', 'enabled', 'internal', 'native', 'has_secret', 'perm_grant_count', 'redirect_url']
    list_filter = [
        'internal',
        ('secret', admin.EmptyFieldListFilter),
    ]
    autocomplete_fields = ['quirks']
    search_fields = ['name']

class OAuthPermissionsGrantAdmin(PokedexModelAdmin):
    list_display = ['client', 'resource',  'grant_type', 'can_create', 'can_read', 'can_update', 'can_delete']
    list_filter = ['grant_type', 'can_create', 'can_read', 'can_update', 'can_delete']
    autocomplete_fields = ['quirks']
    search_fields = ['resource__name', 'client__name']
