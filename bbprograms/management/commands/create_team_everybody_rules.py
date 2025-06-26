from django.core.management.base import BaseCommand
from django.db import transaction
from bbprograms import models
import re

class Command(BaseCommand):
    help = 'Add team everybody rules'

    def create_rule(self, host, is_wildcard=False, in_scope=True, context="ALWAYS", host_format="STRING"):
        rule = models.ScopeRule()
        rule.team = self.team_everybody
        rule.in_scope = in_scope
        rule.rule_type = models.ScopeRule.RuleType.CUSTOM
        rule.rule_context = models.ScopeRule.RuleContext[context]
        rule.host = host
        rule.host_format = models.ScopeRule.HostFormat[host_format]
        rule.is_wildcard = is_wildcard
        rule.save()

    def handle(self, *args, **options):

        self.team_everybody, created = models.Team.objects.get_or_create(handle=models.Team.WILDCARD_HANDLE, name="Placeholder for rules that apply to all programs", submission_state=models.Team.SubmissionState.OPEN, state=models.Team.State.PUBLIC_MODE)

        with transaction.atomic():

            models.ScopeRule.objects.select_for_update().filter(team=self.team_everybody, rule_type=models.ScopeRule.RuleType.CUSTOM).delete()

            self.create_rule("s3.amazonaws.com", is_wildcard=True)
            self.create_rule("storage.googleapis.com", is_wildcard=True)

            self.create_rule("akamai.net", context="CNAMES", is_wildcard=True)
            self.create_rule("akamaized.net", context="CNAMES", is_wildcard=True)
            self.create_rule("edgekey.net", context="CNAMES", is_wildcard=True)
            self.create_rule("cloudfront.net", context="CNAMES", is_wildcard=True)
            self.create_rule("akamaiedge.net", context="CNAMES", is_wildcard=True)
            self.create_rule("edgesuite.net", context="CNAMES", is_wildcard=True)

            self.create_rule("s3.amazonaws.com", context="AMASS", in_scope=False, is_wildcard=True)
            self.create_rule("digitaloceanspaces.com", context="AMASS", in_scope=False, is_wildcard=True)
            self.create_rule("storage.googleapis.com", context="AMASS", in_scope=False, is_wildcard=True)

            self.create_rule(r"^(s3-|s3\.).+\.amazonaws\.com", host_format="REGEX", in_scope=False)
            self.create_rule(r"^[A-Za-z0-9]{32}\.cloudfront\.net", host_format="REGEX", in_scope=False)

            self.create_rule("spot-price.s3.amazonaws.com", in_scope=False)
            self.create_rule("awsmedia.s3.amazonaws.com", in_scope=False)
            self.create_rule("aws-quickstart.s3.amazonaws.com", in_scope=False)
            self.create_rule("spot-bid-advisor.s3.amazonaws.com", in_scope=False)
            self.create_rule("www.amazon.com.s3.amazonaws.com", in_scope=False)

