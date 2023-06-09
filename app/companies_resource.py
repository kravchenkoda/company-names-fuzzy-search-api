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

    Properties:
        companies_count: number of documents the companies Elasticsearch index.

    Methods:
        companies_count() -> str:
            Get the count of documents in the companies Elasticsearch index.
        add_company(company: Company) -> None:
            Add a company document to Elasticsearch.
        delete_company(company: Company) -> None:
            Delete a company document from Elasticsearch.
        get_company_by_id(id: int) -> Company:
            Get a company object from Elasticsearch by ID.
        bulk_add(companies: Iterable[Company]) -> BulkResponse:
            Bulk add multiple documents to Elasticsearch companies index.
        bulk_update(companies: Iterable[Company]) -> BulkResponse:
            Bulk update multiple documents from Elasticsearch companies index.
        bulk_delete(companies: Iterable[Company]) -> BulkResponse:
            Bulk delete multiple documents from Elasticsearch companies index.
    """
    @property
    def companies_count(self) -> int:
        """
        Get the count of documents in the companies Elasticsearch index.

        Returns:
            str: The count of companies.
        """
        response = es_client.count(index=COMPANY_INDEX_NAME)
        count = int(response['count'])
        return count

    @staticmethod
    def add_company(company: Company) -> None:
        """
        Add a company document to Elasticsearch.

        Args:
            company (Company): The company object to add.
        """
        document: Mapping[str, Any] = {
            'id': company.id,
            'name': company.name,
            'country': company.country,
            'industry': company.industry,
            'locality': company.locality,
            'linkedin_url': company.linkedin_url,
            'domain': company.domain
        }
        es_client.index(index=COMPANY_INDEX_NAME, document=document)

    @staticmethod
    def delete_company(company: Company) -> None:
        """
        Delete a company document from Elasticsearch.

        Args:
            company (Company): company object to delete.
        """
        es_client.delete(index=COMPANY_INDEX_NAME, id=company.elasticsearch_id)
        CompanyUniqueIds.remove(company.id)
        CompanyUniqueIds.remove_ids_from_cache_map(company.id)

    @staticmethod
    def get_company_by_id(id: int) -> Company:
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
            country=source_obj['country'],
            industry=source_obj['industry'],
            locality=source_obj['locality'],
            linkedin_url=source_obj['linkedin_url'],
            domain=source_obj['domain']
        )

    @staticmethod
    def bulk_add(companies: Iterable[Company]) -> BulkResponse:
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
                    'country': company.country,
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

    @staticmethod
    def bulk_update(companies: Iterable[Company]) -> BulkResponse:
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
                        '_source': {
                            'doc': company.as_es_document_for_partial_update()
                        }
                    }
                except elasticsearch.NotFoundError as e:
                    err_msg = e.error
                    internal_errors.add((company.id, err_msg))
                except elasticsearch.BadRequestError as e:
                    err_msg = e.info['error']['root_cause'][0]['reason']
                    internal_errors.add((company.id, err_msg))

        action_generator: Generator[Mapping[str, Any], None, None] = actions(companies)

        result: tuple[int, list[Mapping[str, Any]]] = elasticsearch.helpers.bulk(
            es_client,
            action_generator,
            raise_on_error=False
        )

        return BulkResponse(result, operation_type, internal_errors)

    @staticmethod
    def bulk_delete(companies: Iterable[Company]) -> BulkResponse:
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
                    err_msg = e.error
                    internal_errors.add((company.id, err_msg))
                except elasticsearch.BadRequestError as e:
                    err_msg = e.info['error']['root_cause'][0]['reason']
                    internal_errors.add((company.id, err_msg))

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
