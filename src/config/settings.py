"""
Configuration settings for the Academic Agent system.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and Credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "academic-agent")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_TEMPERATURE_CREATIVE = float(os.getenv("LLM_TEMPERATURE_CREATIVE", "0.7"))

# Cache Configuration
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # Default: 1 hour
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TRACING_ENABLED = os.getenv("TRACING_ENABLED", "True").lower() == "true"

# Database Schema Cache
SCHEMA_CACHE_TTL = int(os.getenv("SCHEMA_CACHE_TTL", "86400"))  # Default: 24 hours

# Performance Settings
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# RAG Configuration
PDF_STORAGE_DIR = os.getenv("PDF_STORAGE_DIR", "./data/pdfs")
EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", "./data/embeddings")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Tavily Configuration
TAVILY_MAX_RESULTS = int(os.getenv("TAVILY_MAX_RESULTS", "5"))
TAVILY_SEARCH_DEPTH = os.getenv("TAVILY_SEARCH_DEPTH", "basic")
