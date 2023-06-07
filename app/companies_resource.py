from typing import Mapping, Any, Iterable, Generator

import elasticsearch
import elasticsearch.helpers

from company import Company
from company_unique_ids import CompanyUniqueIds
from es import es_client

COMPANY_INDEX_NAME = 'companies'


class CompaniesResource:
    """
    Class representing a resource for managing companies in Elasticsearch.

    This class provides methods to interact with an Elasticsearch index that stores information about companies.
    It allows adding, deleting, and retrieving company documents, as well as performing bulk operations.
    """

    @property
    def companies_count(self):
        """
        Get the count of documents in the companies Elasticsearch index.

        Returns:
            str: The count of companies.
        """
        response = es_client.count(index=COMPANY_INDEX_NAME)
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
        es_client.index(index=COMPANY_INDEX_NAME, document=document)

    def delete_company(self, id_: int) -> None:
        """
        Delete a company document from Elasticsearch.

        Args:
            id_ (str): The ID of the company to delete.
        """
        es_id = Company(id_).elasticsearch_id
        es_client.delete(index=COMPANY_INDEX_NAME, id=es_id)
        CompanyUniqueIds.remove(id_)

    def get_company_by_id(self, id_: int) -> Company:
        """
        Get a company object from Elasticsearch by ID.

        Args:
            id_ (str): The ID of the company document to retrieve.

        Returns:
            Company: The retrieved company object.
        """
        es_id = Company(id_).elasticsearch_id
        response = es_client.get(index=COMPANY_INDEX_NAME, id=es_id)
        source_obj = response['_source']

        return Company(
            id=source_obj['id'],
            name=source_obj['name'],
            industry=source_obj['industry'],
            locality=source_obj['locality'],
            linkedin_url=source_obj['linkedin_url'],
            domain=source_obj['domain']
        )

    def bulk_add(
            self, companies: Iterable[Company]
    ) -> tuple[int, list[Mapping[str, Any]]]:
        """
        Bulk add multiple documents to Elasticsearch companies index.

        Args:
            companies (Iterable[Company]): The companies to add.

        Returns:
            tuple[int, list[Mapping[str, Any]]]: A tuple containing the number of
            successful requests and a list of errors with information about requests.
        """
        actions: Generator[dict[str, Any], None, None] = (
            {
                '_op_type': 'index',
                '_index': COMPANY_INDEX_NAME,
                '_source': {
                    'id': company.id,
                    'name': company.name,
                    'locality': company.locality,
                    'industry': company.industry,
                    'linkedin_url': company.linkedin_url,
                    'domain': company.domain
                }
            }
            for company in companies
        )
        return elasticsearch.helpers.bulk(es_client, actions, raise_on_error=False)

    def bulk_update(
            self, companies: Iterable[Company]
    ) -> tuple[int, list[Mapping[str, Any]]]:
        """
        Bulk update multiple documents from Elasticsearch companies index.

        Args:
            companies (Iterable[Company]): company objects to be updated.

        Returns:
            tuple[int, list[Mapping[str, Any]]]: A tuple containing the number of
            successful requests and a list of errors with information about requests.
        """
        actions: Generator[Mapping[str, Any], None, None] = (
            {
                '_op_type': 'update',
                '_index': COMPANY_INDEX_NAME,
                '_id': company.elasticsearch_id,
                '_source': company.as_es_document_for_bulk_update()
            }
            for company in companies
        )
        return elasticsearch.helpers.bulk(es_client, actions, raise_on_error=False)

    def bulk_delete(self, ids: Iterable[str]) -> tuple[int, list[Mapping[str, Any]]]:
        """
        Bulk delete multiple documents from Elasticsearch companies index.

        Args:
            ids (Iterable[str]): The IDs of the documents to delete.

        Returns:
            tuple[int, list[Mapping[str, Any]]]: A tuple containing the number of
            successful requests and a list of errors with information about requests.
        """
        actions: Generator[Mapping[str, Any], None, None] = (
            {
                '_op_type': 'delete',
                '_index': COMPANY_INDEX_NAME,
                '_id': id_,
            }
            for id_ in ids
        )
        return elasticsearch.helpers.bulk(es_client, actions, raise_on_error=False)
