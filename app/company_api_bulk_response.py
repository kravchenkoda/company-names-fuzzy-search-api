from typing import Mapping, Any

from company_request_handler import CompanyRequestHandler
from bulk_response import BulkResponse


class CompanyApiBulkResponse:
    """
    Class responsible for building response body for bulk add, update and delete
                                                                        operations.
    Attributes:
        es_bulk_response (BulkResponse): object containing encapsulated response data
        from the bulk add, update, delete operations in Elasticsearch.
        request_data (CompanyRequestHandler): HTTP request body.
        op_type (str): operation type, one of: 'index', 'update', 'delete'.
                                    Attribute of the BulkResponse object.
        response (Mapping[str, list[Mapping[str, Any]]]): the initial structure of the
                                        bulk API response with data to be added to it.
        errors_present (bool): indicate whether errors are present in the bulk response
                                                   from Elasticsearch.
    """
    def __init__(self, es_bulk_response: BulkResponse, request_handler: CompanyRequestHandler):
        self.es_bulk_response = es_bulk_response
        self.request_data = request_handler.request_data
        self.op_type: str = es_bulk_response.operation_type
        self.response: Mapping[str, list[Mapping[str, Any]]] = {'data': []}
        self.errors_present: bool = bool(len(self.es_bulk_response.errors))

    def create_bulk_delete_resp(self) -> None:
        """Build the bulk delete response body."""
        success_msg = 'deleted'
        for id_ in self.request_data['ids']:
            if self.errors_present and id_ in self.es_bulk_response.errors:
                error_msg: str = self.es_bulk_response.errors[id_]
                self.process_single_bulk_element(id_, error_msg)
            else:
                self.process_single_bulk_element(id_, success_msg)

    def create_bulk_update_resp(self) -> None:
        """Build the bulk update response body."""
        success_msg = 'updated'
        for element in self.request_data:
            if self.errors_present and element['id'] in self.es_bulk_response.errors:
                error_msg: str = self.es_bulk_response.errors[element['id']]
                self.process_single_bulk_element(element, error_msg)
            else:
                self.process_single_bulk_element(element, success_msg)

    def create_bulk_add_resp(self) -> None:
        """Build the bulk add response body."""
        success_msg = 'created'
        for element in self.request_data:
            self.process_single_bulk_element(element, success_msg)

    def create_bulk_resp(self) -> Mapping[str, list[Mapping[str, Any]]]:
        """
        Build the bulk response body based on the operation type.

        Returns:
            response (Mapping[str, list[Mapping[str, Any]]]): response body.
        """
        if self.op_type == 'index':
            self.create_bulk_add_resp()
        elif self.op_type == 'delete':
            self.create_bulk_delete_resp()
        elif self.op_type == 'update':
            self.create_bulk_update_resp()
        return self.response

    def process_single_bulk_element(
            self, bulk_element: Mapping[str, Any] | int,
            response_msg: str
    ) -> None:
        """
        Map and append given request (bulk_element) and response (response_msg)
                                                            to a response body.
        Args:
            bulk_element (Mapping[str, Any] | int): bulk request body element.
            response_msg (str): response to be mapped to the given request body element.
        """
        elem: Mapping[str, Any] = {'request': bulk_element, 'response': response_msg}
        self.response['data'].append(elem)
