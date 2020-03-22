import zeep
import requests

from urllib.parse import urlparse


class StudentVue:
    """The StudentVue API class"""

    def __init__(self, username: str, password: str, district_domain: str, debug: bool = False):
        if debug:
            self._setup_debug()
        else:
            self._suppress_warnings()

        self._username = username
        self._password = password

        parse_result = urlparse(district_domain)
        if parse_result.scheme:
            self.district_domain = parse_result.netloc
        else:
            self.district_domain = parse_result.path
            if self.district_domain[len(self.district_domain) - 1] == '/':
                self.district_domain = self.district_domain[:-1]

        self.session = requests.Session()
        self.session.headers.update({
            'SOAPAction': 'http://edupoint.com/webservices/ProcessWebServiceRequest',
            'User-Agent': 'StudentVUE/8.0.26 CFNetwork/1121.2.2 Darwin/19.3.0',
            'Content-Type': 'text/xml'
        })
        self.client = zeep.Client(
            'https://{0}/Service/PXPCommunication.asmx?WSDL'.format(self.district_domain),
            transport=zeep.transports.Transport(session=self.session)
        )

    @staticmethod
    def _suppress_warnings():
        import logging
        logging.getLogger('zeep').setLevel(logging.ERROR)

    @staticmethod
    def _setup_debug():
        import logging.config

        logging.config.dictConfig({
            'version': 1,
            'formatters': {
                'verbose': {
                    'format': '%(name)s: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'zeep.transports': {
                    'level': 'DEBUG',
                    'propagate': True,
                    'handlers': ['console'],
                },
            }
        })

    def _make_service_request(self, method_name, **kwargs):
        param_str = '&lt;Parms&gt;'
        for key, value in kwargs.items():
            param_str += '&lt;' + key + '&gt;'
            param_str += value
            param_str += '&lt;/' + key + '&gt;'
        param_str += '&lt;/Parms&gt;'

        return self.client.service.ProcessWebServiceRequest(
            userID=self._username,
            password=self._password,
            skipLoginLog=1,
            parent=0,
            webServiceHandleName='PXPWebServices',
            methodName=method_name,
            paramStr=param_str
        )
