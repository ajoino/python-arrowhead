from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Callable, Tuple
import configparser
from arrowhead_client.logs import get_logger
from arrowhead_client.utils import get_http_method
from arrowhead_client.core_services import core_service
from arrowhead_client.core_service_forms import OrchestrationForm
from arrowhead_client.service import ConsumedHttpService


@dataclass
class ArrowheadSystem:
    """ Basic Arrowhead System class """

    system_name: str
    address: str
    port: str
    authentication_info: str

    @property
    def url(self):
        return f'{self.address}:{self.port}'

    @property
    def dto(self):
        return_dto = {
            'systemName': self.system_name,
            'address': self.address,
            'port': self.port,
            'authenticationInfo': self.authentication_info}
        return return_dto


@dataclass
class ConsumerSystem(ArrowheadSystem):
    """ Class to create Arrowhead consumer systems """

    def __init__(self, *args, keyfile: str = '', certfile: str = '', **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.keyfile = keyfile
        self.certfile = certfile
        self.logger = get_logger(self.system_name, 'debug')
        self.logger.info(f'{self.__class__.__name__} initialized at {self.address}:{self.port}')
        self._consumed_services = {}
        self._consumer_core_system_setup()

    @classmethod
    def from_cfg(cls, properties_file: str) -> ConsumerSystem:
        """ Creates a BaseArrowheadSystem from a descriptor file """

        # Parse configuration file
        config = configparser.ConfigParser()
        with open(properties_file, 'r') as properties:
            config.read_file(properties)
        config = dict(config._sections['SYSTEM'])

        # Create class instance
        system = cls(**config)

        return system

    @property
    def cert(self) -> Tuple[str, str]:
        return self.certfile, self.keyfile

    def add_consumed_service(self, service_definition: str, method_name: str) -> None:
        """ Add orchestration rule for service definition """

        orchestration_form = OrchestrationForm(self, service_definition)

        orchestrated_services = self.consume_service('orchestration-service', json=orchestration_form.dto)

        # TODO: Handle response with more than 1 service
        self._register_consumed_service(orchestrated_services, method_name)

    def consume_service(self, service: str, **kwargs):
        """ Consume registered service """
        # TODO: Add error handling for the case where the service is not
        # registered in _consumed_services
        return self._consumed_services[service].consume(
                **kwargs,
                cert=self.cert)

    def _consumer_core_system_setup(self) -> None:
        """ Sets up the mandatory core systems """
        # TODO: Add method for adding consumed services with error handling and logging
        self._register_consumed_service(core_service('orchestration-service'))

    def _register_consumed_service(self, service: ConsumedHttpService,
                                   method_name: Optional[str] = None) -> None:
        """ Register consumed services with the consumer """

        if method_name:  # Update http method if one is given
            http_method = get_http_method(method_name)
            service.method = http_method

        self._consumed_services[service.service_definition] = service


if __name__ == '__main__':
    pass