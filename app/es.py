from os import environ
from elasticsearch import Elasticsearch

ES_HTTP_HOST = environ['ES_HTTP_HOST']
ES_PASSWORD = environ['ES_PASSWORD']

es_client = Elasticsearch(hosts=[ES_HTTP_HOST], verify_certs=False, basic_auth=('elastic', ES_PASSWORD))
