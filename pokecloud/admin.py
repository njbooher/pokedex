from django.contrib import admin
from pokebase.admin import PokedexModelAdmin, PokedexReadonlyTabularInline, VulnerabilityAdmin as BaseVulnerabilityAdmin
from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse
from . import models
import datetime

class CloudKeyBucketTabularInline(PokedexReadonlyTabularInline):
    model  = models.CloudKey.buckets.through
    extra = 0
    show_change_link = True

class BucketAdminMixin:

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(hosts_count=(Count('hosts', distinct=True)))
        qs = qs.annotate(cloudkeys_count=(Count('cloudkey', distinct=True)))
        return qs

    def cloudkey_count(self, obj):
        return obj.cloudkeys_count
    cloudkey_count.short_description = "# Cloud Keys"
    cloudkey_count.admin_order_field = 'cloudkeys_count'

    def host_count(self, obj):
        return obj.hosts_count
    host_count.short_description = "# Hosts"
    host_count.admin_order_field = 'hosts_count'

    @admin.display(boolean=True)
    def display_can_read(self, obj):
        return obj.can_read
    display_can_read.short_description = "R"
    display_can_read.admin_order_field = 'can_read'

    @admin.display(boolean=True)
    def display_can_write(self, obj):
        return obj.can_write
    display_can_write.short_description = "W"
    display_can_write.admin_order_field = 'can_write'

    @admin.display(boolean=True)
    def display_can_read_acl(self, obj):
        return obj.can_read_acl
    display_can_read_acl.short_description = "R ACL"
    display_can_read_acl.admin_order_field = 'can_read_acl'

class BucketAdmin(BucketAdminMixin, PokedexModelAdmin):

    # Fields

    def get_account(self, obj):
        value = ""
        if obj.owner is not None:
            value = format_html('<a href="{}">{}</a>', reverse('admin:pokecloud_cloudaccount_change', args=(obj.owner.id,)), str(obj.owner))
        return value
    get_account.short_description = 'Account'
    get_account.admin_order_field = 'owner'

    def get_team(self, obj):
        value = ""
        if obj.owner is not None and obj.owner.team is not None:
            value = format_html('<a href="{}">{}</a>', reverse('admin:bbprograms_team_change', args=(obj.owner.team.handle,)), obj.owner.team.handle)
        return value
    get_team.short_description = 'Team'
    get_team.admin_order_field = 'owner__team__handle'


    # Actions

    def reset_last_scanned(self, request, queryset):
        queryset.update(last_scanned=datetime.datetime(1970, 1, 1, 0, 0, 1))
    reset_last_scanned.short_description = "Queue for scanning"

    def ignore(self, request, queryset):
        queryset.update(ignore=True)
    ignore.short_description = "Ignore"

    inlines = [
        CloudKeyBucketTabularInline
    ]
    autocomplete_fields = ['quirks', 'hosts', 'owner']
    list_display = ['id', 'name', 'region', 'get_team', 'get_account', 'host_count', 'cloudkey_count', 'exists', 'display_can_read', 'display_can_write', 'display_can_read_acl', 'ignore', 'last_scanned', 'short_notes']
    list_filter = [
        'provider',
        'region',
        ('owner', admin.EmptyFieldListFilter),
        ('owner__team', admin.EmptyFieldListFilter),
        'ignore',
        'exists',
        'can_read',
        'can_write',
        'can_read_acl',
        ('readable_object', admin.EmptyFieldListFilter),
    ]
    search_fields = ['name', 'notes']
    actions = ['reset_last_scanned', 'ignore']

class CloudKeyAdmin(PokedexModelAdmin):

    def get_queryset(self, request):
        qs = super(CloudKeyAdmin, self).get_queryset(request)
        qs = qs.annotate(hosts_count=(Count('hosts', distinct=True)))
        qs = qs.annotate(buckets_count=(Count('buckets', distinct=True)))
        return qs

    def get_team(self, obj):
        value = ""
        if obj.account is not None and obj.account.team is not None:
            value = format_html('<a href="{}">{}</a>', reverse('admin:bbprograms_team_change', args=(obj.account.team.handle,)), obj.account.team.handle)
        return value
    get_team.short_description = 'Team'
    get_team.admin_order_field = 'account__team__handle'

    def host_count(self, obj):
        return obj.hosts_count
    host_count.short_description = "# Hosts"
    host_count.admin_order_field = 'hosts_count'

    def bucket_count(self, obj):
        return obj.buckets_count
    bucket_count.short_description = "# Buckets"
    bucket_count.admin_order_field = 'buckets_count'

    autocomplete_fields = ['hosts', 'buckets', 'account']
    list_display = ['id', 'key_id', 'provider', 'get_team', 'account', 'host_count', 'bucket_count', 'valid', 'short_notes']
    list_filter = ['provider', 'valid']
    search_fields = ['key_id']

class CloudAccountBucketsTabularInline(BucketAdminMixin, PokedexReadonlyTabularInline):
    model = models.Bucket
    fields = ['id', 'name', 'region', 'host_count', 'exists', 'display_can_read', 'display_can_write', 'display_can_read_acl', 'ignore', 'last_scanned', 'short_notes']
    readonly_fields = ['host_count', 'display_can_read', 'display_can_write', 'display_can_read_acl', 'short_notes']
    extra = 0

class CloudAccountCloudKeysTabularInline(PokedexReadonlyTabularInline):
    model = models.CloudKey
    fields = ['id', 'key_id', 'provider', 'valid', 'short_notes']
    readonly_fields = ['short_notes']
    extra = 0

class CloudAccountAdmin(PokedexModelAdmin):
    def get_queryset(self, request):
        qs = super(CloudAccountAdmin, self).get_queryset(request)
        qs = qs.annotate(buckets_count=(Count('bucket', distinct=True)))
        qs = qs.annotate(cloudkeys_count=(Count('cloudkey', distinct=True)))
        return qs

    def bucket_count(self, obj):
        return obj.buckets_count
    bucket_count.short_description = "# Buckets"
    bucket_count.admin_order_field = 'buckets_count'

    def cloudkey_count(self, obj):
        return obj.cloudkeys_count
    cloudkey_count.short_description = "# CloudKeys"
    cloudkey_count.admin_order_field = 'buckets_count'

    # Actions

    def enable_use_for_ownership_check(self, request, queryset):
        queryset.update(use_for_ownership_check=True)
    enable_use_for_ownership_check.short_description = "Use for ownership check"

    def disable_use_for_ownership_check(self, request, queryset):
        queryset.update(use_for_ownership_check=False)
    disable_use_for_ownership_check.short_description = "Don't use for ownership check"

    inlines = [
        CloudAccountBucketsTabularInline,
        CloudAccountCloudKeysTabularInline
    ]
    autocomplete_fields = ['team']
    list_display = ['id', 'team', 'account_id', 'canonical_user_id', 'display_name', 'use_for_ownership_check', 'bucket_count', 'cloudkey_count', 'short_notes']
    list_filter = [
        ('team', admin.RelatedOnlyFieldListFilter),
        'provider'
    ]
    search_fields = ['account_id', 'canonical_user_id', 'display_name']
    actions = ['enable_use_for_ownership_check', 'disable_use_for_ownership_check']

# Register your models here.
class VulnerabilityAdmin(BaseVulnerabilityAdmin):

    # def get_queryset(self, request):
    #     qs = super(VulnerabilityAdmin, self).get_queryset(request)
    #     qs = qs.select_related('bucket__owner__team__handle')
    #     return qs

    def get_account(self, obj):
        value = ""
        if obj.bucket is not None:
            if obj.bucket.owner is not None:
                value = format_html('<a href="{}">{}</a>', reverse('admin:pokecloud_cloudaccount_change', args=(obj.bucket.owner.id,)), str(obj.bucket.owner))
        return value
    get_account.short_description = 'Account'
    get_account.admin_order_field = 'bucket__owner'

    def get_team(self, obj):
        value = ""
        if obj.bucket is not None and obj.bucket.owner is not None and obj.bucket.owner.team is not None:
            value = format_html('<a href="{}">{}</a>', reverse('admin:bbprograms_team_change', args=(obj.bucket.owner.team.handle,)), obj.bucket.owner.team.handle)
        return value
    get_team.short_description = 'Team'
    get_team.admin_order_field = 'bucket__owner__team__handle'

    def reset_bucket_last_scanned(self, request, queryset):
        for vuln in queryset:
            vuln.bucket.last_scanned = datetime.datetime(1970, 1, 1, 0, 0, 1)
            vuln.bucket.save(update_fields=["last_scanned"])
    reset_bucket_last_scanned.short_description = "Queue bucket for scanning"

    autocomplete_fields = ['bucket', 'weakness']

    list_display = ['id', 'bucket', 'get_team', 'get_account', 'weakness','confirmation_level','severity','reportid','fixed','false_alarm','short_description']
    actions = ['reset_bucket_last_scanned']