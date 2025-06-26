from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
import requests
from bbprograms import models
from urllib.parse import urlparse

import re

valid_hostname = re.compile(r'^[A-Za-z0-9.\-]+$')
wildcard_replacement = r'[A-Za-z0-9\-]+'

class Command(BaseCommand):
    help = 'Derive scope rules from assets'

    def parse_host(self, rule, host):
        if ":" in host:
            host, rule.port = host.split(":", 1)
        if host.startswith('*.'):
            rule.is_wildcard = True
            host = host[2:]
        elif '*' in host and valid_hostname.match(host.replace('*', 'ASDFWILDCARDFDSA')) is not None:
            temp_host = host.replace('*', 'ASDFWILDCARDFDSA')
            escaped_host = re.escape(temp_host)
            host = escaped_host.replace('ASDFWILDCARDFDSA', wildcard_replacement)
            rule.host_format = models.ScopeRule.HostFormat.REGEX
        rule.host = host

    def handle_fullurl(self, asset_identifier):
        parsed_asset_identifier = urlparse(asset_identifier)
        rule = models.ScopeRule()
        self.parse_host(rule, parsed_asset_identifier.netloc)
        rule.path = parsed_asset_identifier.path
        return rule

    def handle_partialurl(self, asset_identifier):
        host, path = asset_identifier.split('/', 1)
        path = "/" + path
        rule = models.ScopeRule()
        rule.path = path
        self.parse_host(rule, host)
        return rule

    def handle_other(self, asset_identifier):
        rule = models.ScopeRule()
        self.parse_host(rule, asset_identifier)
        return rule

    def derive_rules_from_asset_identifier(self, asset_identifier):
        # TODO: Handle remaining rubbish
        maybe_rule = None
        if asset_identifier.startswith("http:") or asset_identifier.startswith("https:"):
            maybe_rule = self.handle_fullurl(asset_identifier)
        elif "/" in asset_identifier:
            maybe_rule = self.handle_partialurl(asset_identifier)
        else:
            maybe_rule = self.handle_other(asset_identifier)

        if maybe_rule is not None and hasattr(maybe_rule, 'host'):
            if hasattr(maybe_rule, 'host_format') and maybe_rule.host_format == models.ScopeRule.HostFormat.REGEX:
                return maybe_rule
            elif valid_hostname.match(maybe_rule.host) is not None:
                return maybe_rule
            else:
                print(f"got rubbish {asset_identifier}")
        else:
            print(f"got rubbish {asset_identifier}")

        return None

    def handle(self, *args, **options):

        for team in models.Team.objects.filter(offers_bounties=True, submission_state__in=[models.Team.SubmissionState.API_ONLY, models.Team.SubmissionState.OPEN]):

            # clear out existing derived rules

            models.ScopeRule.objects.filter(team=team, rule_type=models.ScopeRule.RuleType.DERIVED).delete()

            if team.add_to_scope:

                # create derived in scope rules

                in_scope_assets = models.Asset.objects.filter(team=team, asset_type=models.Asset.AssetType.URL, eligible_for_bounty=True)

                for asset in in_scope_assets:
                    for asset_identifier in asset.asset_identifier.split(","):
                        maybe_rule = self.derive_rules_from_asset_identifier(asset_identifier.strip())

                        if maybe_rule is not None:
                            maybe_rule.team = team
                            maybe_rule.rule_type = models.ScopeRule.RuleType.DERIVED
                            maybe_rule.derived_from = asset
                            maybe_rule.in_scope = True
                            maybe_rule.save()

                # create derived out of scope rules
                out_of_scope_filter = Q(team=team, asset_type=models.Asset.AssetType.URL) & (Q(eligible_for_submission=False) | Q(eligible_for_bounty=False))
                out_of_scope_assets = models.Asset.objects.filter(out_of_scope_filter)

                for asset in out_of_scope_assets:
                    for asset_identifier in asset.asset_identifier.split(","):
                        maybe_rule = self.derive_rules_from_asset_identifier(asset_identifier.strip())

                        if maybe_rule is not None:
                            maybe_rule.team = team
                            maybe_rule.rule_type = models.ScopeRule.RuleType.DERIVED
                            maybe_rule.derived_from = asset
                            maybe_rule.in_scope = False
                            maybe_rule.save()