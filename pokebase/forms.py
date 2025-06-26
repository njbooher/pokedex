from django import forms
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from . import models

class HostImportForm(forms.Form):

    hosts = forms.CharField(widget=forms.Textarea)
    in_scope = forms.BooleanField()

    def clean_hosts(self):

        self.cleaned_data['hosts'] = self.cleaned_data['hosts'].strip()

        parsed_data = []

        try:
            for line in self.cleaned_data['hosts'].split("\n"):
                cols = line.strip().split("\t")
                name = cols[0]
                if len(name) == 0:
                    continue

                if '://' in name:
                    name = name[name.find('://')+3:]
                    
                quirks = ""
                if len(cols) > 1:
                    quirks = cols[1]
                parsed_data.append((name, quirks))
        except ValueError:
            raise ValidationError(
                'Could not parse hosts',
                code='invalid',
            )

        self.cleaned_data['hosts'] = parsed_data

        return self.cleaned_data['hosts']

    def import_hosts(self, hosts, in_scope):

        for hostname, quirks in hosts:
            
            try:
                with transaction.atomic():
                    host, created = models.Host.objects.select_for_update(no_key=True).get_or_create(name=hostname)
                    if in_scope:
                        host.in_scope = True
                    host.save()

            except IntegrityError:
                pass

            for tag in quirks.split(','):
                if len(tag) > 0:
                    quirk, created = models.Quirk.objects.get_or_create(tag=tag)
                    host.quirks.add(quirk)