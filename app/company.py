from dataclasses import dataclass, asdict, field
from typing import Mapping, Any

import elasticsearch
from elastic_transport import ApiResponseMeta

import search_query as s
from company_unique_ids import CompanyUniqueIds
from es import es_client


@dataclass
class Company:
    """
    A class representing a company.

    Attributes:
        id (int): The company's ID.
        name (str): The company's name (optional).
        country (str): The company's country (optional).
        locality (str | None): The company's locality (optional).
        industry (str | None): The company's industry (optional).
        linkedin_url (str | None): The company's LinkedIn URL (optional).
        domain (str | None): The company's domain (optional).

    Properties:
        elasticsearch_id (str): The company's document id in Elasticsearch.

    Methods:
        update: Update the company's fields with new values.
        as_es_document_for_partial_update: Get the company as a source object for
        partial update operations in Elasticsearch.
    """
    id: int = field(default_factory=CompanyUniqueIds.generate)
    name: str | None = None
    country: str | None = None
    locality: str | None = None
    industry: str | None = None
    linkedin_url: str | None = None
    domain: str | None = None

    @property
    def elasticsearch_id(self) -> str:
        """
        Get the Elasticsearch company index document ID associated with the company
        based on its ID field.

        Returns:
            str: The Elasticsearch ID of the company.

        Raises:
            elasticsearch.NotFoundError: If the company is not found in Elasticsearch.
        """
        try:
            return CompanyUniqueIds.get_ids_cache_map()[self.id]
        except KeyError:
            search = s.SearchQuery('companies')
            query: Mapping[str, Any] = search.exact_match('id', self.id)
            response: list[Mapping[str, Any]] = search.perform_search(
                search.build_query([query])
            )
            if not response:
                raise elasticsearch.NotFoundError(
                    meta=ApiResponseMeta(
                        status=404, headers={}, http_version='1.1',
                        duration=0.0, node=None),
                    body='',
                    message=f'document with company id {self.id} '
                            f'was not found in Elasticsearch')
            elasticsearch_id: str = response[0]['_id']

            CompanyUniqueIds.populate_ids_cache_map(self.id, elasticsearch_id)
            return elasticsearch_id

    def update(self) -> None:
        """
        Update the company's Elasticsearch document with new values.
        """
        doc: Mapping[str, Any] = self.as_es_document_for_partial_update()
        es_client.update(index='companies', id=self.elasticsearch_id, doc=doc)

    def as_es_document_for_partial_update(self) -> Mapping[str, Any]:
        """
        Return the Elasticsearch company index source object for partial update.
        Without the 'id' field and those fields that have values of null.

        Returns:
            Mapping[str, Any]: Elasticsearch company index source object
            for partial update.
        """
        as_dict: Mapping[str, Any] = asdict(self)
        as_dict_without_nulls: Mapping[str, Any] = {
            field: value for field, value in as_dict.items()
            if value is not None and field != 'id'
        }
        return as_dict_without_nulls
