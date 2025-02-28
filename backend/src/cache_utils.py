# dishcovery/backend/src/cache_utils.py
import redis
import json
import hashlib
import logging

class QueryCache:
    def __init__(self,
                 host='localhost',
                 port=6379,
                 db=0,
                 max_memory_bytes=524288000,  # 500MB
                 do_config_set=True):
        '''
        host, port, db: standard Redis connection info
        max_memory_bytes: e.g. 500MB => 524288000
        do_config_set: if True, attempt to run CONFIG SET
        '''
        self.r = redis.Redis(host=host, port=port, db=db)
        if do_config_set:
            try:
                self.r.config_set("maxmemory", str(max_memory_bytes))
                self.r.config_set("maxmemory-policy", "allkeys-lru")
                logging.info(f"Set Redis maxmemory={max_memory_bytes} & policy=allkeys-lru")
            except redis.exceptions.ResponseError as e:
                logging.warning("Failed to set Redis maxmemory or policy. Possibly not allowed. Error: %s", e)

    def _make_key(self, query_dict):
        '''
        Convert the query_dict to a consistent JSON string, then MD5-hash it
        to produce a short unique key.
        '''
        key_str = json.dumps(query_dict, sort_keys=True)
        return "query_cache:" + hashlib.md5(key_str.encode('utf-8')).hexdigest()

    def get(self, query_dict):
        '''
        Return cached results for the given query, or None if not found
        '''
        key = self._make_key(query_dict)
        data = self.r.get(key)
        if data:
            return json.loads(data)
        return None

    def set(self, query_dict, results):
        '''
        Store final results for the given query.
        Using simple set(...).
        Eviction by LRU if memory is full.
        '''
        key = self._make_key(query_dict)
        self.r.set(key, json.dumps(results))

class DocCache:
    def __init__(self,
                 host='localhost',
                 port=6379,
                 db=1,
                 max_memory_bytes=524288000,  # 500MB
                 do_config_set=True):
        '''
        doc-level cache, separate db=1 for isolation from query-level cache.
        '''
        self.r = redis.Redis(host=host, port=port, db=db)
        if do_config_set:
            try:
                self.r.config_set("maxmemory", str(max_memory_bytes))
                self.r.config_set("maxmemory-policy", "allkeys-lru")
                logging.info(f"Set Redis (db={db}) maxmemory={max_memory_bytes} & policy=allkeys-lru")
            except redis.exceptions.ResponseError as e:
                logging.warning("Failed to set Redis maxmemory or policy. Error: %s", e)

    def get_doc(self, recipe_id):
        key = f"doc_cache:{recipe_id}"
        doc_data = self.r.get(key)
        if doc_data:
            return json.loads(doc_data)
        return None

    def set_doc(self, recipe_id, doc_data):
        key = f"doc_cache:{recipe_id}"
        self.r.set(key, json.dumps(doc_data))