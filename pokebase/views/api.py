from django.core import serializers
from pokebase import models
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
import json
from bbprograms import scopeutils
from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

class APIJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(self, obj)

class APIMixin(UserPassesTestMixin):
    # access check
    def test_func(self):
        # check the api key
        key = self.request.GET.get('key', None)
        if key is not None and key == apps.get_app_config('pokebase').api_key:
            return True
        return False

@method_decorator(csrf_exempt, name='dispatch')
class APIBaseView(APIMixin, View):
    pass


# Hosts
class HostsImportView(APIBaseView):

    def post(self, request, *args, **kwargs):

        num_created = 0
        num_updated = 0
        num_failed = 0

        new_hosts = []

        for line in request:
            try:
                line = line.decode('utf-8').strip()
                if '://' in line:
                    line = line[line.find('://')+3:]
                line = scopeutils.clean_hostname(line)
                with transaction.atomic():
                    host, created = models.Host.objects.select_for_update(no_key=True).get_or_create(name=line)
                    host.in_scope = scopeutils.hostname_is_in_scope(host.name)
                    host.save()
                if created:
                    new_hosts.append(line)
                    num_created += 1
                else:
                    num_updated += 1
            except IntegrityError:
                num_failed += 1

        if num_created > 0:
            models.Notification(notification_type=models.Notification.NotificationType.HOSTS_ADDED,
                                title="New hosts added: {}".format(num_created),
                                body=new_hosts).save()

        return JsonResponse({"created": num_created, "updated": num_updated, "failed": num_failed})

class HostsExportView(APIBaseView):
    def get(self, request, *args, **kwargs):
        result_filter = Q()
        if "in_scope" in request.GET:
            result_filter = result_filter & Q(in_scope=True)
        if "reachable" in request.GET:
            result_filter = result_filter & Q(reachable=True)
        data = serializers.serialize("json", models.Host.objects.filter(result_filter), fields=('name'))
        return HttpResponse(data, content_type="application/json")


# Notification
class CreateNotificationView(APIBaseView):

    def post(self, request, *args, **kwargs):

        notification_info = json.loads(request.read())

        models.Notification(notification_type=models.Notification.NotificationType[notification_info['type'].upper()],
                                        title=notification_info['title'],
                                        body=notification_info['body']).save()


        return JsonResponse({})