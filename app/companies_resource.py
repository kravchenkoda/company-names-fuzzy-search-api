from typing import Mapping, Any, Iterable, Generator

import elasticsearch
import elasticsearch.helpers

from company import Company
from es import es_client


class CompaniesResource:
    """Class representing a resource for managing companies in Elasticsearch.

    This class provides methods to interact with an Elasticsearch index that stores information about companies.
    It allows adding, deleting, and retrieving company documents, as well as performing bulk operations.

    Attributes:
        _es_index_name (str): The name of the Elasticsearch index used for storing company documents.

    """
    _es_index_name: str = 'companies'

    @property
    def companies_count(self):
        """
        Get the count of documents in the companies Elasticsearch index.

        Returns:
            str: The count of companies.
        """
        response = es_client.count(index=self._es_index_name)
        count: str = response['count']
        return count

    def add_company(self, company: Company) -> None:
        """
        Add a company document to Elasticsearch.

        Args:
            company (Company): The company object to add.
        """
        document: Mapping[str, Any] = {
            'name': company.name,
            'industry': company.industry,
            'locality': company.locality,
            'linkedin_url': company.linkedin_url,
            'domain': company.domain
        }
        es_client.index(index=self._es_index_name, id=company.id, document=document)

    def delete_company(self, id_: str) -> None:
        """
        Delete a company document from Elasticsearch.

        Args:
            id_ (str): The ID of the company to delete.
        """

        try:
            es_client.delete(index=self._es_index_name, id=id_)
        except elasticsearch.NotFoundError:
            pass

    def get_company_by_id(self, id_: str) -> Company:
        """
        Get a company object from Elasticsearch by ID.

        Args:
            id_ (str): The ID of the company document to retrieve.

        Returns:
            Company: The retrieved company object.
        """
        try:
            response = es_client.get(index=self._es_index_name, id=id_)
            source_obj = response['_source']
            id_ = response.get('_id')
            name = source_obj.get('name')
            industry = source_obj.get('industry')
            locality = source_obj.get('locality')
            linkedin_url = source_obj.get('linkedin_url')
            domain = source_obj.get('domain')
            return Company(
                id=id_,
                name=name,
                industry=industry,
                locality=locality,
                linkedin_url=linkedin_url,
                domain=domain
            )
        except elasticsearch.NotFoundError:
            pass

    def bulk_add(self, companies: Iterable[Company]) -> None:
        """
        Bulk add multiple documents to Elasticsearch companies index.

        Args:
            companies (Iterable[Company]): The companies to add.
        """
        actions: Generator[dict[str, Any], None, None] = (
            {
                '_op_type': 'index',
                '_index': self._es_index_name,
                '_id': company.id,
                '_source': {
                    'name': company.name,
                    'locality': company.locality,
                    'industry': company.industry,
                    'linkedin_url': company.linkedin_url,
                    'domain': company.domain
                }
            }
            for company in companies
        )
        elasticsearch.helpers.bulk(es_client, actions)

    def bulk_update(self, documents: Iterable[Mapping[str, Any]]) -> None:
        """
        Bulk update multiple documents from Elasticsearch companies index.

        Args:
            documents (Iterable[Mapping[str, Any]]): documents to be updated.
        """
        actions: Generator[Mapping[str, str], None, None] = (
            {
                '_op_type': 'update',
                '_index': self._es_index_name,
                '_id': document['id'],
                '_source': document
            }
            for document in documents
        )
        es_client.bulk(index=self._es_index_name, operations=actions)

    def bulk_delete(self, ids: Iterable[str]):
        """
        Bulk delete multiple documents from Elasticsearch companies index.

        Args:
            ids (Iterable[str]): The IDs of the documents to delete.
        """
        actions: Generator[dict[str, Any], None, None] = (
            {
                '_op_type': 'delete',
                '_index': self._es_index_name,
                '_id': id_,
            }
            for id_ in ids
        )
        try:
            elasticsearch.helpers.bulk(es_client, actions)
        except elasticsearch.helpers.BulkIndexError:
            pass

