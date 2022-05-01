from airflow.hooks.base import BaseHook
from elasticsearch import Elasticsearch

class ElasticHook(BaseHook):
    # conn_id(elasticsearch_default)는 자동으로 localhost:9200으로 제공됨.
    # 만약 elasticserach 정보를 변경하려면, Web UI의 Admin > Connections에서 수정
    def __init__(self, conn_id='elasticsearch_default', *args, **kwards):
        super().__init__(*args, **kwards)
        conn = self.get_connection(conn_id)

        conn_config = {}
        hosts = []

        if conn.host:
            hosts = conn.host.split(',')
        if conn.port:
            conn_config['port'] = int(conn.port)
        if conn.login:
            conn_config['http_auth'] = (conn.login, conn.password)


        self.es = Elasticsearch(hosts, **conn_config)
        self.index = conn.schema

    # elasticsearch에 대한 정보를 전달
    def info(self):
        return self.es.info()

    # 데이터를 저장할 index 지정
    def set_index(self, index):
        self.index = index 
    
    # 데이터를 es에 저장
    def add_doc(self, index, doc_type, doc):
        self.set_index(index)
        res = self.es.index(index=index, doc_type=doc_type, body=doc)
        return res