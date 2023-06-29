from typing import Mapping, Any, Generator

from flask_restx import Resource, Namespace, reqparse
from flask import make_response, Response
from werkzeug.exceptions import BadRequest

from api_models import company_model_no_id, company_model, multisearch_response_model
from company import Company
from search_query import SearchQuery
from companies_search_result import CompaniesSearchResult
from companies_resource import CompaniesResource

ns = Namespace('api')

parser = reqparse.RequestParser()
parser.add_argument('name', location='args')
parser.add_argument('country', location='args')
parser.add_argument('locality', location='args')
parser.add_argument('industry', location='args')
parser.add_argument('linkedin_url', location='args')
parser.add_argument('domain', location='args')


def validate_bulk_non_empty_body(func):
    """Decorator to validate that the request body is not empty."""

    def wrapper(*args, **kwargs):
        payload = ns.payload
        if len(payload) == 0 or not payload[0].keys():
            raise BadRequest('no body provided')
        else:
            return func(*args, **kwargs)

    return wrapper


def bulk_ops_company_objects_generator(
        payload: list[Mapping[str, Any]]
) -> Generator[Company, None, None]:
    """Generator function to create Company objects from a payload."""
    for company_object in payload:
        yield Company(**company_object)


def build_query_from_request(
        request_data: Mapping[str, Any],
        search: SearchQuery
) -> Mapping[str, Any]:
    """
    Return a search query from a given request data (payload or query params).

    Args:
        request_data (Mapping[str, Any]): data parsed from the request.
        search (SearchQuery): The SearchQuery instance for building queries.
    """
    query_components = []
    filters = []

    for field, value in request_data.items():
        if value:
            if field == 'name' or field == 'locality':
                query_components.append(
                    search.fuzzy_match(field, value.lower())
                )
            else:
                filters.append(
                    search.filter(field, value.lower())
                )
    search_query: Mapping[str, Any] = search.build_query(query_components, filters)
    return search_query


def get_miltisearch_body_from_payload(
        payload: list[Mapping[str, Any]],
        search: SearchQuery
) -> list[Mapping[str, Any]]:
    """
    Return a multisearch body from the given payload.

    Args:
        payload (list[Mapping[str, Any]]): The payload containing search query data.
        search (SearchQuery): The SearchQuery instance for building queries.

    Returns:
        list[Mapping[str, Any]]: The multisearch body generated from the payload.
    """
    msearch_queries: list[Mapping[str, Any]] = [
        build_query_from_request(search_object, search)
        for search_object in payload
    ]
    multisearch_body: list[Mapping[str, Any]] = \
        search.build_multisearch_body(msearch_queries)

    return multisearch_body


def get_company_from_payload(payload: list[Mapping[str, Any]]) -> Company:
    """Create a single Company object from the payload."""
    return Company(**payload[0])


@ns.route('/companies')
class CompaniesResourceRoot(Resource):
    @ns.doc(parser=parser)
    @ns.marshal_list_with(company_model)
    def get(self):
        args: Mapping[str, Any] = parser.parse_args()

        search = SearchQuery('companies')
        query: Mapping[str, Any] = build_query_from_request(args, search)

        search_results = search.perform_search(query)
        company_objects = CompaniesSearchResult.hits_to_objects(search_results)
        return company_objects, 200

    @ns.expect([company_model_no_id], validate=True)
    @validate_bulk_non_empty_body
    def post(self):
        payload: list[Mapping[str, Any]] = ns.payload
        amount_of_companies = len(payload)

        response: Response = make_response()
        response.status_code = 201

        if amount_of_companies == 1:
            company_to_add: Company = get_company_from_payload(payload)
            CompaniesResource().add_company(company_to_add)
            response.headers['Location'] = f'/api/companies/{company_to_add.id}'
        else:
            companies: Generator[Company, None, None] = bulk_ops_company_objects_generator(
                payload
            )
            CompaniesResource().bulk_add(companies)
        return response

    @ns.expect([company_model], validate=True)
    @validate_bulk_non_empty_body
    def patch(self):
        payload: list[Mapping[str, Any]] = ns.payload
        amount_of_companies = len(payload)

        response: Response = make_response()
        response.status_code = 200

        if amount_of_companies == 1:
            company_to_update: Company = get_company_from_payload(payload)
            company_to_update.update()
            response.headers['Location'] = f'/api/companies/{company_to_update.id}'
        else:
            companies: Generator[Company, None, None] = bulk_ops_company_objects_generator(
                payload
            )
            CompaniesResource.bulk_update(companies)
        return response


@ns.route('/companies/<int:id>')
class CompanyDocument(Resource):
    @ns.marshal_with(company_model)
    def get(self, id):
        search_res: Mapping[str, Any] = SearchQuery(
            'companies'
        ).perform_search_by_id(id)

        company_obj: Company = CompaniesSearchResult.hit_to_object(search_res)
        return company_obj, 200

    @ns.expect(company_model)
    def patch(self, id):
        new_fields_to_values: list[tuple[str, Any]] = [
            (key, value) for key, value in ns.payload.items()
        ]
        company_to_update = Company(id)
        company_to_update.update(new_fields_to_values)
        return {'message': 'company updated successfully'}, 200

    def delete(self, id):
        to_remove = Company(id)
        CompaniesResource().delete_company(to_remove)
        return {}, 204


@ns.route('/companies/multi-search')
class CompanyMultisearch(Resource):
    @ns.expect([company_model_no_id], validate=True)
    @ns.marshal_with(multisearch_response_model)
    def post(self):
        payload: list[Mapping[str, Any]] = ns.payload
        search = SearchQuery('companies')

        multisearch_body: list[Mapping[str, Any]] = get_miltisearch_body_from_payload(
            payload, search
        )
        multisearch_result: Generator[list[Mapping[str, Any]], None, None] = \
            search.perform_multisearch(multisearch_body)

        response: list[list[Company]] = list(map(
            CompaniesSearchResult.hits_to_objects, multisearch_result)
        )
        result = {'data': []}

        for req, resp in zip(payload, response):
            element = {'search_request': req, 'search_results': resp}
            result['data'].append(element)

        return result


@ns.route('/companies/bulk-delete')
class CompanyBulkDelete(Resource):
    def post(self):
        pass
