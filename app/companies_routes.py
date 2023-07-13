from typing import Mapping, Any, Generator

from flask_restx import Resource, Namespace, reqparse
from flask import make_response, Response

from api_models import company_model_no_id, company_model, bulk_response_model, bulk_delete_request_model
from bulk_response import BulkResponse
from company import Company
from search_query import SearchQuery
from companies_search_result import CompaniesSearchResult
from companies_resource import CompaniesResource
from company_request_handler import CompanyRequestHandler
from company_api_bulk_response import CompanyApiBulkResponse


ns = Namespace('api')

q_params_parser = reqparse.RequestParser()
q_params_parser.add_argument('name', location='args')
q_params_parser.add_argument('country', location='args')
q_params_parser.add_argument('locality', location='args')
q_params_parser.add_argument('industry', location='args')
q_params_parser.add_argument('linkedin_url', location='args')
q_params_parser.add_argument('domain', location='args')

search_size_header = reqparse.RequestParser()
search_size_header.add_argument(
    'X-Max-Results-Per-Query', type=int,
    location='headers',
    help='Maximum number of search results per request, default 1, maximum 5'
)


@ns.route('/companies')
class CompaniesResourceRoot(Resource):

    @ns.expect(search_size_header, q_params_parser)
    @ns.marshal_list_with(company_model)
    @CompanyRequestHandler.handle_elastic_connection_err
    def get(self):
        args: Mapping[str, Any] = q_params_parser.parse_args()

        request_handler = CompanyRequestHandler(args)
        search: SearchQuery = request_handler.validate_search_size_header(
            search_size_header
        )
        query: Mapping[str, Any] = request_handler.build_query_from_request(search)
        search_results: list[Mapping[str, Any]] = search.perform_search(query)
        company_objects: list[Company] = CompaniesSearchResult.hits_to_objects(search_results)

        return company_objects, 200

    @ns.expect([company_model_no_id], validate=True)
    @CompanyRequestHandler.handle_elastic_connection_err
    def post(self):
        payload: list[Mapping[str, Any]] = ns.payload
        amount_of_companies = len(payload)

        response: Response = make_response()
        response.status_code = 201
        request_handler = CompanyRequestHandler(payload)
        if amount_of_companies == 1:
            company_to_add: Company = request_handler.get_company_from_payload()
            CompaniesResource().add_company(company_to_add)
            response.headers['Location'] = f'/api/companies/{company_to_add.id}'
        else:
            companies: Generator[Company, None, None] = \
                request_handler.bulk_add_update_company_obj_generator()
            es_bulk_response = CompaniesResource.bulk_add(companies)
            response: Mapping[str, list[Mapping[str, Any]]] = CompanyApiBulkResponse(
                request_handler=request_handler, es_bulk_response=es_bulk_response
            ).create_bulk_resp()

        return response

    @ns.expect([company_model], validate=True)
    @CompanyRequestHandler.handle_elastic_connection_err
    @CompanyRequestHandler.handle_elastic_not_found_err
    def patch(self):
        payload: list[Mapping[str, Any]] = ns.payload
        amount_of_companies = len(payload)

        request_handler = CompanyRequestHandler(payload)
        response: Response = make_response()
        response.status_code = 200

        if amount_of_companies == 1:
            company_to_update: Company = request_handler.get_company_from_payload()
            company_to_update.update()
        else:
            companies: Generator[Company, None, None] = \
                request_handler.bulk_add_update_company_obj_generator()
            es_bulk_response: BulkResponse = CompaniesResource.bulk_update(companies)
            response: Mapping[str, list[Mapping[str, Any]]] = CompanyApiBulkResponse(
                es_bulk_response, request_handler
            ).create_bulk_resp()

        return response


@ns.route('/companies/<int:id>')
class CompanyDocument(Resource):

    @ns.marshal_with(company_model)
    @CompanyRequestHandler.handle_elastic_connection_err
    @CompanyRequestHandler.handle_elastic_not_found_err
    def get(self, id):
        search_res: Mapping[str, Any] = SearchQuery(
           'companies'
        ).perform_search_by_id(id)

        company_obj: Company = CompaniesSearchResult.hit_to_object(search_res)
        return company_obj, 200

    @ns.expect(company_model_no_id)
    @CompanyRequestHandler.handle_elastic_connection_err
    @CompanyRequestHandler.handle_elastic_not_found_err
    def patch(self, id):
        response: Response = make_response()
        response.status_code = 200

        company_to_update = Company(id)
        company_to_update.update()

        return response

    @CompanyRequestHandler.handle_elastic_connection_err
    @CompanyRequestHandler.handle_elastic_not_found_err
    def delete(self, id):
        response: Response = make_response()
        response.status_code = 204

        to_remove = Company(id)
        CompaniesResource().delete_company(to_remove)

        return response


@ns.route('/companies/multi-search')
class CompanyMultisearch(Resource):

    @ns.expect(search_size_header, [company_model_no_id], validate=True)
    @ns.marshal_with(bulk_response_model)
    @CompanyRequestHandler.handle_elastic_connection_err
    def post(self):
        payload: list[Mapping[str, Any]] = ns.payload
        request_handler = CompanyRequestHandler(payload)
        search: SearchQuery = request_handler.validate_search_size_header(
            search_size_header
        )
        multisearch_body: list[Mapping[str, Any]] = \
            request_handler.get_miltisearch_body_from_payload(search)

        multisearch_elastic_resp: Generator[list[Mapping[str, Any]], None, None] = \
            search.perform_multisearch(multisearch_body)

        search_results: list[list[Company]] = list(map(
            CompaniesSearchResult.hits_to_objects, multisearch_elastic_resp)
        )
        response_body = CompanyApiBulkResponse.create_multisearch_resp(
            payload, search_results
        )
        return response_body, 200


@ns.route('/companies/bulk-delete')
class CompanyBulkDelete(Resource):

    @ns.expect(bulk_delete_request_model, validate=True)
    @CompanyRequestHandler.handle_elastic_connection_err
    def post(self):
        payload: list[int] = ns.payload
        request_handler = CompanyRequestHandler(payload)

        companies: Generator[Company, None, None] = request_handler. \
            bulk_delete_company_obj_generator()

        bulk_resp: BulkResponse = CompaniesResource.bulk_delete(companies)

        response_body = CompanyApiBulkResponse(
            request_handler=request_handler, es_bulk_response=bulk_resp
        ).response

        return response_body, 207
