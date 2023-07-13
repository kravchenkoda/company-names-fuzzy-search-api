from typing import Mapping, Any, Generator
from functools import wraps

import elastic_transport
import elasticsearch
import werkzeug.exceptions
from flask_restx.reqparse import RequestParser
from werkzeug.exceptions import BadRequest, ServiceUnavailable

from company import Company
from search_query import SearchQuery


class CompanyRequestHandler:
    """
    Handles company-related requests.
    """

    def __init__(self, request_data: Mapping[str, Any] | list[Mapping[str, Any]] | list[int]):
        self.request_data = request_data
        self.validate_bulk_non_empty_body()

    @staticmethod
    def handle_elastic_connection_err(func):
        """
        Decorator function to catch elastic_transport.Connection errors
                                            and return 503 status code.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except elastic_transport.ConnectionError:
                raise ServiceUnavailable
        return wrapper

    @staticmethod
    def handle_elastic_not_found_err(func):
        """
        Decorator function to catch elasticsearch.NotFound errors
                                            and return 404 status code.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except elasticsearch.NotFoundError:
                raise werkzeug.exceptions.NotFound
        return wrapper

    @staticmethod
    def handle_elastic_bad_request_err(func):
        """
        Decorator function to catch elasticsearch.BadRequest errors
                                            and return 400 status code.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except elasticsearch.BadRequestError as e:
                err_msg = e.body['error']['root_cause'][0]['reason']
                raise werkzeug.exceptions.BadRequest(err_msg)
        return wrapper

    def validate_bulk_non_empty_body(self) -> None:
        """
        Validate the request data of bulk operations for a non-empty body.

        Raises:
            BadRequest: If the request data is empty or does not contain any keys.
        """
        bad_request = BadRequest('no body provided')
        req_data = self.request_data

        if isinstance(req_data, list):
            if len(self.request_data) == 0 or not req_data[0].keys():
                raise bad_request
        elif 'ids' in req_data.keys() and not req_data['ids']:
            raise bad_request

    @staticmethod
    def validate_payload_company_obj(payload_company_obj: Mapping[str, Any]):
        """
        Validates the payload company object against the attributes of the
                                                            Company class.
        Args:
            payload_company_obj (Mapping[str, Any]): The payload company object.

        Raises:
            BadRequest: If the payload company object contains extra attributes not
                                                        present in the Company class.
        """
        payload_attrs = set(payload_company_obj.keys())
        company_attrs = set(vars(Company).keys())
        company_attrs.add('id')
        extra_attrs = payload_attrs - company_attrs
        if extra_attrs:
            raise BadRequest(
                f'Company does not have following attribute(s): {", ".join(extra_attrs)}. '
                f'Given object: {payload_company_obj}'
            )

    def bulk_add_update_company_obj_generator(self) -> Generator[Company, None, None]:
        """
        Generator function to create Company objects from the bulk add or bulk
                                                                    update payload.
        """
        for company_object in self.request_data:
            self.validate_payload_company_obj(company_object)
            yield Company(**company_object)

    def bulk_delete_company_obj_generator(self) -> Generator[Company, None, None]:
        """
        Generator function to create Company objects from the bulk delete payload.
        """
        ids: list[int] = self.request_data['ids']
        for id in ids:
            yield Company(id=id)

    def build_query_from_request(
            self, search: SearchQuery,
            payload_company_obj: Mapping[str, Any] = None,
    ) -> Mapping[str, Any]:
        """
        Build a search query from the given request data (payload or query params).

        Args:
            search (SearchQuery): The SearchQuery instance for building queries.
            payload_company_obj (Mapping[str, Any], optional): The payload company
                                                            object. Defaults to None.

        Returns:
            Mapping[str, Any]: The search query.
        """
        if payload_company_obj:
            reqeust_data = payload_company_obj
        else:
            reqeust_data = self.request_data

        query_components = []
        filters = []

        for field, value in reqeust_data.items():
            if value:
                if field == 'name' or field == 'locality':
                    query_components.append(
                        search.fuzzy_match(field, value.lower())
                    )
                else:
                    filters.append(
                        search.filter(field, value.lower())
                    )
        search_query: Mapping[str, Any] = search.build_query(query_components, filters)
        return search_query

    def get_miltisearch_body_from_payload(
            self, search: SearchQuery
    ) -> list[Mapping[str, Any]]:
        """
        Return a multisearch body from the given payload.

        Args:
            search (SearchQuery): The SearchQuery instance for building queries.

        Returns:
            list[Mapping[str, Any]]: The multisearch body generated from the payload.
        """

        msearch_queries: list[Mapping[str, Any]] = [
            self.build_query_from_request(
                search, payload_company_obj=search_company_object
            )
            for search_company_object in self.request_data
        ]
        msearch_body: list[Mapping[str, Any]] = \
            search.build_multisearch_body(msearch_queries)

        return msearch_body

    def get_company_from_payload(self) -> Company:
        """Create a single Company object from the payload."""
        payload = self.request_data
        return Company(**payload[0])

    @staticmethod
    def validate_search_size_header(search_size_header_parser: RequestParser) -> SearchQuery:
        """
        Validate the X-Max-Results-Per-Query header value and create a SearchQuery
                                                                            object.
        Args:
            search_size_header_parser: The parser for the search size header.

        Returns:
            A SearchQuery object with the specified max_results value.

        Raises:
            BadRequest: If the X-Max-Results-Per-Query header value is more than 5.
        """
        max_results = search_size_header_parser.parse_args()['X-Max-Results-Per-Query']

        if max_results is None:
            max_results = 1

        if max_results < 1 or max_results > 5:
            raise BadRequest(
                'X-Max-Results-Per-Query header value must be an integer '
                'between 1 and 5.'
            )
        return SearchQuery('companies', max_results)
