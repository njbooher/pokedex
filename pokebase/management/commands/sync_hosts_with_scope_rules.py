from django.core.management.base import BaseCommand
from django.db.models import Q
from pokebase import models
from bbprograms import models as bbmodels

import re


class Command(BaseCommand):
    help = 'Create hosts out of scope rules'

    def handle(self, *args, **options):
        for team in bbmodels.Team.objects.all():

            # in scope simple
            for rule in bbmodels.ScopeRule.objects.filter(Q(team=team) & bbmodels.ScopeRule.FILTER_IN_SCOPE_SIMPLE):
                try:
                    host = models.Host.objects.get(name=rule.host)
                    team.host_set.add(host)
                except models.Host.DoesNotExist:
                    host = models.Host()
                    host.name = rule.host
                    host.in_scope = True
                    host.save()
                    #host.teams.add(team)


            # out of scope simple
            for rule in bbmodels.ScopeRule.objects.filter(Q(team=team) & bbmodels.ScopeRule.FILTER_OUT_OF_SCOPE_SIMPLE):
                try:
                    host = models.Host.objects.get(name=rule.host)
                    team.host_set.add(host)
                except models.Host.DoesNotExist:
                    host = models.Host()
                    host.name = rule.host
                    host.in_scope = False
                    host.save()
                    #host.teams.add(team)


            # TODO: Wildcards