from flask_restx import fields

from extensions import api

company_model_no_id = api.model('Company', {
    'name': fields.String,
    'country': fields.String,
    'locality': fields.String,
    'industry': fields.String,
    'linkedin_url': fields.String,
    'domain': fields.String
})

company_model = api.model('PatchCompany', {
    'id': fields.Integer,
    'name': fields.String,
    'country': fields.String,
    'locality': fields.String,
    'industry': fields.String,
    'linkedin_url': fields.String,
    'domain': fields.String
})
