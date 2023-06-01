from dataclasses import dataclass, asdict
from typing import Iterable, Mapping, Any

import elasticsearch

from es import es_client


@dataclass
class Company:
    id_: int
    name: str
    locality: str | None = None
    industry: str | None = None
    linkedin_url: str | None = None
    domain: str | None = None

    def update(self, *fields_to_values: Iterable[tuple[str, Any]]):
        """Update the company's fields with new values.

        Args:
            *fields_to_values (Iterable[tuple[str, Any]]): The fields and their
            new values as tuples.
        """
        try:
            doc: Mapping[str, Any] = {
                field: value for field, value in fields_to_values
            }
            es_client.update(id=self.id_, doc=doc)
        except elasticsearch.NotFoundError:
            pass

    def as_elasticsearch_document_dict(self) -> Mapping[str, Any]:
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
