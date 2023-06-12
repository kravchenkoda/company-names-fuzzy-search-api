from typing import Mapping, Any, Iterable, Generator

import elasticsearch
import elasticsearch.helpers

from bulk_response import BulkResponse
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
    def companies_count(self) -> str:
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

    def delete_company(self, id: int) -> None:
        """
        Delete a company document from Elasticsearch.

        Args:
            id (int): The ID of the company to delete.
        """
        es_id: str = Company(id).elasticsearch_id
        es_client.delete(index=COMPANY_INDEX_NAME, id=es_id)
        CompanyUniqueIds.remove(id)

    def get_company_by_id(self, id: int) -> Company:
        """
        Get a company object from Elasticsearch by ID.

        Args:
            id (str): The ID of the company document to retrieve.

        Returns:
            Company: The retrieved company object.
        """
        es_id: str = Company(id).elasticsearch_id
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

    def bulk_add(self, companies: Iterable[Company]) -> BulkResponse:
        """
        Bulk add multiple documents to Elasticsearch companies index.

        Args:
            companies (Iterable[Company]): The companies to add.

        Returns:
            BulkResponse object containing a number of successful operations and
            error messages with corresponding company IDs if any.
        """
        operation_type = 'index'
        actions: Generator[dict[str, Any], None, None] = (
            {
                '_op_type': operation_type,
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

        result: tuple[int, list[Mapping[str, Any]]] = elasticsearch.helpers.bulk(
            es_client,
            actions,
            raise_on_error=False
        )

        return BulkResponse(result, operation_type)

    def bulk_update(self, companies: Iterable[Company]) -> BulkResponse:
        """
        Bulk update multiple documents from Elasticsearch companies index.

        Args:
            companies (Iterable[Company]): company objects to be updated.

        Returns:
            BulkResponse object containing a number of successful operations and
            error messages with corresponding company IDs if any.
        """
        operation_type = 'update'
        internal_errors: set[tuple[int, str]] = set()

        def actions(companies):
            for company in companies:
                try:
                    yield {
                        '_op_type': operation_type,
                        '_index': COMPANY_INDEX_NAME,
                        '_id': company.elasticsearch_id,
                        '_source': company.as_es_document_for_bulk_update()
                    }
                except elasticsearch.NotFoundError as e:
                    internal_errors.add((company.id, str(e)))

        action_generator: Generator[Mapping[str, Any], None, None] = actions(companies)

        result: tuple[int, list[Mapping[str, Any]]] = elasticsearch.helpers.bulk(
            es_client,
            action_generator,
            raise_on_error=False
        )

        return BulkResponse(result, operation_type, internal_errors)

    def bulk_delete(self, companies: Iterable[Company]) -> BulkResponse:
        """
        Bulk delete multiple documents from Elasticsearch companies index.

        Args:
            companies (Iterable[Company]): company objects to be deleted.

        Returns:
            BulkResponse object containing a number of successful operations and
            error messages with corresponding company IDs if any.
        """
        operation_type = 'delete'
        internal_errors: set[tuple[int, str]] = set()

        def actions(companies):
            for company in companies:
                try:
                    yield {
                        '_op_type': operation_type,
                        '_index': COMPANY_INDEX_NAME,
                        '_id': company.elasticsearch_id,
                    }
                except elasticsearch.NotFoundError as e:
                    internal_errors.add((company.id, str(e)))

        action_generator: Generator[Mapping[str, str], None, None] = actions(companies)

        result: tuple[int, list[Mapping[str, Any]]] = elasticsearch.helpers.bulk(
            es_client,
            action_generator,
            raise_on_error=False
        )
        bulk_response = BulkResponse(result, operation_type, internal_errors)

        for action in action_generator:
            CompanyUniqueIds.remove_ids_from_cache_map(action['_id'])

        return bulk_response
