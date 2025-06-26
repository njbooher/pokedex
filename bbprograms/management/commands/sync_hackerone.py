from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.timezone import get_default_timezone
from django.utils.dateparse import parse_datetime
import requests
import http
import urllib3
from bbprograms import models

class Command(BaseCommand):
    help = 'Sync program data from hackerone api'

    def __init__(self, *args, **kwargs):
        self.s = requests.session()
        super().__init__(*args, **kwargs)

    def do_request(self, method, url, **kwargs):

        i = 0
        while i < 3:
            try:
                i += 1
                response = self.s.request(method=method, url=url, **kwargs)
                return response
            except requests.exceptions.InvalidURL:
                self.stdout.write(self.style.NOTICE(f"invalid url {url}"))
                raise
            except KeyboardInterrupt:
                exit()
            except http.client.RemoteDisconnected:
                if i == 3:
                    self.stdout.write(self.style.NOTICE(f"Remote disconnected 3 times trying {url}"))
                    raise
            except requests.exceptions.ConnectionError:
                if i == 3:
                    self.stdout.write(self.style.NOTICE(f"ConnectionError 3 times trying {url}"))
                    raise
            except requests.exceptions.Timeout:
                if i == 3:
                    self.stdout.write(self.style.NOTICE(f"unreachable host {url}"))
                    raise
            except requests.exceptions.ConnectionError:
                if i == 3:
                    self.stdout.write(self.style.NOTICE(f"connection error {url}"))
                    print(f" {url}")
                    raise
            except urllib3.exceptions.MaxRetryError:
                if i == 3:
                    self.stdout.write(self.style.NOTICE(f"max retries {url}"))
                    raise
            except requests.exceptions.SSLError:
                if i == 3:
                    self.stdout.write(self.style.NOTICE(f"ssl error {url}"))
                    raise
            except BaseException:
                if i == 3:
                    self.stdout.write(self.style.NOTICE(f"something went wrong {url}"))
                    raise

    def add_arguments(self, parser):
        parser.add_argument('-p', '--program', help='sync data only for the specified program')

    def handle_field(self, team, data, model_field_name, data_field_name=None):
        if data_field_name is None:
            data_field_name = model_field_name
        if data_field_name in data and data[data_field_name] is not None:
            setattr(team, model_field_name, data[data_field_name])

    def handle_enum_field(self, team, data, model_field_name, model_field_type, data_field_name=None):
        if data_field_name is None:
            data_field_name = model_field_name
        if data_field_name in data and data[data_field_name] is not None:
            if hasattr(model_field_type, data[data_field_name].upper()):
                setattr(team, model_field_name, model_field_type[data[data_field_name].upper()])

    def handle_date_field(self, team, data, model_field_name, data_field_name=None):
        if data_field_name is None:
            data_field_name = model_field_name
        if data_field_name in data and data[data_field_name] is not None:
            parsed_datetime = parse_datetime(data[data_field_name]).astimezone(tz=get_default_timezone()).replace(tzinfo=None)
            setattr(team, model_field_name, parsed_datetime)

    def handle_team(self, team_data):
        with transaction.atomic():
            team, created = models.Team.objects.select_for_update(no_key=True).get_or_create(handle=team_data["handle"])
            self.handle_field(team, team_data, "name")
            self.handle_field(team, team_data, "currency")
            self.handle_enum_field(team, team_data, "submission_state", models.Team.SubmissionState)
            self.handle_field(team, team_data, "triage_active")
            self.handle_enum_field(team, team_data, "state", models.Team.State)
            self.handle_date_field(team, team_data, "started_accepting_at")
            self.handle_field(team, team_data, "number_of_reports_for_user")
            self.handle_field(team, team_data, "number_of_valid_reports_for_user")
            self.handle_field(team, team_data, "bounty_earned_for_user")
            self.handle_date_field(team, team_data, "last_invitation_accepted_at_for_user")
            self.handle_field(team, team_data, "allows_bounty_splitting")
            self.handle_field(team, team_data, "offers_bounties")
            team.save()

    def fetch_teams(self, program_handle=None):

        if program_handle is not None:
            response_data = self.do_request('GET', f'https://api.hackerone.com/v1/hackers/programs/{program_handle}', auth=(self.api_username, self.api_key), headers={"Accept": "application/json"}).json()
            if "attributes" not in response_data:
                print(f"{response_data['id']} team_data has no attributes field")
            self.handle_team(response_data["attributes"])
        else:
            next_url = 'https://api.hackerone.com/v1/hackers/programs?page[size]=100'
            while next_url is not None:
                response_data = self.do_request('GET', next_url, auth=(self.api_username, self.api_key), headers={"Accept": "application/json"}).json()
                if "data" not in response_data or "links" not in response_data:
                    raise CommandError("response from hackerone did not contain data or links field")
                for team_data in response_data["data"]:
                    if "attributes" not in team_data:
                        print(f"{team_data['id']} team_data has no attributes field")
                        continue
                    self.handle_team(team_data["attributes"])
                if "links" in response_data and "next" in response_data["links"] and len(response_data["links"]["next"]) > 0:
                    next_url = response_data["links"]["next"]
                else:
                    next_url = None

    def handle_asset(self, team, asset_data):

        asset = models.Asset()
        asset.team = team
        self.handle_field(asset, asset_data, "is_archived")
        self.handle_field(asset, asset_data, "asset_identifier")
        self.handle_enum_field(asset, asset_data, "asset_type", models.Asset.AssetType)
        self.handle_field(asset, asset_data, "instruction")
        self.handle_enum_field(asset, asset_data, "max_severity", models.Asset.MaxSeverity)
        self.handle_field(asset, asset_data, "eligible_for_bounty")
        self.handle_field(asset, asset_data, "eligible_for_submission")
        self.handle_enum_field(asset, asset_data, "confidentiality_requirement", models.Asset.ConfidentialityRequirement)
        self.handle_enum_field(asset, asset_data, "integrity_requirement", models.Asset.IntegrityRequirement)
        self.handle_enum_field(asset, asset_data, "availability_requirement", models.Asset.AvailabilityRequirement)
        self.handle_date_field(asset, asset_data, "created_at")
        self.handle_date_field(asset, asset_data, "updated_at")
        asset.save()

    def fetch_assets(self, team):

        response_data = self.do_request('GET', f'https://api.hackerone.com/v1/hackers/programs/{team.handle}', auth=(self.api_username, self.api_key), headers={"Accept": "application/json"}).json()

        if "relationships" not in response_data or "structured_scopes" not in response_data["relationships"] or "data" not in response_data["relationships"]["structured_scopes"]:
            print(f"{team.handle} asset data did not contain structure_scopes data")
            return

        for asset_data in response_data["relationships"]["structured_scopes"]["data"]:
            if "attributes" not in asset_data:
                print(f"{team.handle} asset data has no attributes field")
                continue
            self.handle_asset(team, asset_data["attributes"])

    def handle_report(self, team, report_id, weakness, report_data):
        report, created = models.Report.objects.get_or_create(id=report_id)
        report.team = team
        self.handle_field(report, report_data, "title")
        self.handle_field(report, report_data, "state")
        self.handle_field(report, report_data, "vulnerability_information")
        self.handle_date_field(report, report_data, "created_at")
        self.handle_date_field(report, report_data, "triaged_at")
        self.handle_date_field(report, report_data, "closed_at")
        self.handle_date_field(report, report_data, "last_reporter_activity_at")
        self.handle_date_field(report, report_data, "first_program_activity_at")
        self.handle_date_field(report, report_data, "bounty_awarded_at")
        self.handle_date_field(report, report_data, "swag_awarded_at")
        self.handle_date_field(report, report_data, "disclosed_at")
        self.handle_date_field(report, report_data, "reporter_agreed_on_going_public_at")
        self.handle_date_field(report, report_data, "last_public_activity_at")
        self.handle_date_field(report, report_data, "last_activity_at")
        report.weakness = weakness
        report.save()

    def fetch_reports(self, team=None):
        next_url = 'https://api.hackerone.com/v1/hackers/me/reports?page[size]=100'
        while next_url is not None:
            response_data = self.do_request('GET', next_url, auth=(self.api_username, self.api_key), headers={"Accept": "application/json"}).json()

            for report in response_data["data"]:
                try:
                    report_team = models.Team.objects.get(handle=report["relationships"]["program"]["data"]["attributes"]["handle"])
                    if team is not None and report_team != team:
                        continue
                except:
                    continue

                try:
                    weakness = report["relationships"]["weakness"]["data"]["attributes"]["name"]
                except:
                    weakness = ""

                self.handle_report(report_team, int(report["id"]), weakness, report["attributes"])
            if "links" in response_data and "next" in response_data["links"] and len(response_data["links"]["next"]) > 0:
                next_url = response_data["links"]["next"]
            else:
                next_url = None

    def handle_earning(self, report, earning_id, earning_data):
        earning, created = models.Earning.objects.get_or_create(id=earning_id)
        earning.report = report
        self.handle_field(earning, earning_data, "amount")
        self.handle_field(earning, earning_data, "bonus_amount")
        self.handle_field(earning, earning_data, "awarded_amount")
        self.handle_field(earning, earning_data, "awarded_bonus_amount")
        self.handle_field(earning, earning_data, "awarded_currency")
        self.handle_date_field(earning, earning_data, "created_at")
        earning.save()

    def fetch_earnings(self, team=None):

        next_url = 'https://api.hackerone.com/v1/hackers/payments/earnings?page[size]=100'

        while next_url is not None:

            response_data = self.do_request('GET', next_url, auth=(self.api_username, self.api_key), headers={"Accept": "application/json"}).json()

            for earning in response_data["data"]:
                try:
                    earning_team = models.Team.objects.get(handle=earning["relationships"]["program"]["data"]["attributes"]["handle"])
                    if team is not None and earning_team != team:
                        continue
                    earning_report = models.Report.objects.get(id=int(earning["relationships"]["bounty"]["data"]["relationships"]["report"]["data"]["id"]))
                except:
                    continue

                self.handle_earning(earning_report, int(earning["id"]), earning["relationships"]["bounty"]["data"]["attributes"])

            if "links" in response_data and "next" in response_data["links"] and len(response_data["links"]["next"]) > 0:
                next_url = response_data["links"]["next"]
            else:
                next_url = None

    def handle(self, *args, **options):
        app_config = apps.get_app_config('bbprograms')
        self.api_username = app_config.hackerone_api_username
        self.api_key = app_config.hackerone_api_key

        self.fetch_teams(program_handle=options['program'])

        # clear out assets
        if options['program'] is not None:
            asset_qs = models.Asset.objects.filter(team__handle=options['program'])
        else:
            asset_qs = models.Asset.objects.all()

        asset_qs.delete()

        # repopulate assets

        if options['program'] is not None:
            team_qs = models.Team.objects.filter(handle=options['program'])
        else:
            team_qs = models.Team.objects.filter(offers_bounties=True, submission_state__in=[models.Team.SubmissionState.API_ONLY, models.Team.SubmissionState.OPEN])

        for team in team_qs:
            self.fetch_assets(team)

        # sync reports
        if options['program'] is not None:
            team = models.Team.objects.get(handle=options['program'])
            self.fetch_reports(team)
        else:
            self.fetch_reports()

        # sync earnings
        if options['program'] is not None:
            team = models.Team.objects.get(handle=options['program'])
            self.fetch_earnings(team)
        else:
            self.fetch_earnings()

