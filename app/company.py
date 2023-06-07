from dataclasses import dataclass, asdict
from typing import Iterable, Mapping, Any

import elasticsearch

from es import es_client


@dataclass
class Company:
    """
    A class representing a company.

    Attributes:
        id (int): The company's ID.
        name (str): The company's name.
        locality (str | None): The company's locality (optional).
        industry (str | None): The company's industry (optional).
        linkedin_url (str | None): The company's LinkedIn URL (optional).
        domain (str | None): The company's domain (optional).

    Methods:
        update: Update the company's fields with new values.
        as_es_document_dict: Get the company as a source object dictionary for Elasticsearch.
        as_es_document_for_bulk_update: Get the company as a source object for bulk update in Elasticsearch.
    """
    id: int
    name: str
    locality: str | None = None
    industry: str | None = None
    linkedin_url: str | None = None
    domain: str | None = None

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

    def as_es_document_for_bulk_update(self):
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
