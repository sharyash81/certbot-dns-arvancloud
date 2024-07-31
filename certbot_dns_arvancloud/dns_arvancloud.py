"""DNS Authenticator for ArvanCloud DNS."""
import requests

import zope.interface

from certbot import errors
from certbot import interfaces
from certbot.plugins import dns_common

from certbot_dns_arvancloud.arvancloud_client import \
    _MalformedResponseException, \
    _ArvanCloudClient, \
    _NotAuthorizedException

TTL = 120

@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for ArvanCloud
    This Authenticator uses the ArvanCloud DNS API to fulfill a dns-01 challenge.
    """

    description = 'Obtain certificates using a DNS TXT record (if you are using ArvanCloud for DNS).'

    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials = None

    @classmethod
    def add_parser_arguments(cls, add):  # pylint: disable=arguments-differ
        super(Authenticator, cls).add_parser_arguments(add, default_propagation_seconds=60)
        add('credentials', help='ArvanCloud credentials INI file.')

    def more_info(self):  # pylint: disable=missing-function-docstring,no-self-use
        return 'This plugin configures a DNS TXT record to respond to a dns-01 challenge using ' + \
               'the ArvanCloud API.'

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            'credentials',
            'ArvanCloud credentials INI file',
            {
                'api_token': 'ArvanCloud API Token from \'https://npanel.arvancloud.com/profile/api-keys\'',
            }
        )

    def _perform(self, domain, validation_name, validation):
        try:
            self._get_arvancloud_client().add_record(
                Authenticator._domain_extractor(domain),
                "TXT",
                Authenticator._subdomain_extractor(validation_name),
                validation,
                TTL,
                False
            )
        except (
                requests.ConnectionError,
                _MalformedResponseException,
                _NotAuthorizedException
        ) as exception:
            raise errors.PluginError(exception)

    def _cleanup(self, domain, validation_name, validation):
        try:
            self._get_arvancloud_client().delete_record_by_name(domain,Authenticator._subdomain_extractor(validation_name))
        except (requests.ConnectionError, _NotAuthorizedException) as exception:
            raise errors.PluginError(exception)

    def _get_arvancloud_client(self):
        return _ArvanCloudClient(
            self.credentials.conf('api_token'),
        )

    @staticmethod
    def _fqdn_format(name):
        if not name.endswith('.'):
            return '{0}.'.format(name)
        return name
    
    @staticmethod
    def _domain_extractor(subdomain):
        parts = subdomain.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        else:
            return subdomain 
    @staticmethod
    def _subdomain_extractor(fqdn):
        parts = fqdn.split('.')
        if len(parts) > 2:
            return '.'.join(parts[:-2])
        else:
            return ''

