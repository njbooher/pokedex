from django.db import models
import datetime
from pokebase.models import BaseModel, BaseVulnerability, Host


class Environment(BaseModel):
    name = models.CharField(max_length=255, unique=True)

class Asset(BaseModel):

    class AssetType(models.IntegerChoices):
        UNKNOWN = 0, 'Unknown'
        MICROSERVICE = 2, 'Microservice'
        SITE = 3, 'Site'
        EXECUTABLE = 4, 'Executable'

    name = models.CharField(max_length=255, unique=True)
    type = models.IntegerField(choices=AssetType.choices, default=AssetType.UNKNOWN, verbose_name='Type')

class Deployment(BaseModel):

    class Protocol(models.IntegerChoices):
        UNKNOWN = 0, 'Unknown'
        HTTP = 1, 'HTTP'
        HTTPS = 2, 'HTTPS'

    name = None
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, blank=True, null=True)
    protocol = models.IntegerField(choices=Protocol.choices, default=Protocol.HTTPS)
    host = models.ForeignKey(Host, on_delete=models.SET_NULL, blank=True, null=True)
    base_path = models.CharField(max_length=512, blank=True)
    environment = models.ForeignKey(Environment, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['asset', 'protocol', 'host', 'base_path'], name='unique_deployment')
        ]

    def __str__(self):
        fields = [str(self.id)]#[self.Protocol(self.protocol).label, self.host.name, self.base_path]
        return " ".join(fields)

class Interface(BaseModel):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    last_scanned_for_methods = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))
    last_scanned_for_templates = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['asset', 'name'], name='unique_interface')
        ]
        ordering = ['name']

class Method(BaseModel):
    interface = models.ForeignKey(Interface, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['interface', 'name'], name='unique_method')
        ]
        ordering = ['name']

class Route(BaseModel):

    class HTTPMethod(models.IntegerChoices):
        UNKNOWN = 0, 'Unknown'
        GET = 1, 'GET'
        POST = 2, 'POST'
        DELETE = 3, 'DELETE'
        PUT = 4, 'PUT'
        PATCH = 5, 'PATCH'

    name = None
    method = models.ForeignKey(Method, on_delete=models.CASCADE)
    slug = models.CharField(max_length=512, blank=True)
    action = models.CharField(max_length=255, blank=True)
    http_method = models.IntegerField(choices=HTTPMethod.choices, default=HTTPMethod.UNKNOWN, verbose_name='HTTP Method')
    usable = models.BooleanField(null=True)
    required_permission = models.CharField(max_length=255, blank=True)
    response_message_type = models.CharField(max_length=255, blank=True)
    last_scanned = models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 1))
    scan_results = models.TextField(blank=True)
    scan_usable = models.BooleanField(default=False)
    scan_status = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['method', 'action', 'http_method', 'slug'], name='unique_route')
        ]

    def __str__(self):
        return " ".join([self.HTTPMethod(self.http_method).label, self.method.interface.name, self.method.name, self.action, self.slug])

    @property
    def short_scan_results(self):
        return self.scan_results if len(self.scan_results) < 200 else (self.scan_results[:200] + '..')

    # request body format: json, urlencoded ?
    # response format: json, html ?

class Parameter(BaseModel):

    class Location(models.IntegerChoices):
        UNKNOWN = 0, 'Unknown'
        PATH = 1
        QUERY = 2
        COOKIE = 3
        HEADER = 4
        BODY = 5

    # encoding of the parameter value
    class ValueEncoding(models.IntegerChoices):
        UNKNOWN = 0, 'Unknown'
        URL = 1, 'URL'
        JSON = 2, 'JSON'
        FILE = 3
        BASE64 = 4
        VDF = 5, 'VDF'

    class ParamType(models.IntegerChoices):
        UNKNOWN = 0, 'Unknown'
        INT = 1
        STRING = 2
        ARRAY = 3
        MESSAGE = 4
        INT32 = 5
        UINT32 = 6
        INT64 = 7
        UINT64 = 8
        FIXED64 = 9
        BOOLEAN = 10
        RAWBINARY = 11
        FIXED32 = 12
        ENUM = 13
        FLOAT = 14

    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    location = models.IntegerField(choices=Location.choices, default=Location.UNKNOWN)
    value_encoding = models.IntegerField(choices=ValueEncoding.choices, default=ValueEncoding.UNKNOWN)
    param_type = models.IntegerField(choices=ParamType.choices, default=ParamType.UNKNOWN)
    message_type = models.CharField(max_length=255, blank=True)
    repeated = models.BooleanField(null=True)
    required = models.BooleanField(null=True)

    def __str__(self):
        return " ".join([self.Location(self.location).label, self.ValueEncoding(self.value_encoding).label, self.ParamType(self.param_type).label, self.name])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['route', 'location', 'value_encoding', 'param_type', 'name'], name='unique_param')
        ]

class Vulnerability(BaseVulnerability):

    host = models.ForeignKey(Host, on_delete=models.CASCADE, blank = True, null = True)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, blank = True, null = True)
    interface = models.ForeignKey(Interface, on_delete=models.SET_NULL, blank = True, null = True)
    method = models.ForeignKey(Method, on_delete=models.SET_NULL, blank = True, null = True)
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, blank = True, null = True)
    parameter = models.ForeignKey(Parameter, on_delete=models.SET_NULL, blank = True, null = True)

    # class Meta:
    #     constraints = [
    #         models.CheckConstraint(
    #             name="%(app_label)s_%(class)s_one_of_host_bucket_asset",
    #             check=(
    #                 models.Q(host__isnull=True, asset__isnull=True) | models.Q(host__isnull=True, bucket__isnull=True) | models.Q(bucket__isnull=True, asset__isnull=True)
    #             ),
    #         )
    #     ]

