from django.db import models
from bbprograms import models as bbmodels
import datetime
from pokebase.models import Host
from pokebase.models import BaseModel, NotableMixin, BaseVulnerability, Weakness

class CloudMixin(models.Model):

    class Provider(models.IntegerChoices):
        AWS = 0, 'AWS'
        GCP = 1, 'GCP'
        AZURE = 2, 'Azure'

    provider = models.IntegerField(choices=Provider.choices)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Bucket(BaseModel, CloudMixin):
    name = models.CharField(max_length=255, unique=True)
    region = models.CharField(max_length=255, blank=True)
    owner = models.ForeignKey('CloudAccount', blank=True, null=True, on_delete=models.SET_NULL)
    owner_from_acl = models.CharField(max_length=512, blank=True)
    last_scanned = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))
    readable_object = models.CharField(max_length=512, blank=True, help_text="Used to help determine bucket owner")
    exists = models.BooleanField(default=True)
    ignore = models.BooleanField(default=False)
    hosts = models.ManyToManyField(Host, blank=True)
    can_read = models.BooleanField(default=False)
    can_read_acl = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)

    @classmethod
    def delete_suspicious(cls):
        cls.objects.filter(ignore=False, last_scanned=datetime.datetime(1970, 1, 1, 0, 0, 1), provider=cls.Provider["AWS"]).delete()

class CloudAccount(NotableMixin, CloudMixin):

    FAKE_BUCKET_TEAM_HANDLE = "__CAMPER__"

    team = models.ForeignKey(bbmodels.Team, blank=True, null=True, on_delete=models.CASCADE)
    account_id = models.CharField(max_length=255, unique=True)
    canonical_user_id = models.CharField(max_length=255, blank=True, help_text="obfuscated id for s3")
    display_name = models.CharField(max_length=512, blank=True)
    use_for_ownership_check = models.BooleanField(default=True)

    def __str__(self):
        pieces = [self.account_id]
        if self.display_name:
            pieces.append(f"dn:{self.display_name}")
        return " ".join(pieces)

    class Meta:
        ordering = ["account_id"]

class CloudKey(NotableMixin, CloudMixin):
    key_id = models.CharField(max_length=255, unique=True)
    account = models.ForeignKey(CloudAccount, blank=True, null=True, on_delete=models.SET_NULL)
    hosts = models.ManyToManyField(Host, blank=True)
    buckets = models.ManyToManyField(Bucket, blank=True)
    valid = models.BooleanField(default=True)

    def __str__(self):
        return self.key_id

class Vulnerability(BaseVulnerability):
    weakness = models.ForeignKey(Weakness, on_delete=models.SET_NULL, blank = True, null = True, related_name='+')
    bucket = models.ForeignKey(Bucket, on_delete=models.CASCADE, blank = True, null = True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)