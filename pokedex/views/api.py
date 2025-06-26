from collections import defaultdict
from django.core import serializers
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
import json
from bbprograms import scopeutils
from pokedex import models
from pokebase import models as pbmodels
from pokebase.views.api import APIBaseView, APIJSONEncoder

# Route
class RoutesImportBaseView(APIBaseView):

    GARBAGE_INTERFACE_SENTINEL = "GARBAGE_INTERFACE_SENTINEL"

    def get_ignored_interfaces(self, asset):
        return {
            self.GARBAGE_INTERFACE_SENTINEL
        }

    def make_params(self, actions, route, route_http_method, parameters):
        for param_info in parameters:

            try:
                param = models.Parameter.objects.select_for_update(no_key=True).get(route=route, name=param_info['name'])
                if len(param.notes) == 0 and len(param_info.get('description', '')) > 0:
                    actions.append("updating notes for {}".format(param_info['name']))
                    param.notes = param_info.get('description', '')
                    param.save()
            except models.Parameter.DoesNotExist:
                actions.append("creating param {} {}".format(route, param_info['name']))

                param = models.Parameter()

                param.route = route

                param.name = param_info['name']

                if route_http_method == models.Route.HTTPMethod.POST:
                    param.location = models.Parameter.Location.BODY
                else:
                    param.location = models.Parameter.Location.QUERY

                param.value_encoding = models.Parameter.ValueEncoding.URL

                param.message_type = ''
                param_raw_type = param_info.get('type', 'UNKNOWN')

                if param_raw_type == '{message}':
                    param.param_type = models.Parameter.ParamType.MESSAGE
                elif param_raw_type == 'bool':
                    param.param_type = models.Parameter.ParamType.BOOLEAN
                elif hasattr(models.Parameter.ParamType, param_raw_type.upper()):
                    param.param_type = models.Parameter.ParamType[param_raw_type.upper()]
                elif param_raw_type[0] == 'E' or param_raw_type == '{enum}':
                    param.param_type = models.Parameter.ParamType.ENUM
                else:
                    param.param_type = models.Parameter.ParamType.MESSAGE
                    param.message_type = param_raw_type


                param.repeated = param_info.get('repeated', False)
                param.required = param_info.get('required', False) or not param_info.get('optional', True)

                param.notes = param_info.get('description', '')

                param.save()

    def make_route(self, actions, method, route_info):
        action = route_info.get('action', '')
        slug = route_info.get('slug', '')
        http_method = models.Route.HTTPMethod[route_info.get('httpmethod', 'UNKNOWN')]
        try:
            route = models.Route.objects.select_for_update(no_key=True).get(method=method, action=action, slug=slug, http_method=http_method)
            if len(route.notes) == 0 and len(route_info.get('description', '')) > 0:
                actions.append("updating notes for {}".format(method))
                route.notes = route_info.get('description', '')
                route.save()
        except models.Route.DoesNotExist:
            actions.append("creating route {} {} {} {}".format(method.interface, method, action, models.Route.HTTPMethod.labels[http_method]))
            route = models.Route()
            route.method = method
            route.action = action
            route.slug = slug
            route.http_method = http_method
            route.usable = route_info.get('usable', None)
            route.response_message_type = route_info.get('response', '')
            route.source = models.Route.Source[route_info.get('_type', 'UNKNOWN').upper()]
            route.notes = route_info.get('description', '')
            route.save()
        if 'parameters' in route_info:
            self.make_params(actions, route, route.http_method, route_info['parameters'])

    def handle_method(self, actions, interface, method_name, route_info, only_new_methods=False):
        try:
            method = models.Method.objects.get(interface=interface, name=method_name)
        except models.Method.DoesNotExist:
            actions.append("creating method {} {}".format(interface, method_name))
            method = models.Method()
            method.interface = interface
            method.name = method_name
            method.save()
            if only_new_methods:
                self.make_route(actions, method, route_info)

        if not only_new_methods:
            self.make_route(actions, method, route_info)

    def handle_interface(self, actions, asset, interface_name):

        try:
            interface = models.Interface.objects.get(asset=asset, name=interface_name)
        except models.Interface.DoesNotExist:
            actions.append("creating interface {} {}".format(asset, interface_name))
            interface = models.Interface()
            interface.asset = asset
            interface.name = interface_name
            interface.save()

        return interface

class RoutesByControllerMethodImportView(RoutesImportBaseView):

    def post(self, request, asset, *args, **kwargs):

        actions = []

        raw_interfaces = json.loads(request.read())
        asset = models.Asset.objects.get(name=asset)

        ignored_interfaces = self.get_ignored_interfaces(asset)

        for interface_name in raw_interfaces:
            if interface_name in ignored_interfaces:
                continue

            interface = self.handle_interface(actions, asset, interface_name)

            for method_name in raw_interfaces[interface_name]:
                try:
                    with transaction.atomic():
                        self.handle_method(actions, interface, method_name, raw_interfaces[interface_name][method_name])
                except Exception as e:
                    actions.append(str(e))

        if len(actions) > 0:
            pbmodels.Notification(notification_type=pbmodels.Notification.NotificationType.WEBAPIS_ADDED,
                                title=f"New WebAPI updates for {asset.name}",
                                body=actions).save()

        return JsonResponse({})

class RoutesBySlugImportView(RoutesImportBaseView):

    def get_interface_and_method(self, slug, route_info):
        if 'interface' in route_info and 'method' in route_info:
            return (route_info['interface'], route_info['method'])
        else:
            parts = slug.lstrip('/').split('/')
            if len(parts) >= 2:
                return (parts[0], parts[1])
            else:
                return (self.GARBAGE_INTERFACE_SENTINEL, self.GARBAGE_INTERFACE_SENTINEL)

    def post(self, request, asset, *args, **kwargs):

        actions = []

        raw_slugs = json.loads(request.read())
        asset = models.Asset.objects.get(name=asset)

        ignored_interfaces = self.get_ignored_interfaces(asset)

        for slug in raw_slugs:

            interface_name, method_name = self.get_interface_and_method(slug, raw_slugs[slug])

            if interface_name in ignored_interfaces:
                continue

            try:
                with transaction.atomic():
                    interface = self.handle_interface(actions, asset, interface_name)
                    if method_name != self.GARBAGE_INTERFACE_SENTINEL:
                        only_new_methods = 'only_new_methods' in self.request.GET or hasattr(self, 'only_new_methods')
                        self.handle_method(actions, interface, method_name, raw_slugs[slug], only_new_methods=only_new_methods)

            except Exception as e:
                actions.append(str(e))

        if len(actions) > 0:
            pbmodels.Notification(notification_type=pbmodels.Notification.NotificationType.WEBAPIS_ADDED,
                                title=f"New Route updates for {asset.name}",
                                body=actions).save()

        return JsonResponse({})

class RoutesExportView(APIBaseView):

    def make_method_dict(self, asset, route):
        method_dict = {}

        method_dict['description'] = route.notes
        method_dict['usable'] = route.usable
        method_dict['slug'] = route.slug
        method_dict['response_message_type'] = route.response_message_type
        method_dict['_type'] = models.Route.Source(route.source).label.lower()
        method_dict['httpmethod'] = models.Route.HTTPMethod(route.http_method).label
        if route.response_message_type:
            method_dict['response'] = route.response_message_type
        method_dict['action'] = route.action
        return method_dict

    def make_param_dict(self, asset, route, method_dict, param):
        param_dict = {}
        param_dict['name'] = param.name
        param_dict['description'] = param.notes
        param_dict['location'] = models.Parameter.Location(param.location).label
        param_dict['required'] = param.required
        param_dict['repeated'] = param.repeated
        if param.param_type == models.Parameter.ParamType.MESSAGE:
            param_dict['type'] = param.message_type
        else:
            param_dict['type'] = models.Parameter.ParamType(param.param_type).label.lower()
        return param_dict

    def get(self, request, asset, *args, **kwargs):

        routes = defaultdict(lambda: defaultdict(dict))

        for route in models.Route.objects.filter(method__interface__asset__name=asset).order_by('method__interface__name', 'method__name'):

            interface = route.method.interface.name
            method = route.method.name

            method_dict = self.make_method_dict(asset, route)
            method_dict['parameters'] = []

            for param in models.Parameter.objects.filter(route=route):
                param_dict = self.make_param_dict(asset, route, method_dict, param)
                method_dict['parameters'].append(param_dict)

            routes[interface][method] = method_dict

        return JsonResponse(routes)

class DeploymentsExportView(APIBaseView):

    class Encoder(APIJSONEncoder):
        def default(self, obj):
            protocol = "https://" if obj.protocol == models.Deployment.Protocol.HTTPS else "http://"
            return ''.join([protocol, obj.host.name, obj.base_path])

    def get(self, request, *args, **kwargs):
        data = serializers.serialize("json", models.Deployment.objects.all(), cls=DeploymentsExportView.Encoder)
        return HttpResponse(data, content_type="application/json")

class InterfacesExportView(APIBaseView):
    def get(self, request, *args, **kwargs):
        data = serializers.serialize("json", models.Interface.objects.all(), fields=('name'))
        return HttpResponse(data, content_type="application/json")

class MethodsExportView(APIBaseView):
    def get(self, request, *args, **kwargs):
        data = serializers.serialize("json", models.Method.objects.all(), fields=('name'))
        return HttpResponse(data, content_type="application/json")

class SlugsExportView(APIBaseView):
    def get(self, request, *args, **kwargs):
        data = serializers.serialize("json", models.Route.objects.all(), fields=('slug'))
        return HttpResponse(data, content_type="application/json")

class ParametersExportView(APIBaseView):
    def get(self, request, *args, **kwargs):
        result_filter = Q()
        if "location" in request.GET:
            location = request.GET['location'].upper()
            if hasattr(models.Parameter.Location, location):
                result_filter = result_filter & Q(location=models.Parameter.Location[location])
        data = serializers.serialize("json", models.Parameter.objects.filter(result_filter), fields=('name'))
        return HttpResponse(data, content_type="application/json")

class DomainsInScopeExportView(APIBaseView):
    def get(self, request, *args, **kwargs):
        scope = {
            "wildcards": scopeutils.get_wildcards_in_scope()
        }
        return JsonResponse(scope, encoder=APIJSONEncoder)

# class DomainsOutOfScopeExportView(APIBaseView):
#     def get(self, request, *args, **kwargs):
#         return JsonResponse(settings.OUT_OF_SCOPE_DOMAINS, encoder=APIJSONEncoder)
