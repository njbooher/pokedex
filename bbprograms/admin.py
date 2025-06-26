from django.contrib import admin
from django.db.models import Count
import datetime
from . import  models

# Register your models here.
class AssetAdminMixin:
    def confidentiality(self, obj):
        if obj.confidentiality_requirement is not None:
            return models.Asset.ConfidentialityRequirement(obj.confidentiality_requirement).label
        else:
            return None
    confidentiality.short_description = "C"
    confidentiality.admin_order_field = 'confidentiality_requirement'

    def integrity(self, obj):
        if obj.integrity_requirement is not None:
            return models.Asset.IntegrityRequirement(obj.integrity_requirement).label
        else:
            return None
    integrity.short_description = "I"
    integrity.admin_order_field = 'integrity_requirement'

    def availability(self, obj):
        if obj.availability_requirement is not None:
            return models.Asset.AvailabilityRequirement(obj.availability_requirement).label
        else:
            return None
    availability.short_description = "A"
    availability.admin_order_field = 'availability_requirement'

class AssetAdmin(admin.ModelAdmin, AssetAdminMixin):
    list_display = ["team", "asset_type", "asset_identifier", "max_severity", "eligible_for_bounty", "eligible_for_submission", "confidentiality", "integrity", "availability", "created_at", "updated_at", "short_instruction"]
    list_filter = ["asset_type", "max_severity", "eligible_for_bounty", "eligible_for_submission", "confidentiality_requirement", "integrity_requirement", "availability_requirement"]
    search_fields = ["asset_identifier"]
    autocomplete_fields = ["team"]

class TeamAssetsTabularInline(admin.TabularInline, AssetAdminMixin):

    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    model = models.Asset
    readonly_fields = ["confidentiality", "integrity", "availability", "short_instruction"]
    fields = ["team", "asset_type", "asset_identifier", "max_severity", "eligible_for_bounty", "eligible_for_submission", "confidentiality", "integrity", "availability", "created_at", "updated_at", "short_instruction"]
    extra = 0

class OrganizationTeamsTabularInline(admin.TabularInline, AssetAdminMixin):

    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    model = models.Team
    readonly_fields = ["handle", "name"]
    fields = ["handle", "name"]
    extra = 0

class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["handle", "codename", "name"]
    search_fields = ["handle", "codename", "name"]
    inlines = [
        OrganizationTeamsTabularInline
    ]

class TeamAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(TeamAdmin, self).get_queryset(request)
        qs = qs.annotate(assets_count=(Count('asset', distinct=True)))
        return qs

    def asset_count(self, obj):
        return obj.assets_count
    asset_count.short_description = "# Assets"
    asset_count.admin_order_field = 'assets_count'

    inlines = [
        TeamAssetsTabularInline
    ]
    list_display = ["handle", "name", "submission_state", "asset_count", "state", "started_accepting_at", "number_of_reports_for_user", "number_of_valid_reports_for_user", "bounty_earned_for_user", "triage_active", "allows_bounty_splitting", "offers_bounties", "add_to_scope"]
    list_filter = ["submission_state", "triage_active", "state", "allows_bounty_splitting", "offers_bounties"]
    search_fields = ["handle", "name"]

class ScopeRuleAdmin(admin.ModelAdmin):

    def reset_last_run_amass(self, request, queryset):
        queryset.update(last_run_amass=datetime.datetime(1970, 1, 1, 0, 0, 1))
    reset_last_run_amass.short_description = "Queue for amass scanning"

    list_display = ["id", "team", "rule_type", "rule_context", "in_scope", "host", "host_format", "is_wildcard", "port", "path", "derived_from", "last_run_amass"]
    list_filter = ["rule_type", "rule_context", "host_format", "in_scope", "is_wildcard"]
    search_fields = ["host"]
    autocomplete_fields = ["team", "derived_from"]
    actions = ['reset_last_run_amass']

class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'team', 'title', 'state', 'created_at', 'bounty_awarded_at', 'closed_at']
    list_filter = [
        ('team', admin.RelatedOnlyFieldListFilter),
        'state',
        'weakness'
    ]
    search_fields = ["title"]

class EarningAdmin(admin.ModelAdmin):

    def get_report_title(self, obj):
        return obj.report.title
    get_report_title.admin_order_field  = 'report__title'  #Allows column order sorting
    get_report_title.short_description = 'Asset'  #Renames column head

    list_display = ['id', 'get_report_title', 'amount', 'bonus_amount', 'awarded_amount', 'awarded_bonus_amount', 'awarded_currency', 'created_at']
    list_filter = [
        'report__weakness'
    ]