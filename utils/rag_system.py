#!/usr/bin/env python
import os
import logging
import json
import hashlib
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self):
        """Initialize the RAG system."""
        # Set up the data directory
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize the ChromaDB client
        self.client = chromadb.PersistentClient(path=os.path.join(self.data_dir, 'chroma'))
        
        # Set up the embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction()
        
        # Initialize collections
        self.collections = {
            "code_examples": self._get_or_create_collection("code_examples"),
            "project_requirements": self._get_or_create_collection("project_requirements"),
            "project_structure": self._get_or_create_collection("project_structure")
        }
        
        # Initialize the data sources
        self.data_sources = {
            "geeksforgeeks": "https://www.geeksforgeeks.org/",
            "stackoverflow": "https://stackoverflow.com/"
        }
        
        # Check if we need to populate the collections
        self._check_and_populate_collections()
    
    def _get_or_create_collection(self, name: str):
        """Get or create a collection."""
        try:
            return self.client.get_collection(name=name, embedding_function=self.embedding_function)
        except:
            return self.client.create_collection(name=name, embedding_function=self.embedding_function)
    
    def _check_and_populate_collections(self):
        """Check if collections need to be populated and do so if necessary."""
        # Check if code_examples collection is empty
        if self.collections["code_examples"].count() == 0:
            logger.info("Populating code_examples collection with initial data")
            self._populate_code_examples()
        
        # Check if project_requirements collection is empty
        if self.collections["project_requirements"].count() == 0:
            logger.info("Populating project_requirements collection with initial data")
            self._populate_project_requirements()
        
        # Check if project_structure collection is empty
        if self.collections["project_structure"].count() == 0:
            logger.info("Populating project_structure collection with initial data")
            self._populate_project_structure()
    
    def _populate_code_examples(self):
        """Populate the code_examples collection with initial data."""
        # Load initial data from JSON file if available
        initial_data_path = os.path.join(self.data_dir, 'initial_code_examples.json')
        
        if os.path.exists(initial_data_path):
            try:
                with open(initial_data_path, 'r') as f:
                    initial_data = json.load(f)
                
                # Add the data to the collection
                documents = []
                metadatas = []
                ids = []
                
                for item in initial_data:
                    documents.append(item["content"])
                    metadatas.append({
                        "source": item.get("source", "local"),
                        "framework": item.get("framework", "python"),
                        "category": item.get("category", "general")
                    })
                    # Create a deterministic ID based on the content
                    item_id = hashlib.md5(item["content"].encode()).hexdigest()
                    ids.append(item_id)
                
                self.collections["code_examples"].add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Added {len(documents)} initial code examples")
            except Exception as e:
                logger.error(f"Error loading initial code examples: {str(e)}")
    
    def _populate_project_requirements(self):
        """Populate the project_requirements collection with initial data."""
        # Load initial data from JSON file if available
        initial_data_path = os.path.join(self.data_dir, 'initial_project_requirements.json')
        
        if os.path.exists(initial_data_path):
            try:
                with open(initial_data_path, 'r') as f:
                    initial_data = json.load(f)
                
                # Add the data to the collection
                documents = []
                metadatas = []
                ids = []
                
                for item in initial_data:
                    documents.append(item["content"])
                    metadatas.append({
                        "source": item.get("source", "local"),
                        "project_type": item.get("project_type", "general"),
                        "framework": item.get("framework", "python")
                    })
                    # Create a deterministic ID based on the content
                    item_id = hashlib.md5(item["content"].encode()).hexdigest()
                    ids.append(item_id)
                
                self.collections["project_requirements"].add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Added {len(documents)} initial project requirements")
            except Exception as e:
                logger.error(f"Error loading initial project requirements: {str(e)}")
    
    def _populate_project_structure(self):
        """Populate the project_structure collection with initial data."""
        # Load initial data from JSON file if available
        initial_data_path = os.path.join(self.data_dir, 'initial_project_structure.json')
        
        if os.path.exists(initial_data_path):
            try:
                with open(initial_data_path, 'r') as f:
                    initial_data = json.load(f)
                
                # Add the data to the collection
                documents = []
                metadatas = []
                ids = []
                
                for item in initial_data:
                    documents.append(item["content"])
                    metadatas.append({
                        "source": item.get("source", "local"),
                        "framework": item.get("framework", "python"),
                        "project_type": item.get("project_type", "general")
                    })
                    # Create a deterministic ID based on the content
                    item_id = hashlib.md5(item["content"].encode()).hexdigest()
                    ids.append(item_id)
                
                self.collections["project_structure"].add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Added {len(documents)} initial project structures")
            except Exception as e:
                logger.error(f"Error loading initial project structures: {str(e)}")
    
    def query(self, query_text: str, collection_name: str, n_results: int = 5, 
             filter_metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Query the RAG system for relevant information.
        
        Args:
            query_text: The query text
            collection_name: The name of the collection to query
            n_results: The number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            A string containing the relevant information
        """
        if collection_name not in self.collections:
            logger.error(f"Collection {collection_name} not found")
            return "No relevant information found."
        
        try:
            # Query the collection
            results = self.collections[collection_name].query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Process the results
            if not results["documents"] or not results["documents"][0]:
                # If no results from the collection, try to fetch from external sources
                return self._fetch_from_external_sources(query_text, collection_name)
            
            # Format the results
            formatted_results = []
            for i, doc in enumerate(results["documents"][0]):
                source = results["metadatas"][0][i].get("source", "unknown")
                formatted_results.append(f"Source: {source}\n{doc}\n")
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Error querying collection {collection_name}: {str(e)}")
            return "Error retrieving information."
    
    def _fetch_from_external_sources(self, query_text: str, collection_name: str) -> str:
        """
        Fetch information from external sources when the collection doesn't have relevant data.
        
        Args:
            query_text: The query text
            collection_name: The name of the collection
            
        Returns:
            A string containing the relevant information
        """
        logger.info(f"Fetching information from external sources for query: {query_text}")
        
        results = []
        
        # Try GeeksForGeeks
        try:
            geeks_results = self._search_geeksforgeeks(query_text)
            if geeks_results:
                results.append(f"Source: GeeksForGeeks\n{geeks_results}\n")
        except Exception as e:
            logger.error(f"Error searching GeeksForGeeks: {str(e)}")
        
        # Try StackOverflow
        try:
            stackoverflow_results = self._search_stackoverflow(query_text)
            if stackoverflow_results:
                results.append(f"Source: StackOverflow\n{stackoverflow_results}\n")
        except Exception as e:
            logger.error(f"Error searching StackOverflow: {str(e)}")
        
        if not results:
            return "No relevant information found."
        
        return "\n".join(results)
    
    def _search_geeksforgeeks(self, query_text: str) -> str:
        """Search GeeksForGeeks for relevant information."""
        # This is a simplified implementation
        # In a real system, you would use the GeeksForGeeks API or web scraping
        return f"Example code and explanation for {query_text} from GeeksForGeeks."
    
    def _search_stackoverflow(self, query_text: str) -> str:
        """Search StackOverflow for relevant information."""
        # This is a simplified implementation
        # In a real system, you would use the StackOverflow API or web scraping
        return f"Example code and explanation for {query_text} from StackOverflow."
    
    def add_document(self, content: str, collection_name: str, metadata: Dict[str, Any]) -> bool:
        """
        Add a document to the RAG system.
        
        Args:
            content: The document content
            collection_name: The name of the collection
            metadata: The document metadata
            
        Returns:
            True if successful, False otherwise
        """
        if collection_name not in self.collections:
            logger.error(f"Collection {collection_name} not found")
            return False
        
        try:
            # Create a deterministic ID based on the content
            doc_id = hashlib.md5(content.encode()).hexdigest()
            
            # Add the document to the collection
            self.collections[collection_name].add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Added document to collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document to collection {collection_name}: {str(e)}")
            return False
    
    def delete_document(self, doc_id: str, collection_name: str) -> bool:
        """
        Delete a document from the RAG system.
        
        Args:
            doc_id: The document ID
            collection_name: The name of the collection
            
        Returns:
            True if successful, False otherwise
        """
        if collection_name not in self.collections:
            logger.error(f"Collection {collection_name} not found")
            return False
        
        try:
            # Delete the document from the collection
            self.collections[collection_name].delete(ids=[doc_id])
            
            logger.info(f"Deleted document {doc_id} from collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document from collection {collection_name}: {str(e)}")
            return False
