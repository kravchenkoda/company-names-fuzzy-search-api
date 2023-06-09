from typing import Mapping, Any, Iterable, Generator

from elastic_transport import ApiResponseMeta
from elasticsearch import NotFoundError

from es import es_client


class SearchQuery:
    """Class for performing search in Elasticsearch."""

    def __init__(self, index, max_results=1):
        """Initialize the SearchQuery instance.

        Args:
            index (str): The Elasticsearch index to search.
            max_results (int, optional): The maximum number of results to return. Defaults to 10.
        """
        self.index: str = index
        self.max_num_results: int = max_results

    @staticmethod
    def fuzzy_match(field: str, query: str) -> Mapping[str, Any]:
        """
        Create a fuzzy match query for a specific field.

        Args:
            field (str): The field to perform the fuzzy match on.
            query (str): The query string to search for.

        Returns:
            Mapping[str, Any]: The fuzzy match query.
        """
        query: Mapping[str, Any] = {
            'match': {
                field: {
                    'query': query,
                    'fuzziness': 'auto'
                }
            }
        }
        return query

    @staticmethod
    def exact_match(field: str, query: str) -> Mapping[str, Any]:
        """
        Create an exact match query for a specific field.

        Args:
            field (str): The field to perform the exact match on.
            query (str): The query string to search for.

        Returns:
            Mapping[str, Any]: The term-level query.
        """
        query: Mapping[str, Any] = {
            'term': {
                field: query
            }
        }
        return query

    @staticmethod
    def filter(field: str, query: str) -> Mapping[str, Any]:
        """
        Create a filter query for a specific field.

        Args:
            field (str): The field to apply the filter on.
            query (str): The filter value to match.

       Returns:
            Mapping[str, Any]: The filter query.
        """
        query: Mapping[str, Any] = {
            'term': {
                f'{field}.keyword': query
            }
        }
        return query

    @staticmethod
    def build_query(
            queries: Iterable[Mapping[str, Any]],
            filters: Iterable[Mapping[str, Any]] | None = None
    ) -> Mapping[str, Any]:
        """
        Build the full search query combining multiple queries and filters.

        Args:
            queries (Iterable[Mapping[str, Any]]): List of queries to include in the
                                                                        must clause.
            filters (Iterable[Mapping[str, Any]], optional): List of filters to
            include in the filter clause. Defaults to None.

        Returns:
            Mapping[str, Any]: The complete search query.
        """
        query: Mapping[str, Any] = {
            "bool": {
                "must": queries,
                "filter": filters or []
            }
        }
        return query

    def perform_search(self, query: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        """
        Perform the search query and return the results.

        Args:
            query (Mapping[str, Any]): The Elasticsearch query to execute.

        Returns:
            list[Mapping[str, Any]]: search results.
        """
        response = es_client.search(
            index=self.index,
            query=query,
            size=self.max_num_results,
            request_cache=True
        )['hits']['hits']

        return response

    def perform_search_by_id(self, id_: int) -> Mapping[str, Any]:
        """
        Perform the search query by company ID and return the results.

        Args:
            id_ (int): The ID of the company to retrieve.

        Returns:
            Mapping[str, Any]: The search result for the specified company ID.

        Raises:
            elasticsearch.NotFoundError: if the document with the given id field
            does not exist.
        """
        query: Mapping[str, Any] = self.exact_match('id', id_)
        response: list[Mapping[str, Any]] = self.perform_search(
            self.build_query([query])
        )
        try:
            result = response[0]
        except IndexError:
            raise NotFoundError(
                meta=ApiResponseMeta(
                    status=404, headers={}, http_version='1.1',
                    duration=0.0, node=None),
                body='',
                message=f'document with company id {id_} '
                        f'was not found in Elasticsearch {self.index} index.')
        return result

    def build_multisearch_body(
            self,
            queries: Iterable[Mapping[str, Any]]
    ) -> list[Mapping[str, Any]]:
        """
        Build the multi-search body for executing multiple search queries.

        Args:
            queries: search queries, each query is a mapping
                    containing the desired search parameters.

        Returns:
            list[Mapping[str, Any]]: The multi-search body.
        """
        msearch_query = []
        for query in queries:
            req_head = {'request_cache': True}
            req_body = {'query': query, 'size': self.max_num_results}
            msearch_query.extend([req_head, req_body])
        return msearch_query

    def perform_multisearch(
            self,
            multisearch_body: Iterable[Mapping[str, Any]]
    ) -> Generator[list[Mapping[str, Any]], None, None]:
        """
        Perform a multi-search operation using the provided multi-search body.

        Args:
            multisearch_body: An iterable of multi-search queries.

        Yields:
            list[Mapping[str, Any]]: A list of results for each individual
            search request.
        """
        response: Mapping[str, Any] = es_client.msearch(
            searches=multisearch_body,
            index='companies'
        )
        for result in response['responses']:
            results_per_request = []
            current_num_of_results = 0
            for hit in result['hits']['hits']:
                if current_num_of_results < self.max_num_results:
                    results_per_request.append(hit)
                    current_num_of_results += 1
            yield results_per_request
