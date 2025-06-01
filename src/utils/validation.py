"""
Validation utilities for the Academic Agent system.
Provides comprehensive input validation and sanitization.
"""
import re
import html
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import unicodedata

from src.models.state import AcademicAgentState
from src.utils.logging import logger


class ValidationLevel(Enum):
    """Validation strictness levels."""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        """
        Initialize validation error.
        
        Args:
            message (str): Error message
            field (str): Field that failed validation
            value (Any): Value that failed validation
        """
        super().__init__(message)
        self.field = field
        self.value = value


@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_value: Any = None


class InputValidator:
    """
    Validates and sanitizes user inputs for the Academic Agent system.
    """
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(UNION|OR|AND)\b.*\b(SELECT|INSERT|UPDATE|DELETE)\b)",
        r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT)\b)",
        r"(<script|</script>)",
        r"(\bxp_cmdshell\b)",
        r"(\bsp_executesql\b)"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*="
    ]
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """
        Initialize the input validator.
        
        Args:
            validation_level (ValidationLevel): Level of validation strictness
        """
        self.validation_level = validation_level
        
        # Compile regex patterns for performance
        self.sql_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_INJECTION_PATTERNS]
        self.xss_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.XSS_PATTERNS]
    
    def validate_user_query(self, query: str) -> ValidationResult:
        """
        Validate user query input.
        
        Args:
            query (str): User query to validate
            
        Returns:
            ValidationResult: Validation result
        """
        errors = []
        warnings = []
        
        # Basic checks
        if not query or not isinstance(query, str):
            errors.append("Query must be a non-empty string")
            return ValidationResult(False, errors, warnings)
        
        # Length checks
        if len(query.strip()) == 0:
            errors.append("Query cannot be empty or only whitespace")
        elif len(query) > 5000:
            errors.append("Query is too long (maximum 5000 characters)")
        elif len(query) > 1000:
            warnings.append("Query is quite long, consider breaking it down")
        
        # Security checks
        if self._contains_sql_injection(query):
            errors.append("Query contains potentially malicious SQL patterns")
        
        if self._contains_xss(query):
            errors.append("Query contains potentially malicious script patterns")
        
        # Content validation
        if self.validation_level in [ValidationLevel.STANDARD, ValidationLevel.STRICT]:
            # Check for excessive special characters
            special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s\-_.,?!]', query)) / len(query)
            if special_char_ratio > 0.3:
                warnings.append("Query contains many special characters")
            
            # Check for repeated characters (potential spam)
            if re.search(r'(.)\1{10,}', query):
                warnings.append("Query contains excessive repeated characters")
        
        if self.validation_level == ValidationLevel.STRICT:
            # Additional strict checks
            if re.search(r'[^\x00-\x7F]', query):
                warnings.append("Query contains non-ASCII characters")
        
        # Sanitize the query
        sanitized_query = self._sanitize_query(query)
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, sanitized_query)
    
    def validate_user_id(self, user_id: str) -> ValidationResult:
        """
        Validate user ID input.
        
        Args:
            user_id (str): User ID to validate
            
        Returns:
            ValidationResult: Validation result
        """
        errors = []
        warnings = []
        
        if not user_id or not isinstance(user_id, str):
            errors.append("User ID must be a non-empty string")
            return ValidationResult(False, errors, warnings)
        
        # Basic format validation
        user_id = user_id.strip()
        if not user_id:
            errors.append("User ID cannot be empty")
        elif len(user_id) < 3:
            errors.append("User ID must be at least 3 characters long")
        elif len(user_id) > 50:
            errors.append("User ID is too long (maximum 50 characters)")
        
        # Pattern validation (alphanumeric, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            errors.append("User ID can only contain letters, numbers, underscores, and hyphens")
        
        # Security checks
        if self._contains_sql_injection(user_id) or self._contains_xss(user_id):
            errors.append("User ID contains potentially malicious patterns")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, user_id)
    
    def validate_user_context(self, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate user context input.
        
        Args:
            context (Dict[str, Any]): User context to validate
            
        Returns:
            ValidationResult: Validation result
        """
        errors = []
        warnings = []
        sanitized_context = {}
        
        if not isinstance(context, dict):
            errors.append("User context must be a dictionary")
            return ValidationResult(False, errors, warnings)
        
        # Validate each field in context
        for key, value in context.items():
            # Validate key
            if not isinstance(key, str) or not key.strip():
                errors.append(f"Context key must be a non-empty string: {key}")
                continue
            
            # Sanitize key
            clean_key = self._sanitize_string(key)
            
            # Validate value based on type
            if isinstance(value, str):
                # String validation
                if len(value) > 1000:
                    errors.append(f"Context value too long for key '{key}' (maximum 1000 characters)")
                    continue
                
                if self._contains_sql_injection(value) or self._contains_xss(value):
                    errors.append(f"Context value contains malicious patterns for key '{key}'")
                    continue
                
                sanitized_context[clean_key] = self._sanitize_string(value)
                
            elif isinstance(value, (int, float)):
                # Numeric validation
                if abs(value) > 1e10:
                    warnings.append(f"Very large numeric value for key '{key}'")
                
                sanitized_context[clean_key] = value
                
            elif isinstance(value, bool):
                sanitized_context[clean_key] = value
                
            elif isinstance(value, (list, dict)):
                # Complex types - basic validation
                if len(str(value)) > 5000:
                    errors.append(f"Complex context value too large for key '{key}'")
                    continue
                
                sanitized_context[clean_key] = value
                
            else:
                warnings.append(f"Unsupported context value type for key '{key}': {type(value)}")
                sanitized_context[clean_key] = str(value)
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, sanitized_context)
    
    def validate_state(self, state: AcademicAgentState) -> ValidationResult:
        """
        Validate the complete agent state.
        
        Args:
            state (AcademicAgentState): State to validate
            
        Returns:
            ValidationResult: Validation result
        """
        errors = []
        warnings = []
        
        if not isinstance(state, dict):
            errors.append("State must be a dictionary")
            return ValidationResult(False, errors, warnings)
        
        # Validate required fields
        required_fields = ["user_query", "user_id", "user_context"]
        for field in required_fields:
            if field not in state:
                errors.append(f"Missing required field: {field}")
        
        # Validate individual fields if present
        if "user_query" in state:
            query_result = self.validate_user_query(state["user_query"])
            errors.extend(query_result.errors)
            warnings.extend(query_result.warnings)
        
        if "user_id" in state:
            user_id_result = self.validate_user_id(state["user_id"])
            errors.extend(user_id_result.errors)
            warnings.extend(query_result.warnings)
        
        if "user_context" in state:
            context_result = self.validate_user_context(state["user_context"])
            errors.extend(context_result.errors)
            warnings.extend(context_result.warnings)
        
        # Validate optional fields
        if "generated_sql" in state and state["generated_sql"]:
            sql_result = self._validate_sql_query(state["generated_sql"])
            errors.extend(sql_result.errors)
            warnings.extend(sql_result.warnings)
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)
    
    def _contains_sql_injection(self, text: str) -> bool:
        """Check if text contains SQL injection patterns."""
        return any(pattern.search(text) for pattern in self.sql_patterns)
    
    def _contains_xss(self, text: str) -> bool:
        """Check if text contains XSS patterns."""
        return any(pattern.search(text) for pattern in self.xss_patterns)
    
    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize user query.
        
        Args:
            query (str): Query to sanitize
            
        Returns:
            str: Sanitized query
        """
        # Remove null bytes
        query = query.replace('\x00', '')
        
        # Normalize unicode
        query = unicodedata.normalize('NFKC', query)
        
        # HTML escape
        query = html.escape(query)
        
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def _sanitize_string(self, text: str) -> str:
        """
        Sanitize a general string.
        
        Args:
            text (str): Text to sanitize
            
        Returns:
            str: Sanitized text
        """
        if not isinstance(text, str):
            return str(text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Remove control characters except newline and tab
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Trim whitespace
        text = text.strip()
        
        return text
    
    def _validate_sql_query(self, sql: str) -> ValidationResult:
        """
        Validate SQL query for safety.
        
        Args:
            sql (str): SQL query to validate
            
        Returns:
            ValidationResult: Validation result
        """
        errors = []
        warnings = []
        
        if not sql or not isinstance(sql, str):
            errors.append("SQL query must be a non-empty string")
            return ValidationResult(False, errors, warnings)
        
        # Check for dangerous SQL operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER',
            'EXEC', 'EXECUTE', 'xp_cmdshell', 'sp_executesql'
        ]
        
        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                errors.append(f"SQL contains dangerous keyword: {keyword}")
        
        # Check for multiple statements
        if ';' in sql and sql.count(';') > 1:
            errors.append("SQL contains multiple statements")
        
        # Check for comments
        if '--' in sql or '/*' in sql:
            warnings.append("SQL contains comments")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, sql)


# Global validator instance
input_validator = InputValidator()
