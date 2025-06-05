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
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "portal-academico")
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
RAG_STORAGE_TYPE = os.getenv("RAG_STORAGE_TYPE", "supabase")  # "local" ou "supabase"

# BM25 Configuration
USE_BM25 = os.getenv("USE_BM25", "True").lower() == "true"
HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.5"))  # Peso para embeddings vs BM25
BM25_K1 = float(os.getenv("BM25_K1", "1.5"))  # Parâmetro k1 do BM25
BM25_B = float(os.getenv("BM25_B", "0.75"))  # Parâmetro b do BM25

# Tavily Configuration
TAVILY_MAX_RESULTS = int(os.getenv("TAVILY_MAX_RESULTS", "5"))
TAVILY_SEARCH_DEPTH = os.getenv("TAVILY_SEARCH_DEPTH", "basic")

# MCP Configuration
MCP_ENABLED = os.getenv("MCP_ENABLED", "True").lower() == "true"
MCP_CONTEXT_TTL = int(os.getenv("MCP_CONTEXT_TTL", "3600"))  # 1 hour
MCP_CLEANUP_INTERVAL = int(os.getenv("MCP_CLEANUP_INTERVAL", "300"))  # 5 minutes
MCP_MAX_CONTEXT_SIZE = int(os.getenv("MCP_MAX_CONTEXT_SIZE", "1000000"))  # 1MB

# Metrics Configuration
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "True").lower() == "true"
METRICS_EXPORT_INTERVAL = int(os.getenv("METRICS_EXPORT_INTERVAL", "60"))  # 1 minute
METRICS_RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", "7"))

# Error Handling Configuration
ERROR_RECOVERY_ENABLED = os.getenv("ERROR_RECOVERY_ENABLED", "True").lower() == "true"
MAX_RECOVERY_ATTEMPTS = int(os.getenv("MAX_RECOVERY_ATTEMPTS", "3"))
FALLBACK_RESPONSE_ENABLED = os.getenv("FALLBACK_RESPONSE_ENABLED", "True").lower() == "true"
