from typing import Mapping, Any, Generator

from flask_restx import Resource, Namespace, reqparse
from flask import make_response, Response

from api_models import company_model_no_id, company_model, multisearch_response_model, bulk_delete_request_model
from company import Company
from search_query import SearchQuery
from companies_search_result import CompaniesSearchResult
from companies_resource import CompaniesResource
from company_request_handler import CompanyRequestHandler

ns = Namespace('api')

parser = reqparse.RequestParser()
parser.add_argument('name', location='args')
parser.add_argument('country', location='args')
parser.add_argument('locality', location='args')
parser.add_argument('industry', location='args')
parser.add_argument('linkedin_url', location='args')
parser.add_argument('domain', location='args')


@ns.route('/companies')
class CompaniesResourceRoot(Resource):
    @ns.doc(parser=parser)
    @ns.marshal_list_with(company_model)
    def get(self):
        args: Mapping[str, Any] = parser.parse_args()

        request_handler = CompanyRequestHandler(args)
        search = SearchQuery('companies')

        query: Mapping[str, Any] = request_handler.build_query_from_request(search)
        search_results = search.perform_search(query)
        company_objects = CompaniesSearchResult.hits_to_objects(search_results)

        return company_objects, 200

    @ns.expect([company_model_no_id], validate=True)
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
            CompaniesResource.bulk_add(companies)
        return response

    @ns.doc('perform multisearch')
    @ns.expect([company_model], validate=True)
    def patch(self):
        payload: list[Mapping[str, Any]] = ns.payload
        amount_of_companies = len(payload)

        request_handler = CompanyRequestHandler(payload)
        response: Response = make_response()
        response.status_code = 200

        if amount_of_companies == 1:
            company_to_update: Company = request_handler.get_company_from_payload()
            company_to_update.update()
            response.headers['Location'] = f'/api/companies/{company_to_update.id}'
        else:
            companies: Generator[Company, None, None] = \
                request_handler.bulk_add_update_company_obj_generator()
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
        request_handler = CompanyRequestHandler(payload)

        multisearch_body: list[Mapping[str, Any]] = \
            request_handler.get_miltisearch_body_from_payload(search)

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

    @ns.expect(bulk_delete_request_model, validate=True)
    def post(self):
        payload: list[int] = ns.payload
        request_handler = CompanyRequestHandler(payload)

        companies: Generator[Company, None, None] = request_handler.\
            bulk_delete_company_obj_generator()

        CompaniesResource.bulk_delete(companies)
        return {}, 207
