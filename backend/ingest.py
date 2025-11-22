import os
import json
import markdown
from typing import List, Dict, Any, Tuple
from pathlib import Path
import fitz
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

from backend.selectors import HTMLSelectorExtractor


class DocumentIngestion:
    """Handles document parsing, chunking, embedding, and storage in ChromaDB."""
    
    def __init__(self, persist_directory: str = "./db", reset: bool = False):
        self.persist_directory = persist_directory
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        if reset:
            try:
                self.client.delete_collection("qa_knowledge_base")
            except:
                pass
        
        try:
            self.collection = self.client.get_or_create_collection(
                name="qa_knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
        except:
            self.collection = self.client.create_collection(
                name="qa_knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=550,
            chunk_overlap=120,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.selector_extractor = HTMLSelectorExtractor()
        self.chunk_counter = 0
    
    def parse_document(self, file_path: str, file_content: bytes, filename: str) -> Tuple[str, str]:
        """
        Parse document based on file extension.
        Returns (text_content, doc_type).
        """
        ext = Path(filename).suffix.lower()
        
        if ext == '.pdf':
            return self._parse_pdf(file_content), 'spec'
        elif ext == '.md':
            return self._parse_markdown(file_content.decode('utf-8')), 'spec'
        elif ext == '.txt':
            return file_content.decode('utf-8'), 'ui_ux' if 'ui' in filename.lower() or 'ux' in filename.lower() else 'spec'
        elif ext == '.json':
            return self._parse_json(file_content.decode('utf-8')), 'api'
        elif ext == '.html' or ext == '.htm':
            return self._parse_html(file_content.decode('utf-8')), 'html_dom'
        else:
            return file_content.decode('utf-8', errors='ignore'), 'spec'
    
    def _parse_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF using PyMuPDF."""
        import io
        pdf_stream = io.BytesIO(file_content)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    
    def _parse_markdown(self, content: str) -> str:
        """Parse markdown and convert to plain text."""
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    
    def _parse_json(self, content: str) -> str:
        """Convert JSON to readable pseudo-document."""
        try:
            data = json.loads(content)
            return self._flatten_json(data)
        except json.JSONDecodeError:
            return content
    
    def _flatten_json(self, data: Any, prefix: str = '') -> str:
        """Recursively flatten JSON into readable text."""
        lines = []
        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    lines.append(f"{new_prefix}:")
                    lines.append(self._flatten_json(value, new_prefix))
                else:
                    lines.append(f"{new_prefix}: {value}")
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                new_prefix = f"{prefix}[{idx}]"
                if isinstance(item, (dict, list)):
                    lines.append(self._flatten_json(item, new_prefix))
                else:
                    lines.append(f"{new_prefix}: {item}")
        else:
            lines.append(str(data))
        return '\n'.join(lines)
    
    def _parse_html(self, content: str) -> str:
        """Extract both text and DOM structure from HTML."""
        soup = BeautifulSoup(content, 'html.parser')
        
        text_content = soup.get_text(separator='\n', strip=True)
        
        selectors_data = self.selector_extractor.extract_selectors(content)
        selector_text = self.selector_extractor.format_for_storage(selectors_data)
        
        return f"{text_content}\n\n{selector_text}"
    
    def chunk_text(self, text: str, source_document: str, doc_type: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        Returns list of chunk dictionaries.
        """
        chunks = self.text_splitter.split_text(text)
        
        chunk_dicts = []
        for idx, chunk in enumerate(chunks):
            self.chunk_counter += 1
            chunk_dict = {
                'chunk_id': f"{Path(source_document).stem}_{self.chunk_counter}",
                'text': chunk,
                'source_document': source_document,
                'doc_type': doc_type,
                'chunk_index': idx
            }
            
            if doc_type == 'html_dom':
                chunk_dict['has_selectors'] = 'SELECTOR' in chunk or '#' in chunk or 'class=' in chunk
            
            chunk_dicts.append(chunk_dict)
        
        return chunk_dicts
    
    def embed_and_store(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Generate embeddings for chunks and store in ChromaDB.
        Returns number of chunks stored.
        """
        if not chunks:
            return 0
        
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        
        ids = [chunk['chunk_id'] for chunk in chunks]
        metadatas = [{
            'source_document': chunk['source_document'],
            'doc_type': chunk['doc_type'],
            'chunk_index': chunk['chunk_index']
        } for chunk in chunks]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas
        )
        
        return len(chunks)
    
    def ingest_documents(self, uploaded_files: List[Tuple[str, bytes, str]]) -> Dict[str, Any]:
        """
        Main ingestion pipeline.
        uploaded_files: List of (file_path, file_content, filename) tuples.
        Returns summary statistics.
        """
        stats = {
            'total_files': 0,
            'total_chunks': 0,
            'files_processed': [],
            'doc_types': {}
        }
        
        for file_path, file_content, filename in uploaded_files:
            try:
                text_content, doc_type = self.parse_document(file_path, file_content, filename)
                
                chunks = self.chunk_text(text_content, filename, doc_type)
                
                num_stored = self.embed_and_store(chunks)
                
                stats['total_files'] += 1
                stats['total_chunks'] += num_stored
                stats['files_processed'].append({
                    'filename': filename,
                    'doc_type': doc_type,
                    'chunks': num_stored
                })
                
                stats['doc_types'][doc_type] = stats['doc_types'].get(doc_type, 0) + 1
                
            except Exception as e:
                stats['files_processed'].append({
                    'filename': filename,
                    'error': str(e)
                })
        
        return stats
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get current collection statistics."""
        count = self.collection.count()
        return {
            'total_chunks': count,
            'persist_directory': self.persist_directory
        }
