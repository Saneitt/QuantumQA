import os
import json
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
import google.generativeai as genai


class RAGEngine:
    """RAG (Retrieval-Augmented Generation) engine for test case generation."""
    
    def __init__(self, persist_directory: str = "./db"):
        self.persist_directory = persist_directory
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        try:
            self.collection = self.client.get_collection("qa_knowledge_base")
        except:
            self.collection = self.client.create_collection(
                name="qa_knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
        
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=gemini_api_key)
    
    def retrieve_context(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        """
        Retrieve top-K relevant chunks for a query.
        Returns list of retrieved chunks with metadata.
        """
        query_embedding = self.embedding_model.encode([query], show_progress_bar=False)[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        retrieved_chunks = []
        if results['documents'] and len(results['documents']) > 0:
            for idx in range(len(results['documents'][0])):
                chunk = {
                    'text': results['documents'][0][idx],
                    'metadata': results['metadatas'][0][idx],
                    'distance': results['distances'][0][idx] if results.get('distances') else None
                }
                retrieved_chunks.append(chunk)
        
        return retrieved_chunks
    
    def compile_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Compile retrieved chunks into a single context string."""
        context_parts = []
        
        for idx, chunk in enumerate(chunks, 1):
            source = chunk['metadata'].get('source_document', 'unknown')
            doc_type = chunk['metadata'].get('doc_type', 'unknown')
            text = chunk['text']
            
            context_parts.append(f"[Source {idx}: {source} ({doc_type})]\n{text}\n")
        
        return '\n---\n'.join(context_parts)
    
    def generate_test_cases(self, user_query: str, retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate test cases using Gemini API with strict grounding rules.
        Returns list of test case dictionaries.
        """
        context = self.compile_context(retrieved_chunks)
        
        source_docs = list(set([chunk['metadata'].get('source_document', 'unknown') for chunk in retrieved_chunks]))
        
        system_prompt = """You are an expert QA automation engineer specializing in documentation-grounded test case generation.

CRITICAL RULES:
1. Generate test cases ONLY based on features explicitly mentioned in the provided documentation
2. Every test case MUST reference its source document(s) in the "Grounded_In" field
3. Do NOT hallucinate features, functionality, or behaviors not described in the docs
4. If information is insufficient, generate fewer test cases rather than making assumptions
5. Include both positive and negative test cases where documentation supports them
6. Use actual UI element names and flows from the documentation

IMPORTANT: You MUST respond with ONLY valid JSON. No explanation, no markdown, no code blocks. Just pure JSON.

OUTPUT FORMAT:
Return a valid JSON array of test case objects. Each test case must have:
[
  {
    "Test_ID": "TC-001",
    "Feature": "Feature name from docs",
    "Test_Scenario": "Clear scenario description",
    "Steps": ["Step 1", "Step 2"],
    "Expected_Result": "Expected outcome based on docs",
    "Grounded_In": ["document_name.md"]
  }
]

RESPONSE: Start with [ and end with ] only. No markdown formatting."""
        
        user_prompt = f"""Based on the following documentation excerpts, {user_query}

DOCUMENTATION CONTEXT:
{context}

AVAILABLE SOURCE DOCUMENTS:
{', '.join(source_docs)}

Generate test cases as a JSON array. Remember:
- Only use features explicitly mentioned in the documentation
- Reference source documents in "Grounded_In"
- Include test IDs starting from TC-001
- Focus on quality over quantity"""
        
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content([
                system_prompt,
                user_prompt
            ])
            content = response.text
            
            # Clean up markdown code blocks if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and 'test_cases' in parsed:
                    test_cases = parsed['test_cases']
                elif isinstance(parsed, dict) and 'testCases' in parsed:
                    test_cases = parsed['testCases']
                elif isinstance(parsed, list):
                    test_cases = parsed
                else:
                    test_cases = [parsed] if isinstance(parsed, dict) else []
                validated_cases = []
                for tc in test_cases:
                    if self._validate_test_case(tc):
                        validated_cases.append(tc)
                return validated_cases
            except json.JSONDecodeError as je:
                return [{
                    "Test_ID": "ERROR",
                    "Feature": "Parse Error",
                    "Test_Scenario": f"Failed to parse LLM response: {str(je)}",
                    "Steps": ["Check LLM output format", f"Raw content: {content[:200]}"],
                    "Expected_Result": "Valid JSON",
                    "Grounded_In": ["system_error"]
                }]
        except Exception as e:
            return [{
                "Test_ID": "ERROR",
                "Feature": "Generation Error",
                "Test_Scenario": f"Failed to generate test cases: {str(e)}",
                "Steps": ["Check API key", "Check connection"],
                "Expected_Result": "Successful generation",
                "Grounded_In": ["system_error"]
            }]
    
    def _validate_test_case(self, test_case: Dict) -> bool:
        """Validate that a test case has all required fields."""
        required_fields = ["Test_ID", "Feature", "Test_Scenario", "Expected_Result", "Grounded_In"]
        return all(field in test_case for field in required_fields)
    
    def get_sources_for_test_case(self, test_case: Dict[str, Any]) -> List[str]:
        """Extract source documents referenced by a test case."""
        return test_case.get("Grounded_In", [])
