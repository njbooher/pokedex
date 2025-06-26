from django.db import models
from pokebase.models import BaseModel

# OAuth Stuff

class OAuthClient(BaseModel):
    client_id = models.CharField(max_length=255, unique=True)
    secret = models.CharField(max_length=255, blank=True)
    enabled = models.BooleanField(default=True)
    internal = models.BooleanField(default=False)
    native = models.BooleanField(default=False)
    client_service = models.CharField(max_length=255, blank=True)
    app = models.CharField(max_length=255, blank=True)
    product = models.CharField(max_length=255, blank=True)
    redirect_url = models.CharField(max_length=255, blank=True)
    full_metadata = models.TextField(blank=True)
    client_credentials_metadata = models.TextField(blank=True)

    class Meta:
        ordering = ['client_id']
        verbose_name = "OAuth Client"

class OAuthResource(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    class Meta:
        ordering = ['name']
        verbose_name = "OAuth Resource"

class OAuthPermissionsGrant(BaseModel):

    class GrantType(models.IntegerChoices):
        UNKNOWN = 0, 'Unknown'
        AUTHORIZATION_CODE = 1, 'authorization_code'
        CLIENT_CREDENTIALS = 2, 'client_credentials'
        DEVICE_AUTH = 3, 'device_auth'
        DEVICE_CODE = 4, 'device_code'
        EXCHANGE_CODE = 5, 'exchange_code'
        EXTERNAL_AUTH = 6, 'external_auth'
        PASSWORD = 7, 'password'
        TOKEN_TO_TOKEN = 8, 'token_to_token'
        BEARER = 9, 'bearer'

    name = None
    client = models.ForeignKey(OAuthClient, related_name='grants', related_query_name='grant', on_delete=models.CASCADE)
    resource = models.ForeignKey(OAuthResource, related_name='grants', related_query_name='grant', on_delete=models.CASCADE)
    grant_type = models.IntegerField(choices=GrantType.choices, default=GrantType.UNKNOWN)
    can_create = models.BooleanField(default=False)
    can_read = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    def __str__(self):
        perms = ['CREATE', 'READ', 'UPDATE', 'DELETE']
        perms_string = " | ".join([d for d, s in zip(perms, [self.can_create, self.can_read, self.can_update, self.can_delete]) if s])
        return " ".join([self.client.name, self.resource.name, self.GrantType(self.grant_type).label, perms_string])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['client', 'resource', 'grant_type'], name='unique_oauth_perm_grant')
        ]
        ordering = ['resource__name']
        verbose_name = "OAuth Permissions Grant"
