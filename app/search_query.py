import json

from es import es_client


class SearchQuery:
    """Class for performing search queries in Elasticsearch."""

    def __init__(self, index, max_results=10):
        """Initialize the SearchQuery instance.

        Args:
            index (str): The Elasticsearch index to search.
            max_results (int, optional): The maximum number of results to return. Defaults to 10.
        """
        self.index: str = index
        self.max_num_results: int = max_results

    @staticmethod
    def fuzzy_match(field: str, query: str) -> dict:
        """
        Create a fuzzy match query for a specific field.

        Args:
            field (str): The field to perform the fuzzy match on.
            query (str): The query string to search for.

        Returns:
        dict: The fuzzy match query.
        """
        query: dict = {
            'match': {
                field: {
                    'query': query,
                    'fuzziness': 'auto'
                }
            }
        }
        return query

    @staticmethod
    def exact_match(field: str, query: str) -> dict:
        """
        Create an exact match query for a specific field.

        Args:
            field (str): The field to perform the exact match on.
            query (str): The query string to search for.

        Returns:
            dict: The exact match query.
        """
        query = {
            'term': {
                field: query
            }
        }
        return query

    @staticmethod
    def filter(field: str, query: str) -> dict:
        """
        Create a filter query for a specific field.

        Args:
            field (str): The field to apply the filter on.
            query (str): The filter value to match.

       Returns:
            dict: The filter query.
        """
        query: dict = {
            'term': {
                f'{field}.keyword': query
            }
        }
        return query

    @staticmethod
    def build_query(queries: list[dict], filters: list[dict] | None = None) -> dict:
        """
        Build the full search query combining multiple queries and filters.

        Args:
            queries (list[dict]): List of queries to include in the must clause.
            filters (list[dict], optional): List of filters to include in the filter clause. Defaults to None.

        Returns:
            dict: The complete Elasticsearch query.
        """

        query: dict = {
                "bool": {
                    "must": queries,
                    "filter": filters or []
                }
            }
        return query

    def perform_search(self, query: dict) -> str:
        """
        Perform the search query and return the results.

        Args:
            query (dict): The Elasticsearch query to execute.

        Returns:
            str: JSON-formatted search results.
        """
        response = es_client.search(index=self.index, query=query, size=self.max_num_results)
        return json.dumps(response['hits']['hits'])

    def perform_search_by_id(self, document_id: int) -> str:
        """
        Perform the search query by document ID and return the results.

        Args:
            document_id (int): The ID of the document to retrieve.

        Returns:
            str: JSON-formatted search results.
        """
        response = es_client.get(self.index, document_id)
        return json.dumps(response['hits']['hits'])
