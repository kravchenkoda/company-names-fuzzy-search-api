from flask_restx import fields

from extensions import api

company_model_no_id = api.model('CompanyNoId', {
    'name': fields.String,
    'country': fields.String,
    'locality': fields.String,
    'industry': fields.String,
    'linkedin_url': fields.String,
    'domain': fields.String
})

company_model = api.clone('Company', company_model_no_id, {
    'id': fields.Integer
})

multisearch_response_element = api.model('MultiSearchElement', {
    'search_request': fields.Nested(company_model_no_id, skip_none=True),
    'search_results': fields.List(fields.Nested(company_model, skip_none=True))
})

multisearch_response_model = api.model('MultiSearchResponseModel', {
    'data': fields.List(fields.Nested(multisearch_response_element))
})

bulk_delete_request_model = api.model('BulkDeleteRequestModel', {
    'ids': fields.List(fields.Integer)
})
