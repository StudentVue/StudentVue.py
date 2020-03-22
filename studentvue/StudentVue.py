import zeep

from lxml import etree
from xmljson import abdera, XMLData
from urllib.parse import urlparse

from collections import OrderedDict


class UnescapingPlugin(zeep.Plugin):
    def egress(self, envelope, http_headers, operation, binding_options):
        xml_string = etree.tostring(envelope).decode()
        xml_string = xml_string.replace('&amp;', '&')
        new_envelope = etree.fromstring(xml_string)
        return new_envelope, http_headers


class StudentVue:
    """The StudentVue API class"""

    def __init__(self,
                 username: str, password: str, district_domain: str,
                 xmljson_serializer: XMLData = abdera,
                 zeep_transport: zeep.Transport = None,
                 zeep_settings: zeep.Settings = None,
                 debug: bool = False):
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

        self.xmljson_serializer = xmljson_serializer
        self.client = zeep.Client(
            'https://{0}/Service/PXPCommunication.asmx?WSDL'.format(self.district_domain),
            plugins=[UnescapingPlugin()],
            transport=zeep_transport,
            settings=zeep_settings
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

    def _make_service_request(self, method_name, **kwargs) -> str:
        param_str = '&lt;Parms&gt;'
        for key, value in kwargs.items():
            param_str += '&lt;' + key + '&gt;'
            param_str += str(value)
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

    def _xml_json_serialize(self, xml_string: str) -> OrderedDict:
        return self.xmljson_serializer.data(etree.fromstring(xml_string))

    def get_messages(self) -> OrderedDict:
        return self._xml_json_serialize(self._make_service_request('GetPXPMessages'))

    def get_calendar(self) -> OrderedDict:
        return self._xml_json_serialize(self._make_service_request('StudentCalendar'))

    def get_attendance(self) -> OrderedDict:
        return self._xml_json_serialize(self._make_service_request('Attendance'))

    def get_gradebook(self, report_period: int = 0) -> OrderedDict:
        return self._xml_json_serialize(self._make_service_request('Gradebook', ReportPeriod=report_period))

    def get_class_notes(self) -> OrderedDict:
        return self._xml_json_serialize(self._make_service_request('StudentHWNotes'))

    def get_student_info(self) -> OrderedDict:
        return self._xml_json_serialize(self._make_service_request('StudentInfo'))
