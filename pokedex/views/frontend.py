from django.shortcuts import render
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views import View

class FrontendViewMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class RoutesView(FrontendViewMixin, View):
    def get(self, request, asset, *args, **kwargs):
        return render(request, 'pokedex/routes.html', {"asset":asset})

