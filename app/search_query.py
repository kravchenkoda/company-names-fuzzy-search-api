from typing import Mapping, Any, Iterable

from es import es_client


class SearchQuery:
    """Class for performing search in Elasticsearch."""

    def __init__(self, index, max_results=10):
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
            queries (Iterable[Mapping[str, Any]]): List of queries to include in the must clause.
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

    def perform_search(self, query: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        Perform the search query and return the results.

        Args:
            query (Mapping[str, Any]): The Elasticsearch query to execute.

        Returns:
            Mapping[str, Any]: search results.
        """
        response = es_client.search(index=self.index, query=query, size=self.max_num_results)
        return response['hits']['hits']

    def perform_search_by_id(self, document_id: int) -> Mapping[str, Any]:
        """
        Perform the search query by document ID and return the results.

        Args:
            document_id (int): The ID of the document to retrieve.

        Returns:
            Mapping[str, Any]: The search result for the specified document ID.
        """
        response = es_client.get(index=self.index, id=document_id)
        return response['_source']
