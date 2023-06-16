from typing import Mapping, Any
from company import Company


class CompaniesSearchResult:
    """Class for converting Elasticsearch search hits to Company objects."""

    @staticmethod
    def hit_to_object(hit: Mapping[str, Any]):
        """
        Convert a single search hit to a Company object.

        Args:
            hit (Mapping[str, Any]): The search hit to convert.

        Returns:
            Company: The Company object created from the search hit.
        """
        source_obj = hit['_source']
        company = Company(
            id=source_obj['id'],
            name=source_obj['name'],
            country=source_obj['country'],
            locality=source_obj['locality'],
            industry=source_obj['industry'],
            linkedin_url=source_obj['linkedin_url'],
            domain=source_obj['domain']
        )
        return company

    @staticmethod
    def hits_to_objects(hits: list[Mapping[str, Any]]) -> list[Company]:
        """
        Convert a list of search hits to a list of Company objects.

        Args:
            hits (list[Mapping[str, Any]]): The search hits to convert.

        Returns:
            list[Company]: The list of Company objects created from the search hits.
        """
        companies = []
        for hit in hits:
            source_obj = hit['_source']
            company = Company(
                id=source_obj['id'],
                name=source_obj['name'],
                country=source_obj['country'],
                locality=source_obj['locality'],
                industry=source_obj['industry'],
                linkedin_url=source_obj['linkedin_url'],
                domain=source_obj['domain']
            )
            companies.append(company)
        return companies
