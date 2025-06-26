import re
from . import models
import django.utils.timezone
from datetime import timedelta
from django.conf import settings

regex_cache = {}
scope_cache = {}

def in_cache(cache, key):
    if "expires" not in cache:
        cache["expires"] = django.utils.timezone.now() + timedelta(hours=1)
        return False
    elif django.utils.timezone.now() > cache["expires"]:
        cache.clear()
        cache["expires"] = django.utils.timezone.now() + timedelta(hours=1)
        return False
    else:
        return key in cache

def get_in_scope_regex():

    if not in_cache(regex_cache, "in_scope"):

        in_scope_simple_and_wildcard = list(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_IN_SCOPE_SIMPLE_AND_WILDCARD).values_list('host', flat=True))
        in_scope_wildcard = list(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_IN_SCOPE_WILDCARD).values_list('host', flat=True))

        in_scope_set = {rf'^{host}$' for host in in_scope_simple_and_wildcard}
        in_scope_set.update({fr'\.{host}$' for host in in_scope_wildcard})
        in_scope = re.compile('|'.join(in_scope_set))

        regex_cache["in_scope"] = in_scope

    return regex_cache["in_scope"]

def get_in_scope_cname_regex():

    if not in_cache(regex_cache, "in_scope_cname"):

        in_scope_simple_and_wildcard = list(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_CNAMES_IN_SCOPE_SIMPLE_AND_WILDCARD).values_list('host', flat=True))
        in_scope_wildcard = list(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_CNAMES_IN_SCOPE_WILDCARD).values_list('host', flat=True))

        in_scope_set = {rf'^{host}$' for host in in_scope_simple_and_wildcard}
        in_scope_set.update({fr'\.{host}$' for host in in_scope_wildcard})
        in_scope = re.compile('|'.join(in_scope_set))

        regex_cache["in_scope_cname"] = in_scope

    return regex_cache["in_scope_cname"]

def get_in_scope_extractor_regex():

    if not in_cache(regex_cache, "in_scope_extractor"):
        in_scope_wildcard = list(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_IN_SCOPE_WILDCARD).values_list('host', flat=True))
        if len(in_scope_wildcard) == 0:
            return None

        regex_cache["in_scope_extractor"] = re.compile(r'([A-Za-z0-9.\-]+)\.(' + '|'.join({fr'{host}' for host in in_scope_wildcard}) + ')')

    return regex_cache["in_scope_extractor"]

def get_out_of_scope_regex():

    if not in_cache(regex_cache, "out_of_scope"):
        out_of_scope_simple_and_wildcard = list(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_OUT_OF_SCOPE_SIMPLE_AND_WILDCARD).values_list('host', flat=True))
        out_of_scope_wildcard = list(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_OUT_OF_SCOPE_WILDCARD).values_list('host', flat=True))
        out_of_scope_regex = list(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_OUT_OF_SCOPE_REGEX).values_list('host', flat=True))

        out_of_scope_set = {rf'^{host}$' for host in out_of_scope_simple_and_wildcard}
        out_of_scope_set.update({fr'\.{host}$' for host in out_of_scope_wildcard})
        out_of_scope_set.update(out_of_scope_regex)
        regex_cache["out_of_scope"] = re.compile('|'.join(out_of_scope_set))

    return regex_cache["out_of_scope"]

def clean_hostname(hostname):
    return re.sub(r'^(\*\.|u00[A-F0-9]{2}|(?:(?:25)+2F)+|(?:252F)+|(?:2F)+|\.)', '', hostname)

def hostname_is_in_scope(hostname):
    if settings.POKEDEX_ALLOW_ALL_HOSTNAMES:
        return True
    in_scope = get_in_scope_regex()
    return in_scope.search(hostname) is not None and not hostname_is_out_of_scope(hostname)

def hostname_is_out_of_scope(hostname):
    out_of_scope = get_out_of_scope_regex()
    return out_of_scope.search(hostname) is not None

def hostname_is_out_of_scope_for_subdomain_takeover(hostname):
    buckets_out_of_scope = get_buckets_out_of_scope_regex()
    return buckets_out_of_scope.search(hostname) is not None or hostname_is_in_scope(hostname)

def hostname_is_in_scope_for_cname(hostname):
    if settings.POKEDEX_ALLOW_ALL_HOSTNAMES:
        return True
    in_scope_for_cname = get_in_scope_cname_regex().search(hostname) is not None
    in_scope = get_in_scope_regex().search(hostname) is not None
    return (in_scope_for_cname or in_scope) and not hostname_is_out_of_scope(hostname)

def extract_in_scope_hostnames_for_httpx(input):
    hostnames = []
    in_scope_extractor_regex = get_in_scope_extractor_regex()
    if in_scope_extractor_regex is not None:
        for possible_host_match in in_scope_extractor_regex.finditer(input):
            possible_host = clean_hostname(possible_host_match.group())
            if hostname_is_in_scope_for_cname(possible_host):
                hostnames.append(possible_host)
    return hostnames

def get_wildcards_in_scope():
    if not in_cache(scope_cache, "wildcards_in_scope"):
        scope_cache["wildcards_in_scope"] = set(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_IN_SCOPE_WILDCARD).values_list('host', flat=True))
    return scope_cache["wildcards_in_scope"]

def get_wildcards_in_scope_for_amass(count=20):
    if not in_cache(scope_cache, "wildcards_in_scope_for_amass"):
        scope_cache["wildcards_in_scope_for_amass"] = set()
        rules = models.ScopeRule.objects.filter(models.ScopeRule.FILTER_IN_SCOPE_WILDCARD).order_by('last_run_amass')[:count]
        for rule in rules:
            rule.last_run_amass = django.utils.timezone.now()
            rule.save()
            scope_cache["wildcards_in_scope_for_amass"].add(rule.host)
    return scope_cache["wildcards_in_scope_for_amass"]

def get_wildcards_in_scope_for_securitytrails(count=20):
    if not in_cache(scope_cache, "wildcards_in_scope_for_securitytrails"):
        scope_cache["wildcards_in_scope_for_securitytrails"] = set()
        rules = models.ScopeRule.objects.filter(models.ScopeRule.FILTER_IN_SCOPE_WILDCARD).order_by('last_run_securitytrails')[:count]
        for rule in rules:
            rule.last_run_securitytrails = django.utils.timezone.now()
            rule.save()
            scope_cache["wildcards_in_scope_for_securitytrails"].add(rule.host)
    return scope_cache["wildcards_in_scope_for_securitytrails"]

def get_securitytrails_in_scope():
    return get_wildcards_in_scope_for_securitytrails()

def get_securitytrails_out_of_scope():
    if not in_cache(scope_cache, "securitytrails_out_of_scope"):
        scope_cache["securitytrails_out_of_scope"] = set(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_SECURITYTRAILS_OUT_OF_SCOPE).values_list('host', flat=True))
    return scope_cache["securitytrails_out_of_scope"]

def get_amassbf_in_scope():
    if not in_cache(scope_cache, "amassbf_in_scope"):
        scope_cache["amassbf_in_scope"] = set(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_AMASSBF_IN_SCOPE).values_list('host', flat=True))
    return scope_cache["amassbf_in_scope"]

def get_amass_in_scope():
    if not in_cache(scope_cache, "amass_in_scope"):
        wildcards_in_scope = get_wildcards_in_scope_for_amass()
        amass_out_of_scope = get_amass_out_of_scope()
        scope_cache["amass_in_scope"] = set([x for x in wildcards_in_scope if x not in amass_out_of_scope])
    return scope_cache["amass_in_scope"]

def get_amass_out_of_scope():
    if not in_cache(scope_cache, "amass_out_of_scope"):
        scope_cache["amass_out_of_scope"] = set(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_AMASS_OUT_OF_SCOPE).values_list('host', flat=True))
        scope_cache["amass_out_of_scope"].update(get_wildcards_out_of_scope())
        scope_cache["amass_out_of_scope"].update(get_securitytrails_out_of_scope())
        scope_cache["amass_out_of_scope"].update(get_simple_out_of_scope())
    return scope_cache["amass_out_of_scope"]

def get_amass_out_of_scope_regex():
    if not in_cache(regex_cache, "amass_out_of_scope"):
        amass_out_of_scope = get_amass_out_of_scope()
        out_of_scope_set = {fr'\.{host}$' for host in amass_out_of_scope}
        regex_cache["amass_out_of_scope"] = re.compile('|'.join(out_of_scope_set))
    return regex_cache["amass_out_of_scope"]

def get_buckets_out_of_scope():
    if not in_cache(scope_cache, "buckets_out_of_scope"):
        scope_cache["buckets_out_of_scope"] = set(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_BUCKETS_OUT_OF_SCOPE).values_list('host', flat=True))
    return scope_cache["buckets_out_of_scope"]

def get_buckets_out_of_scope_regex():
    if not in_cache(regex_cache, "buckets_out_of_scope"):
        buckets_out_of_scope = get_buckets_out_of_scope()
        out_of_scope_set = {fr'\.{host}$' for host in buckets_out_of_scope}
        regex_cache["buckets_out_of_scope"] = re.compile('|'.join(out_of_scope_set))
    return regex_cache["buckets_out_of_scope"]

def get_simple_out_of_scope():
    if not in_cache(scope_cache, "simple_out_of_scope"):
        scope_cache["simple_out_of_scope"] = set(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_OUT_OF_SCOPE_SIMPLE).values_list('host', flat=True))
    return scope_cache["simple_out_of_scope"]

def get_wildcards_out_of_scope():
    if not in_cache(scope_cache, "wildcards_out_of_scope"):
        scope_cache["wildcards_out_of_scope"] = set(models.ScopeRule.objects.filter(models.ScopeRule.FILTER_OUT_OF_SCOPE_WILDCARD).values_list('host', flat=True))
    return scope_cache["wildcards_out_of_scope"]
