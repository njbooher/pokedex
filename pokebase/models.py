from django.db import models
#from bbprograms import models as bbmodels
import datetime
from . import slack

# Generic Stuff

class NotableMixin(models.Model):
    notes = models.TextField(blank=True)

    @property
    def short_notes(self):
        return self.notes if len(self.notes) < 200 else (self.notes[:200] + '..')

    class Meta:
        abstract = True


class Quirk(NotableMixin):
    tag = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.tag

class QuirkyMixin(models.Model):
    quirks = models.ManyToManyField(Quirk, blank=True)
    class Meta:
        abstract = True

class BaseModel(NotableMixin, QuirkyMixin):

    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True

class Weakness(BaseModel):

    class Meta:
        verbose_name_plural = 'weaknesses'

class BaseVulnerability(models.Model):

    class Severity(models.IntegerChoices):
        NONE = 0
        LOW = 1
        MEDIUM = 2
        HIGH = 3
        CRITICAL = 4

    class ConfirmationLevel(models.IntegerChoices):
        WIP = 0
        SCANNER = 1
        CONFIRMED = 2

    weakness = models.ForeignKey(Weakness, on_delete=models.SET_NULL, blank = True, null = True)
    confirmation_level = models.IntegerField(choices=ConfirmationLevel.choices, default=ConfirmationLevel.CONFIRMED)
    severity = models.IntegerField(choices=Severity.choices, default=Severity.NONE)
    description = models.TextField(blank=True)
    reportid = models.IntegerField(blank=True, null=True)
    fixed = models.BooleanField()
    false_alarm = models.BooleanField(default=False)

    @property
    def short_description(self):
        return self.description if len(self.description) < 200 else (self.description[:200] + '...')

    class Meta:
        verbose_name_plural = 'vulnerabilities'
        abstract = True

# Generic Stuff

class Technology(BaseModel):
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'technologies'


class Host(BaseModel):

    name = models.CharField(max_length=255, unique=True)
    reachable = models.BooleanField(null=True)
    name_resolves = models.BooleanField(null=True)
    last_resolved = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))
    is_alias = models.BooleanField(default=False)
    alias_to = models.ForeignKey('self', related_name="aliases", related_query_name="alias", blank=True, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=255, blank=True)
    status = models.IntegerField(default=0)
    status_previous = models.IntegerField(default=0)
    content_length = models.IntegerField(default=0)
    technologies = models.ManyToManyField(Technology, blank=True)
    in_scope = models.BooleanField(null=True)

    # @property
    # def is_bucket(self):
    #     return self.bucket_pointed_to is not None

class DNSRecord(BaseModel):
    class RecordType(models.IntegerChoices):
        UNKNOWN = 0
        A = 1
        AAAA = 2
        CNAME = 3
        NS = 4
        TXT = 5
        PTR = 6
        MX = 7
        SOA = 8

    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    record_type = models.IntegerField(choices=RecordType.choices, default=RecordType.UNKNOWN)
    value = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'DNS Record'

class Header(BaseModel):
    host = models.ForeignKey(Host, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255)
    value = models.TextField(blank=True)

# Recording keeping stuff

class Notification(models.Model):

    class NotificationType(models.IntegerChoices):
        UNKNOWN = 0, 'Unknown'
        HOSTS_ADDED = 1, 'Hosts Added'
        PROTOBUFS_ADDED = 2, 'Protobufs Added'
        WEBAPIS_ADDED = 3, 'WebAPIs Added'
        JSMONITOR_CHANGES = 4, 'JS Changes'
        GITMONITOR_CHANGES = 5, 'Git Monitor Changes'
        STATUSCODE_CHANGE = 6, 'Status Code Change'
        S3MISCONFIG = 7, 'S3 Misconfiguration'
        OAUTH_RESOURCE_ADDED = 8, 'OAuth Resource Added'
        NUCLEI_RESULT = 9, 'Nuclei Result'
        FFUF_RESULT = 10, 'FFUF Result'
        JOB_ERROR = 11, 'Job Error',
        DIRECT_RESULT = 12, 'Direct Result'
        BUCKETS_ADDED = 13, 'Buckets Added'
        OAUTH_CHANGES = 14, 'OAuth Changes'
        HOST_REACHABLE = 15, 'Host Reachable'
        GRAPHQL_CHANGES = 16, 'GraphQL Changes'

    notification_type = models.IntegerField(choices=NotificationType.choices, default=NotificationType.UNKNOWN)
    title = models.CharField(max_length=255)
    body = models.JSONField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                slack.Notification(self.title, self.body).send()
            except Exception as e:
                pass
        super().save(*args, **kwargs)