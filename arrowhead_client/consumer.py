from dataclasses import dataclass
from functools import partial
import requests
from .service import ConsumedService, ProviderSystem

class BaseConsumer():
    def __init__(self):
        ''' BaseConsumer '''
        self.rule_dictionary = {}

    def add_orchestration_rule(self, rule, http_method, service_definition=None):
        ''' Add orchestration rule into rule dictionary '''

        orchestrated_services = self.query_orchestration(service_definition)

        # Currently only extracts the first service definition
        if orchestrated_services:
            orchestrated_services = orchestrated_services[0]
        elif not orchestrated_services:
            self.logger.error(f'No orchestration rules for service \'{service_definition}\'')
            orchestrated_services = None

        self.logger.debug(f'orchestrated services: {orchestrated_services}')

        self.rule_dictionary[rule] = {'method': http_method, 
                                      'service': orchestrated_services}
        self.logger.info(f'Added service consumation rule {rule}')

    def query_orchestration(self, service_definition=None):
        ''' Query orchestration for a particular service '''
        if not service_definition:
            requested_service = None
        else:
            requested_service = {
                    "serviceDefinitionRequirement": service_definition,
                    "interfaceRequirements": None,
                    "securityRequirements": None,
                    "metadataRequirements": None,
                    "versionRequirement": None,
                    "maxVersionRequirement": None,
                    "minVersionRequirement": None
                    }

        orchestration_form = {
                "commands": None,
                "orchestrationFlags": {
                    "overrideStore": True if service_definition else False
                    },
                "preferredProviders": None,
                "requestedService": requested_service,
                "requesterCloud": None,
                "requesterSystem": self.system_json
                }

        orchestration_response = requests.post(
                f'https://{self.orch_url}/orchestration',
                cert=(self.certfile, self.keyfile),
                verify=False,
                json=orchestration_form)
        # Add errors regarding orchestration response codes
        if orchestration_response.status_code != 200:
            self.logger.error(f'Orchestration for service {service_definition} failed: Orchestrator status <{orchestration_response.status_code}>')

        extracted_services = [ConsumedService.from_orch_response(orch_r)
                for orch_r in orchestration_response.json()['response']]

        return extracted_services

    def consume(self, rule, payload=None, json=None):
        ''' Consumes service under rule '''
        if not rule in self.rule_dictionary:
            self.logger.error(f'Rule \'{rule}\' is not registered')
            raise ValueError('Consumed rule is not registered')

        method, service = self.rule_dictionary[rule].values()
        if not service:
            self.logger.error(f'Rule \'{rule}\' does not have a corresponding service')
            raise RuntimeError(f'Service does not exist')

        if method.upper() == 'GET':
            response = requests.get(service.url,
                    cert=(self.certfile, self.keyfile),
                    verify=False)
        if method.upper() == 'POST':
            response = requests.post(service.url, data=payload, json=json,
                    cert=(self.certfile, self.keyfile),
                    verify=False)
        if method.upper() == 'PUT':
            response = requests.put(service.url, data=payload, json=json,
                    cert=(self.certfile, self.keyfile),
                    verify=False)
        if method.upper() == 'DELETE':
            response = requests.delete(service.url,
                    cert=(self.certfile, self.keyfile),
                    verify=False)

        if response.status_code < 200 and response.status_code >= 300:
            self.logger.error(f'Consumation of service \'{service.service_definition}\' failed: Status <{response.status_code}>')
        self.logger.info(f'Consumed service \'{service.service_definition}\': <{method}> at {service.url}')

        return response
