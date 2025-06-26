from math import fabs
from django.db import models
import datetime

class Organization(models.Model):
    handle = models.CharField(max_length=512, primary_key=True)
    codename = models.CharField(max_length=512, blank=True)
    name = models.CharField(max_length=512, blank=True)
    def __str__(self):
        return self.name
        
class Team(models.Model):

    WILDCARD_HANDLE = "__TEAMEVERYBODY__"

    class SubmissionState(models.IntegerChoices):
        OTHER = 0
        OPEN = 1
        API_ONLY = 2
        PAUSED = 3

    class State(models.IntegerChoices):
        OTHER = 0
        SANDBOXED = 1
        SOFT_LAUNCHED = 2 # private
        PUBLIC_MODE = 3

    class SynackCategory(models.IntegerChoices):
        OTHER = 0
        WEB_APPLICATION = 1
        HOST = 2

    class SynackCollaboration(models.IntegerChoices):
        OTHER = 0
        FVEY = (1, 'FVEY')
        USA = (2, 'USA')

    handle = models.CharField(max_length=512, primary_key=True)
    name = models.CharField(max_length=512, blank=True)
    currency = models.CharField(max_length=512, blank=True)
    submission_state = models.IntegerField(choices=SubmissionState.choices, default=SubmissionState.OTHER)
    triage_active = models.BooleanField(default=False)
    state = models.IntegerField(choices=State.choices, default=State.OTHER)
    started_accepting_at = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))
    number_of_reports_for_user = models.IntegerField(default=0)
    number_of_valid_reports_for_user = models.IntegerField(default=0)
    bounty_earned_for_user = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    last_invitation_accepted_at_for_user = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))
    allows_bounty_splitting = models.BooleanField(default=False)
    offers_bounties = models.BooleanField(default=False)
    add_to_scope = models.BooleanField(default=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, blank=True, null=True)
    synack_category = models.IntegerField(choices=SynackCategory.choices, default=SynackCategory.OTHER)
    synack_collaboration= models.IntegerField(choices=SynackCollaboration.choices, default=SynackCollaboration.OTHER)
    synack_missions_only = models.BooleanField(default=False)
    synack_dypri = models.BooleanField(default=False)
    
    def __str__(self):
        return self.handle

class Asset(models.Model):

    class MaxSeverity(models.IntegerChoices):
        NONE = 0
        LOW = 1
        MEDIUM = 2
        HIGH = 3
        CRITICAL = 4

    class AssetType(models.IntegerChoices):
        OTHER = 0
        CIDR = 1
        URL = 2
        EXECUTABLE = 3
        APPLE_STORE_APP_ID = 4
        TESTFLIGHT = 5
        OTHER_IPA = 6
        GOOGLE_PLAY_APP_ID = 7
        OTHER_APK = 8
        WINDOWS_APP_STORE_APP_ID = 9
        SOURCE_CODE = 10
        DOWNLOADABLE_EXECUTABLES = 11
        HARDWARE = 12

    class ConfidentialityRequirement(models.IntegerChoices):
        NONE = 0
        LOW = 1
        MEDIUM = 2
        HIGH = 3

    class IntegrityRequirement(models.IntegerChoices):
        NONE = 0
        LOW = 1
        MEDIUM = 2
        HIGH = 3

    class AvailabilityRequirement(models.IntegerChoices):
        NONE = 0
        LOW = 1
        MEDIUM = 2
        HIGH = 3

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    is_archived = models.BooleanField(default=False)
    asset_type = models.IntegerField(choices=AssetType.choices, default=AssetType.OTHER)
    asset_identifier = models.CharField(max_length=512, blank=True)
    instruction = models.TextField(blank=True)
    max_severity = models.IntegerField(choices=MaxSeverity.choices, default=MaxSeverity.NONE)
    eligible_for_bounty = models.BooleanField(default=False)
    eligible_for_submission = models.BooleanField(default=False)
    confidentiality_requirement = models.IntegerField(choices=ConfidentialityRequirement.choices, blank=True, null=True)
    integrity_requirement = models.IntegerField(choices=IntegrityRequirement.choices, blank=True, null=True)
    availability_requirement = models.IntegerField(choices=AvailabilityRequirement.choices, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))
    updated_at = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))

    def __str__(self):
        return self.asset_identifier

    @property
    def short_instruction(self):
        return self.instruction if len(self.instruction) < 200 else (self.instruction[:200] + '..')

class ScopeRule(models.Model):

    class RuleType(models.IntegerChoices):
        DERIVED = 0
        CUSTOM = 1

    class RuleContext(models.IntegerChoices):
        ALWAYS = 0
        CNAMES = 1
        SECURITYTRAILS = 2
        AMASS = 3
        AMASSBF = 4
        BUCKETS = 5

    class HostFormat(models.IntegerChoices):
        STRING = 0
        REGEX = 1

    FILTER_IN_SCOPE_SIMPLE = models.Q(is_wildcard=False, in_scope=True, rule_context=RuleContext.ALWAYS, host_format=HostFormat.STRING)
    FILTER_IN_SCOPE_WILDCARD = models.Q(is_wildcard=True, in_scope=True, rule_context=RuleContext.ALWAYS, host_format=HostFormat.STRING)
    FILTER_IN_SCOPE_SIMPLE_AND_WILDCARD = models.Q(in_scope=True, rule_context=RuleContext.ALWAYS, host_format=HostFormat.STRING)
    FILTER_IN_SCOPE_REGEX = models.Q(is_wildcard=False, in_scope=True, rule_context=RuleContext.ALWAYS, host_format=HostFormat.REGEX)
    FILTER_CNAMES_IN_SCOPE_SIMPLE = models.Q(is_wildcard=False, in_scope=True, rule_context=RuleContext.CNAMES, host_format=HostFormat.STRING)
    FILTER_CNAMES_IN_SCOPE_WILDCARD = models.Q(is_wildcard=True, in_scope=True, rule_context=RuleContext.CNAMES, host_format=HostFormat.STRING)
    FILTER_CNAMES_IN_SCOPE_SIMPLE_AND_WILDCARD = models.Q(in_scope=True, rule_context=RuleContext.CNAMES, host_format=HostFormat.STRING)
    FILTER_SECURITYTRAILS_IN_SCOPE = models.Q(in_scope=True, rule_context=RuleContext.SECURITYTRAILS, host_format=HostFormat.STRING)
    FILTER_AMASSBF_IN_SCOPE = models.Q(in_scope=True, rule_context=RuleContext.AMASSBF, host_format=HostFormat.STRING)

    FILTER_OUT_OF_SCOPE_SIMPLE = models.Q(is_wildcard=False, in_scope=False, rule_context=RuleContext.ALWAYS, host_format=HostFormat.STRING)
    FILTER_OUT_OF_SCOPE_WILDCARD = models.Q(is_wildcard=True, in_scope=False, rule_context=RuleContext.ALWAYS, host_format=HostFormat.STRING)
    FILTER_OUT_OF_SCOPE_SIMPLE_AND_WILDCARD = models.Q(in_scope=False, rule_context=RuleContext.ALWAYS, host_format=HostFormat.STRING)
    FILTER_CNAMES_OUT_OF_SCOPE_SIMPLE = models.Q(is_wildcard=False, in_scope=False, rule_context=RuleContext.CNAMES, host_format=HostFormat.STRING)
    FILTER_CNAMES_OUT_OF_SCOPE_WILDCARD = models.Q(is_wildcard=True, in_scope=False, rule_context=RuleContext.CNAMES, host_format=HostFormat.STRING)
    FILTER_CNAMES_OUT_OF_SCOPE_SIMPLE_AND_WILDCARD = models.Q(in_scope=False, rule_context=RuleContext.CNAMES, host_format=HostFormat.STRING)
    FILTER_OUT_OF_SCOPE_REGEX = models.Q(is_wildcard=False, in_scope=False, rule_context=RuleContext.ALWAYS, host_format=HostFormat.REGEX)
    FILTER_SECURITYTRAILS_OUT_OF_SCOPE = models.Q(in_scope=False, rule_context=RuleContext.SECURITYTRAILS, host_format=HostFormat.STRING)
    FILTER_AMASS_OUT_OF_SCOPE = models.Q(in_scope=False, rule_context=RuleContext.AMASS, host_format=HostFormat.STRING)
    FILTER_BUCKETS_OUT_OF_SCOPE = models.Q(in_scope=False, rule_context=RuleContext.BUCKETS, host_format=HostFormat.STRING)

    team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True, null=True)
    rule_type = models.IntegerField(choices=RuleType.choices, default=RuleType.CUSTOM)
    rule_context = models.IntegerField(choices=RuleContext.choices, default=RuleContext.ALWAYS)
    derived_from = models.ForeignKey(Asset, on_delete=models.CASCADE, blank=True, null=True)
    in_scope = models.BooleanField(default=False)
    host = models.CharField(max_length=512, blank=True)
    host_format = models.IntegerField(choices=HostFormat.choices, default=HostFormat.STRING)
    is_wildcard = models.BooleanField(default=False)
    port = models.IntegerField(blank=True, null=True)
    path = models.CharField(max_length=512, blank=True)
    last_run_amass = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))
    last_run_securitytrails = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))

class Report(models.Model):

    class SynackState(models.IntegerChoices):
        OTHER = 0
        ACCEPTED = 1
        IN_QUEUE = 2
        REJECTED = 3

    team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=512, blank=True)
    state = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(null=True)
    vulnerability_information = models.TextField(blank=True)
    triaged_at = models.DateTimeField(null=True)
    closed_at = models.DateTimeField(null=True)
    last_reporter_activity_at = models.DateTimeField(null=True)
    first_program_activity_at = models.DateTimeField(null=True)
    last_program_activity_at = models.DateTimeField(null=True)
    bounty_awarded_at = models.DateTimeField(null=True)
    swag_awarded_at = models.DateTimeField(null=True)
    disclosed_at = models.DateTimeField(null=True)
    reporter_agreed_on_going_public_at = models.DateTimeField(null=True)
    last_public_activity_at = models.DateTimeField(null=True)
    last_activity_at = models.DateTimeField(null=True)
    weakness = models.CharField(max_length=512, blank=True)
    sub_weakness = models.CharField(max_length=512, blank=True)
    synack_state = models.IntegerField(choices=SynackState.choices, default=SynackState.OTHER)

class Earning(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, blank=True, null=True)
    type = models.CharField(max_length=512, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    awarded_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    awarded_bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    awarded_currency = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))