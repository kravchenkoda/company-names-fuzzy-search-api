from dataclasses import dataclass, asdict, field
from typing import Iterable, Mapping, Any

import elasticsearch

from search_query import SearchQuery
from company_unique_ids import CompanyUniqueIds
from es import es_client


@dataclass
class Company:
    """
    A class representing a company.

    Attributes:
        id (int): The company's ID.
        name (str): The company's name (optional).
        locality (str | None): The company's locality (optional).
        industry (str | None): The company's industry (optional).
        linkedin_url (str | None): The company's LinkedIn URL (optional).
        domain (str | None): The company's domain (optional).

    Properties:
        elasticsearch_id (str): The company's document id in Elasticsearch.

    Methods:
        update: Update the company's fields with new values.
        as_es_document_dict: Get the company as a source object dictionary for
        Elasticsearch.

        as_es_document_for_bulk_update: Get the company as a source object for
        bulk update in Elasticsearch.
    """
    id: int = field(default_factory=CompanyUniqueIds.generate)
    name: str | None = None
    locality: str | None = None
    industry: str | None = None
    linkedin_url: str | None = None
    domain: str | None = None

    @property
    def elasticsearch_id(self) -> str:
        """
        Get the Elasticsearch ID associated with the company based on its ID.

        Returns:
            str: The Elasticsearch ID of the company.
        """
        search = SearchQuery('companies')
        query: Mapping[str, Any] = search.exact_match('id', self.id)
        response: list[Mapping[str, Any]] = search.perform_search(
            search.build_query([query])
        )
        return response[0]['_id']

    def update(self, *fields_to_values: Iterable[tuple[str, Any]]):
        """
        Update the company's fields with new values.

        Args:
            *fields_to_values (Iterable[tuple[str, Any]]): The fields and their
            new values as tuples.
        """
        try:
            doc: Mapping[str, Any] = {
                field: value for field, value in fields_to_values
            }
            es_client.update(id=self.id, doc=doc)
        except elasticsearch.NotFoundError:
            pass

    def as_es_document_dict(self) -> Mapping[str, Any]:
        """
        Get the company as a source object dictionary for Elasticsearch.

        Returns:
            Mapping[str, Any]: The company represented as a source object
            for Elasticsearch.
        """
        as_dict: Mapping[str, Any] = asdict(self)
        as_dict_without_id: Mapping[str, Any] = {
            field: value for field, value in as_dict.items() if field != 'id_'
        }
        return as_dict_without_id

    def as_es_document_for_bulk_update(self) -> Mapping[str, Any]:
        """
        Get the company as a source object for bulk update in Elasticsearch.

        Returns:
            dict: The company represented as a source object for bulk update.
        """
        as_dict: Mapping[str, Any] = asdict(self)
        as_dict_without_nulls: Mapping[str, Any] = {
            field: value for field, value in as_dict.items() if field is not None
        }
        return {
            'doc':
                as_dict_without_nulls
        }
