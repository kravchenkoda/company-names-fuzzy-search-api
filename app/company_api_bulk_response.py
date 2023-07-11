from typing import Mapping, Any

from company_request_handler import CompanyRequestHandler

from bulk_response import BulkResponse


class CompanyApiBulkResponse:
    def __init__(self, es_bulk_response: BulkResponse, request_handler: CompanyRequestHandler):
        self.es_bulk_response = es_bulk_response
        self.request_data = request_handler.request_data
        self.op_type: str = es_bulk_response.operation_type
        self.response_model: Mapping[str, list[Mapping[str, Any]]] = {'data': []}
        self.errors_present: bool = bool(len(self.es_bulk_response.errors))

    def bulk_delete(self):
        successes_msg = 'deleted'
        for id_ in self.request_data['ids']:
            if self.errors_present and id_ in self.es_bulk_response.errors:
                self.process_error_element(id_, self.es_bulk_response.errors[id_])
            else:
                self.process_single_bulk_element(id_, successes_msg)

    def bulk_update(self):
        successes_msg = 'updated'
        for element in self.request_data:
            if self.errors_present and element['id'] in self.es_bulk_response.errors:
                self.process_error_element(
                    element, self.es_bulk_response.errors[element['id']]
                )
            else:
                self.process_single_bulk_element(element, successes_msg)

    def bulk_add(self):
        successes_msg = 'created'
        if not self.errors_present:
            for element in self.request_data:
                self.process_single_bulk_element(element, successes_msg)

    def create_bulk_response(self):
        if self.op_type == 'index':
            self.bulk_add()
        elif self.op_type == 'delete':
            self.bulk_delete()
        elif self.op_type == 'update':
            self.bulk_update()
        return self.response_model

    def process_single_bulk_element(self, bulk_element, successes_msg):
        elem = {'request': bulk_element, 'response': successes_msg}
        self.response_model['data'].append(elem)

    def process_error_element(self, bulk_element, error_msg):
        elem = {'request': bulk_element, 'response': error_msg}
        self.response_model['data'].append(elem)
