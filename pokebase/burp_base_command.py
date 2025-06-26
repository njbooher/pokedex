from django.core.management.base import BaseCommand, CommandError
from pokebase.utils import *
from pokedex.models import Asset, Interface, Method, Parameter
import argparse
import base64
import http.cookies
from collections import defaultdict
import urllib.parse
import email.parser
import json
import re
import os

class BurpBaseCommand(BaseCommand):

    junk_param_pattern = re.compile(r'\'|"|-|<|>|\(|\)|/')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('FILE', type=argparse.FileType('r'))

    def str_is_int(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def param_name_prefix(self, param_name):
        if '_' in param_name and not '[' in param_name:
            return param_name.split('_', 1)[0]
        return None

    def simplify_param_name(self, param_name):
        if '[' in param_name:
            return param_name.split('[')[0] + '[]'
        return param_name

    def param_is_array(self, param_name):
        return '[' in param_name

    def param_is_probably_junk(self, param_name):
        if self.junk_param_pattern.findall(param_name):
            return True
        return False

    def maybe_filename(self, request_path):
        filename = os.path.basename(request_path)
        if '.' in filename:
            return filename
        return ""

    def parse_http_headers(self, r, is_decoded=False):

        if is_decoded == False:
            decoded = base64.b64decode(r)
        else:
            decoded = r

        try:
            header_lines = decoded[:decoded.index(b'\r\n\r\n')].decode('UTF-8').split("\r\n")
        except:
            print(decoded)
            raise

        # remove GET line
        header_lines.pop(0)
        headers = defaultdict(list)
        for line in header_lines:
            header_name, header_value = line.split(": ", 1)
            headers[header_name.lower()].append(header_value)
        return headers

    def get_http_request_body(self, r, is_decoded=False):

        if is_decoded == False:
            decoded = base64.b64decode(r)
        else:
            decoded = r

        try:
            post_body = decoded[decoded.index(b'\r\n\r\n'):]
        except:
            print(decoded)
            raise

        return post_body

    def parse_post_body(self, content_type, body_bytes):

        if 'multipart/form-data' in content_type:
            return self.parse_post_form_multipart(content_type, body_bytes)
        elif 'application/x-www-form-urlencoded' in content_type:
            return self.parse_url_encoded_params(body_bytes, 'POST')
        elif 'application/json' in content_type:
            return self.parse_post_form_json(body_bytes)
        else:
            return []

    def parse_url_encoded_params(self, body_bytes, location):
        params = []
        if type(body_bytes) is bytes:
            try:
                body_bytes = body_bytes.decode('UTF-8')
            except UnicodeDecodeError:
                print("bailed early for bad unicode param")
                return params
        for param_name, param_value in urllib.parse.parse_qsl(body_bytes, keep_blank_values=True):

            if self.param_is_probably_junk(param_name):
                continue

            param = Parameter()
            param.name = self.simplify_param_name(param_name.strip())
            param.value_encoding = Parameter.ValueEncoding.URL
            if location == 'GET':
                param.location = Parameter.Location.QUERY
            elif location == 'POST':
                param.location = Parameter.Location.BODY
            elif location == 'COOKIE':
                param.location = Parameter.Location.COOKIE
            if self.param_is_array(param_name):
                param.param_type = Parameter.ParamType.ARRAY
            params.append(param)

        return params

    def parse_post_form_multipart(self, content_type, body_bytes):

        params = []
        msg = email.parser.BytesParser().parsebytes(b"Content-Type: " + content_type.encode('UTF-8') + b"\r\n\r\n" + body_bytes)

        for part in msg.walk():
            param_name = part.get_param('name', header='content-disposition')

            if param_name is not None:

                if self.param_is_probably_junk(param_name):
                    continue

                param = Parameter()
                param.name = self.simplify_param_name(param_name.strip())
                param.value_encoding = Parameter.ValueEncoding.URL
                if part.get_filename() is not None:
                    param.value_encoding = Parameter.ValueEncoding.FILE
                param.location = Parameter.Location.BODY
                if self.param_is_array(param_name):
                    param.type = Parameter.ParamType.ARRAY
                params.append(param)

        return params

    def parse_post_form_json(self, body_bytes):

        body_decoded = json.loads(body_bytes)
        params = []

        if type(body_decoded) is dict:
            for param_name, param_value in body_decoded.items():

                if self.param_is_probably_junk(param_name):
                    continue

                param = Parameter()
                param.name = self.simplify_param_name(param_name.strip())
                param.value_encoding = Parameter.ValueEncoding.JSON
                param.location = Parameter.Location.BODY
                if self.param_is_array(param_name):
                    param.type = Parameter.ParamType.ARRAY
                params.append(param)

        return params

    def parse_json_response_body(self, body_bytes):

        params = []

        try:
            body_decoded = json.loads(body_bytes)
        except json.decoder.JSONDecodeError:
            return params

        params.extend(self.parse_json_response_param("", body_decoded))

        return params

    def parse_json_response_param(self, param_key, param_value):

        params = []

        param_key = param_key.strip()

        if param_key != "" and not self.str_is_int(param_key):
                param = {}
                param['paramName'] = param_key
                param['paramType'] = type(param_value)
                temp_val = str(param_value).strip()
                if len(temp_val) > 30000:
                    param['paramValue'] = '<long truncated>'
                else:
                    param['paramValue'] = temp_val
                param['paramNameValueCombined'] = param['paramName'] + '=' + param['paramValue']
                params.append(param)

        if type(param_value) is dict:
            for sub_param_name, sub_param_value in param_value.items():
                params.extend(self.parse_json_response_param(sub_param_name, sub_param_value))
        elif type(param_value) is list:
            for sub_param_value in param_value:
                params.extend(self.parse_json_response_param("", sub_param_value))

        return params

    def parse_cookies(self, cookie_header):
        params = []
        try:
            for param_name, param_value in http.cookies.SimpleCookie(cookie_header).items():

                if self.param_is_probably_junk(param_name):
                    continue

                param = Parameter()
                param.name = self.simplify_param_name(param_name.strip())
                param.value_encoding = Parameter.ValueEncoding.URL
                param.location = Parameter.Location.COOKIE
                if self.param_is_array(param_name):
                    param.type = Parameter.ParamType.ARRAY
                params.append(param)

        except http.cookies.CookieError:
            pass
        return params

    def get_request_cookie_names(self, cookie_header):
        try:
            return list(http.cookies.SimpleCookie(cookie_header).keys())
        except http.cookies.CookieError:
            return []

    def get_query_params(self, query_string):
        param_names = set()
        for param_name in urllib.parse.parse_qs(query_string, keep_blank_values=True).keys():
            if '[' in param_name:
                param_names.add(param_name.split('[')[0] + '[]')
            else:
                param_names.add(param_name)
        return list(param_names)

    def get_query_param_names(self, query_string):
        param_names = set()
        for param_name in urllib.parse.parse_qs(query_string).keys():
            if '[' in param_name:
                param_names.add(param_name.split('[')[0] + '[]')
            else:
                param_names.add(param_name)
        return list(param_names)

    def get_response_cookie_names(self, cookie_header):
        cookie_names = []
        for cookie in cookie_header:
            cookie_names.append(cookie.split('=')[0])
        return cookie_names

    def get_vary(self, vary_header):
        vary = set()
        for item in vary_header.split(','):
            vary.add(item.strip().lower())
        return list(vary)

    def get_content_type(self, content_type):
        return content_type.split(';')[0]

    def get_request_path(self, request_path):
        return '/' +  request_path.lstrip('/').split('?')[0]

    # highly inefficient, but i don't care

    def ensure_asset(self, asset_name, save=False):
        try:
            asset = Asset.objects.get(name=asset_name)
        except Asset.DoesNotExist:
            asset = Asset()
            asset.name = asset_name
            if save:
                asset.save()
        return asset

    def ensure_interface(self, asset_name, interface_name, save=False):
        try:
            interface = Interface.objects.get(asset__name=asset_name, name=interface_name)
        except Interface.DoesNotExist:
            interface = Interface()
            interface.asset = self.ensure_asset(asset_name, save)
            interface.name = interface_name
            if save:
                interface.save()
        return interface

    def ensure_method(self, asset_name, interface_name, method_name, save=False):
        try:
            method = Method.objects.get(interface__asset__name=asset_name, interface__name=interface_name, name=method_name)
        except Method.DoesNotExist:
            method = Method()
            method.interface = self.ensure_interface(asset_name, interface_name, save)
            method.name = method_name
            if save:
                method.save()
        return method
