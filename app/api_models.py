from flask_restx import fields

from extensions import api

company_model = api.model('Company', {
    'id': fields.Integer(readonly=True),
    'name': fields.String,
    'country': fields.String,
    'locality': fields.String,
    'industry': fields.String,
    'linkedin_url': fields.String,
    'domain': fields.String
})
