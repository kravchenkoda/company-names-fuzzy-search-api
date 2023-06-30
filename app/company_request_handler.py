from werkzeug.exceptions import BadRequest
from typing import Mapping, Any, Generator

from company import Company
from search_query import SearchQuery


class CompanyRequestHandler:
    """
    Handles company-related requests.
    """

    def __init__(self, request_data: Mapping[str, Any] | list[Mapping[str, Any]]):
        self.request_data = request_data
        self.validate_bulk_non_empty_body()

    def validate_bulk_non_empty_body(self) -> None:
        """
        Validate the request data for bulk operations and non-empty body.

        Raises:
            BadRequest: If the request data is empty or does not contain any keys.
        """
        if isinstance(self.request_data, list):
            if len(self.request_data) == 0 or not self.request_data[0].keys():
                raise BadRequest('no body provided')

    def bulk_ops_company_objects_generator(self) -> Generator[Company, None, None]:
        """Generator function to create Company objects from a payload."""
        for company_object in self.request_data:
            yield Company(**company_object)

    def build_query_from_request(
            self, search: SearchQuery,
            payload_company_obj: Mapping[str, Any] = None,
    ) -> Mapping[str, Any]:
        """
        Build a search query from the given request data (payload or query params).

        Args:
            search (SearchQuery): The SearchQuery instance for building queries.
            payload_company_obj (Mapping[str, Any], optional): The payload company object. Defaults to None.

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
