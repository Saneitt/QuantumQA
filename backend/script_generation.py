import os
import json
from typing import Dict, Any, List
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import chromadb


class SeleniumScriptGenerator:
    """Generates production-ready Selenium Python scripts from test cases."""
    
    def __init__(self, persist_directory: str = "./db"):
        self.persist_directory = persist_directory
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        try:
            self.collection = self.client.get_collection("qa_knowledge_base")
        except:
            self.collection = None
        
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=gemini_api_key)
    
    def retrieve_html_selectors(self) -> str:
        """Retrieve HTML selector information from the knowledge base."""
        if not self.collection:
            return ""
        
        query = "HTML selectors buttons inputs forms cart payment shipping discount"
        query_embedding = self.embedding_model.encode([query], show_progress_bar=False)[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5,
            where={"doc_type": "html_dom"}
        )
        
        selector_context = ""
        if results['documents'] and len(results['documents']) > 0:
            for doc in results['documents'][0]:
                selector_context += doc + "\n\n"
        
        return selector_context
    
    def retrieve_relevant_docs(self, test_case: Dict[str, Any]) -> str:
        """Retrieve relevant documentation based on test case content."""
        if not self.collection:
            return ""
        query = f"{test_case.get('Feature', '')} {test_case.get('Test_Scenario', '')}"
        query_embedding = self.embedding_model.encode([query], show_progress_bar=False)[0]
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=3
        )
        doc_context = ""
        if results['documents'] and len(results['documents']) > 0:
            for idx, doc in enumerate(results['documents'][0]):
                source = results['metadatas'][0][idx].get('source_document', 'unknown')
                doc_context += f"[{source}]\n{doc}\n\n"
        return doc_context

    def generate_script(self, test_case: Dict[str, Any], html_content: str = None) -> str:
        """
        Generate a production-ready Selenium Python script.
        Args:
            test_case: The test case dictionary
            html_content: Optional HTML content for additional selector extraction
        Returns:
            Python script as a string
        """
        selector_context = self.retrieve_html_selectors()
        doc_context = self.retrieve_relevant_docs(test_case)
        test_case_str = json.dumps(test_case, indent=2)
        system_prompt = """You are an expert Selenium automation engineer specializing in writing clean, production-ready test scripts.

CRITICAL REQUIREMENTS:
1. Use ONLY selectors found in the provided HTML selector context
2. Implement WebDriverWait for all element interactions (explicit waits)
3. Include proper error handling and logging
4. Use modular functions with clear docstrings
5. Add comments linking steps back to documentation
6. Use Chrome WebDriver with proper initialization
7. Make scripts runnable and self-contained
8. Follow Python best practices (PEP 8)

SCRIPT STRUCTURE:
- Import statements
- Helper functions
- Main test function (run_test)
- WebDriver setup with proper configuration
- Clean teardown

OUTPUT:
Generate a complete, runnable Python script. Do not add markdown code fences or explanations - just pure Python code."""
        user_prompt = f"""Generate a Selenium Python script for this test case:

TEST CASE:
{test_case_str}

HTML SELECTORS (use these exact selectors):
{selector_context}

DOCUMENTATION CONTEXT:
{doc_context}

Requirements:
- Use WebDriverWait with explicit waits (10-20 seconds timeout)
- Match selectors from the HTML context exactly
- Include comments referencing the source documents from Grounded_In
- Implement the test steps precisely as described
- Add assertions for the expected result
- Handle potential errors gracefully
- Make the script production-ready and executable

Generate the complete Python script now."""
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content([
                system_prompt,
                user_prompt
            ])
            script = response.text
            if script.startswith("```python"):
                script = script.replace("```python", "").replace("```", "").strip()
            elif script.startswith("```"):
                script = script.replace("```", "").strip()
            header = f"""#!/usr/bin/env python3
# Auto-generated Selenium test script
# Test ID: {test_case.get('Test_ID', 'Unknown')}
# Feature: {test_case.get('Feature', 'Unknown')}
# Grounded in: {', '.join(test_case.get('Grounded_In', []))}

"""
            return header + script
        except Exception as e:
            error_script = f"""#!/usr/bin/env python3
# ERROR: Failed to generate script
# Error: {str(e)}

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_test():
    '''
    Test ID: {test_case.get('Test_ID', 'Unknown')}
    Feature: {test_case.get('Feature', 'Unknown')}
    
    ERROR: Script generation failed. Please check:
    1. Gemini API key is set correctly
    2. Network connection is stable
    3. API quota is available
    
    Error details: {str(e)}
    '''
    print("ERROR: Script generation failed")
    print("Error details: {str(e)}")

if __name__ == "__main__":
    run_test()
"""
            return error_script
