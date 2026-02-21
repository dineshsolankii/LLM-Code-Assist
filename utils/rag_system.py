#!/usr/bin/env python
"""RAG system with Redis caching layer."""
import os
import logging
import json
import hashlib
from typing import Dict, Any, Optional

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class RAGSystem:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=os.path.join(self.data_dir, 'chroma'))
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction()
        self.collections = {
            'code_examples': self._get_or_create_collection('code_examples'),
            'project_requirements': self._get_or_create_collection('project_requirements'),
            'project_structure': self._get_or_create_collection('project_structure'),
        }
        self._redis = None
        self._check_and_populate_collections()

    @property
    def redis(self):
        if self._redis is None:
            try:
                import redis as redis_lib
                url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
                self._redis = redis_lib.from_url(url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = False
        return self._redis if self._redis is not False else None

    def _get_or_create_collection(self, name):
        try:
            return self.client.get_collection(name=name, embedding_function=self.embedding_function)
        except Exception:
            return self.client.create_collection(name=name, embedding_function=self.embedding_function)

    def _check_and_populate_collections(self):
        mapping = [
            ('code_examples', 'initial_code_examples.json', ['framework', 'category']),
            ('project_requirements', 'initial_project_requirements.json', ['project_type', 'framework']),
            ('project_structure', 'initial_project_structure.json', ['framework', 'project_type']),
        ]
        for coll_name, filename, keys in mapping:
            try:
                if self.collections[coll_name].count() == 0:
                    logger.info(f'Populating {coll_name}')
                    self._load_initial_data(filename, coll_name, keys)
            except Exception as e:
                logger.error(f'Error checking {coll_name}: {e}')

    def _load_initial_data(self, filename, collection_name, meta_keys):
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            documents, metadatas, ids = [], [], []
            for item in data:
                documents.append(item['content'])
                meta = {k: item.get(k, 'general') for k in meta_keys}
                meta['source'] = item.get('source', 'local')
                metadatas.append(meta)
                ids.append(hashlib.md5(item['content'].encode()).hexdigest())
            self.collections[collection_name].add(documents=documents, metadatas=metadatas, ids=ids)
            logger.info(f'Added {len(documents)} items to {collection_name}')
        except Exception as e:
            logger.error(f'Error loading {filename}: {e}')

    def query(self, query_text, collection_name, n_results=5, filter_metadata=None):
        if collection_name not in self.collections:
            return 'No relevant information found.'
        cache_key = f'cache:rag:{hashlib.md5(f"{query_text}:{collection_name}".encode()).hexdigest()}'
        if self.redis:
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    return cached
            except Exception:
                pass
        try:
            results = self.collections[collection_name].query(
                query_texts=[query_text], n_results=n_results, where=filter_metadata,
            )
            if not results['documents'] or not results['documents'][0]:
                result = self._fetch_from_external_sources(query_text, collection_name)
            else:
                formatted = []
                for i, doc in enumerate(results['documents'][0]):
                    source = results['metadatas'][0][i].get('source', 'unknown')
                    formatted.append(f'Source: {source}\n{doc}\n')
                result = '\n'.join(formatted)
            if self.redis:
                try:
                    self.redis.setex(cache_key, 600, result)
                except Exception:
                    pass
            return result
        except Exception as e:
            logger.error(f'Error querying {collection_name}: {e}')
            return 'Error retrieving information.'

    def _fetch_from_external_sources(self, query_text, collection_name):
        results = []
        results.append(f'Source: GeeksForGeeks\nExample for {query_text}\n')
        results.append(f'Source: StackOverflow\nExample for {query_text}\n')
        return '\n'.join(results) if results else 'No relevant information found.'

    def add_document(self, content, collection_name, metadata):
        if collection_name not in self.collections:
            return False
        try:
            doc_id = hashlib.md5(content.encode()).hexdigest()
            self.collections[collection_name].add(documents=[content], metadatas=[metadata], ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f'Error adding document: {e}')
            return False

    def delete_document(self, doc_id, collection_name):
        if collection_name not in self.collections:
            return False
        try:
            self.collections[collection_name].delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f'Error deleting document: {e}')
            return False
