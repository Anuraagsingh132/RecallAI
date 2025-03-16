import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ResponseGenerator:
    """Class for generating responses using an LLM (Google Gemini)."""
    
    def __init__(self, model_name: str = "gemini-pro"):
        """
        Initialize the ResponseGenerator.
        
        Args:
            model_name: Name of the Gemini model to use
        """
        # Configure the Google Generative AI API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
        genai.configure(api_key=api_key)
        
        # Set up the model
        self.model = genai.GenerativeModel(model_name)
        
    def generate(self, query: str, context: str) -> str:
        """
        Generate a response to a query using the provided context.
        
        Args:
            query: User query
            context: Context from retrieved documents
            
        Returns:
            Generated response
        """
        # Prepare the prompt
        prompt = self._create_prompt(query, context)
        
        # Generate the response
        response = self.model.generate_content(prompt)
        
        # Extract and return the response text
        return response.text
        
    def _create_prompt(self, query: str, context: str) -> str:
        """
        Create a prompt for the LLM.
        
        Args:
            query: User query
            context: Context from retrieved documents
            
        Returns:
            Formatted prompt
        """
        return f"""You are a helpful assistant that provides accurate information based on the given context. 
If the context doesn't contain enough information to answer the question, admit that you don't know rather than making up an answer.
Always cite your sources when possible.

CONTEXT:
{context}

USER QUESTION:
{query}

YOUR ANSWER:"""

class OpenSourceResponseGenerator:
    """Alternative class for generating responses using local open-source LLMs."""
    
    def __init__(self, model_path: str):
        """
        Initialize the OpenSourceResponseGenerator.
        
        Args:
            model_path: Path to the local model
        """
        # This is a placeholder - implementation would depend on the model and library
        # For example, you might use LangChain with a Llama model
        self.model_path = model_path
        
    def generate(self, query: str, context: str) -> str:
        """
        Generate a response using a local model.
        
        Args:
            query: User query
            context: Context from retrieved documents
            
        Returns:
            Generated response
        """
        # Placeholder - actual implementation would use the local model
        # Example using LangChain + Llama:
        # from langchain.llms import LlamaCpp
        # llm = LlamaCpp(model_path=self.model_path)
        # prompt = self._create_prompt(query, context)
        # return llm.predict(prompt)
        
        return "This is a placeholder for local model response. Implement using your preferred local LLM."
        
    def _create_prompt(self, query: str, context: str) -> str:
        """
        Create a prompt for the local LLM.
        
        Args:
            query: User query
            context: Context from retrieved documents
            
        Returns:
            Formatted prompt
        """
        return f"""<s>[INST] 
You are a helpful assistant that provides accurate information based on the given context. 
If the context doesn't contain enough information to answer the question, admit that you don't know.

Context:
{context}

Question:
{query}
[/INST]

""" 