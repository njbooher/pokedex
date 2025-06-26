from django.core.management.base import BaseCommand
import argparse
import requests
import urllib3
import socket
import re

from pokedex import models



class Command(BaseCommand):
    help = 'Populate csp headers'

    def __init__(self, *args, **kwargs):
        self.s = requests.session()
        self.csp_pattern = re.compile(r'<meta http-equiv="Content-Security-Policy" content="(?P<cspvalue>[^"]+)"',re.IGNORECASE)
        super().__init__(*args, **kwargs)

    def do_request(self, url):
        try:
            r = self.s.head(url, timeout=2)
            return r
        except requests.exceptions.Timeout:
            print(f"unreachable host {url}")
            return None
        except requests.exceptions.ConnectionError:
            #self.s = requests.session()
            print(f"connection error {url}")
            return None
        except requests.exceptions.InvalidURL:
            print(f"invalid url {url}")
            return None
        except urllib3.exceptions.MaxRetryError:
            print(f"max retries {url}")
            return None
        except requests.exceptions.SSLError:
            print(f"ssl error {url}")
            return None
        except KeyboardInterrupt:
            exit()
        except BaseException:
            print(f"something went wrong {url}")
            return None

    def handle_host(self, host):
        r = self.do_request('https://'+host.name)
        if r is None:
            print(f"https failed for {host.name}, retrying http")
            r = self.do_request('http://'+host.name)
        return r

    def handle(self, *args, **options):

        qs = models.Host.objects.all(reachable=True)

        for host in qs:

            r = self.handle_host(host)

            if r is None:
                continue
            headers = host.header_set.all()
            if len(list(filter(lambda x: x.name == "Content-Security-Policy", headers))) == 0:
                if 'Content-Security-Policy' in r.headers:
                        header = models.Header(host=host, name="Content-Security-Policy", value=r.headers["Content-Security-Policy"])
                        header.save()
                else:
                    result = self.csp_pattern.match(r.text)
                    if result is not None:
                        header = models.Header(host=host, name="Content-Security-Policy".lower(), value=result.group('cspvalue'))
                        header.save()