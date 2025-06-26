from django.conf import settings
from django.core import serializers
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from pokecloud import models
from pokebase import models as pbmodels
from pokebase.views.api import APIBaseView

# Buckets

class BucketsImportView(APIBaseView):

    endings = {
        "AWS": ".s3.amazonaws.com",
        "GCP": ".storage.googleapis.com"
    }

    def post(self, request, *args, **kwargs):

        num_created = 0
        num_updated = 0
        num_failed = 0

        new_buckets = []

        provider = "AWS"

        if "provider" in request.GET:
            provider = request.GET["provider"]

        name_ending = self.endings[provider]

        for line in request:
            try:
                bucket_name = line.decode('utf-8').strip()
                if not bucket_name.endswith(name_ending):
                    bucket_name += name_ending
                with transaction.atomic():
                    bucket, created  = models.Bucket.objects.select_for_update(no_key=True).get_or_create(name=bucket_name, provider=models.Bucket.Provider[provider])
                    bucket.save()
                if created:
                    new_buckets.append(bucket_name)
                    num_created += 1
                else:
                    num_updated += 1
            except IntegrityError:
                num_failed += 1

        if num_created > 0 and settings.POKEDEX_NEW_BUCKET_NOTIFICATIONS:
            pbmodels.Notification(notification_type=pbmodels.Notification.NotificationType.BUCKETS_ADDED,
                                title="New buckets added: {}".format(num_created),
                                body=new_buckets).save()

        return JsonResponse({"created": num_created, "updated": num_updated, "failed": num_failed})

class BucketsExportView(APIBaseView):
    def get(self, request, *args, **kwargs):
        result_filter = Q()
        if "exists" in request.GET:
            result_filter = result_filter & Q(exists=True)
        if "noignore" in request.GET:
            result_filter = result_filter & Q(ignore=False)
        if "noowner" in request.GET:
            result_filter = result_filter & Q(owner=None)
        data = serializers.serialize("json", models.Bucket.objects.filter(result_filter), fields=('name'))
        return HttpResponse(data, content_type="application/json")
