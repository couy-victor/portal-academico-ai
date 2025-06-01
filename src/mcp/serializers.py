"""
MCP Serializers for context data.
Provides serialization and deserialization of context data in different formats.
"""
import json
import pickle
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

from src.utils.logging import logger


class BaseContextSerializer(ABC):
    """
    Base class for context serializers.
    """
    
    @abstractmethod
    def serialize(self, data: Any) -> bytes:
        """
        Serialize data to bytes.
        
        Args:
            data (Any): Data to serialize
            
        Returns:
            bytes: Serialized data
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """
        Deserialize bytes to data.
        
        Args:
            data (bytes): Serialized data
            
        Returns:
            Any: Deserialized data
        """
        pass


class JSONContextSerializer(BaseContextSerializer):
    """
    JSON-based context serializer.
    """
    
    def __init__(self, ensure_ascii: bool = False, indent: Optional[int] = None):
        """
        Initialize JSON serializer.
        
        Args:
            ensure_ascii (bool): Whether to ensure ASCII encoding
            indent (Optional[int]): JSON indentation
        """
        self.ensure_ascii = ensure_ascii
        self.indent = indent
    
    def serialize(self, data: Any) -> bytes:
        """
        Serialize data to JSON bytes.
        
        Args:
            data (Any): Data to serialize
            
        Returns:
            bytes: JSON serialized data
        """
        try:
            json_str = json.dumps(
                data, 
                ensure_ascii=self.ensure_ascii,
                indent=self.indent,
                default=self._json_default
            )
            return json_str.encode('utf-8')
        except Exception as e:
            logger.error(f"JSON serialization error: {e}")
            raise
    
    def deserialize(self, data: bytes) -> Any:
        """
        Deserialize JSON bytes to data.
        
        Args:
            data (bytes): JSON serialized data
            
        Returns:
            Any: Deserialized data
        """
        try:
            json_str = data.decode('utf-8')
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"JSON deserialization error: {e}")
            raise
    
    def _json_default(self, obj: Any) -> Any:
        """
        Default JSON serializer for non-serializable objects.
        
        Args:
            obj (Any): Object to serialize
            
        Returns:
            Any: Serializable representation
        """
        # Handle datetime objects
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        
        # Handle other objects by converting to string
        return str(obj)


class ProtobufContextSerializer(BaseContextSerializer):
    """
    Protocol Buffers context serializer.
    Note: This is a placeholder implementation.
    In a real system, you would use actual protobuf definitions.
    """
    
    def __init__(self):
        """Initialize Protobuf serializer."""
        logger.warning("ProtobufContextSerializer is a placeholder implementation")
    
    def serialize(self, data: Any) -> bytes:
        """
        Serialize data using pickle as protobuf placeholder.
        
        Args:
            data (Any): Data to serialize
            
        Returns:
            bytes: Serialized data
        """
        try:
            return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Protobuf serialization error: {e}")
            raise
    
    def deserialize(self, data: bytes) -> Any:
        """
        Deserialize data using pickle as protobuf placeholder.
        
        Args:
            data (bytes): Serialized data
            
        Returns:
            Any: Deserialized data
        """
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Protobuf deserialization error: {e}")
            raise


class CompressedJSONSerializer(JSONContextSerializer):
    """
    Compressed JSON serializer for large context data.
    """
    
    def __init__(self, compression_level: int = 6, **kwargs):
        """
        Initialize compressed JSON serializer.
        
        Args:
            compression_level (int): Compression level (1-9)
            **kwargs: Additional arguments for JSONContextSerializer
        """
        super().__init__(**kwargs)
        self.compression_level = compression_level
    
    def serialize(self, data: Any) -> bytes:
        """
        Serialize and compress data.
        
        Args:
            data (Any): Data to serialize
            
        Returns:
            bytes: Compressed serialized data
        """
        try:
            import gzip
            json_data = super().serialize(data)
            return gzip.compress(json_data, compresslevel=self.compression_level)
        except ImportError:
            logger.warning("gzip not available, falling back to uncompressed JSON")
            return super().serialize(data)
        except Exception as e:
            logger.error(f"Compressed JSON serialization error: {e}")
            raise
    
    def deserialize(self, data: bytes) -> Any:
        """
        Decompress and deserialize data.
        
        Args:
            data (bytes): Compressed serialized data
            
        Returns:
            Any: Deserialized data
        """
        try:
            import gzip
            json_data = gzip.decompress(data)
            return super().deserialize(json_data)
        except ImportError:
            logger.warning("gzip not available, trying uncompressed JSON")
            return super().deserialize(data)
        except Exception as e:
            logger.error(f"Compressed JSON deserialization error: {e}")
            raise


class SerializerFactory:
    """
    Factory for creating context serializers.
    """
    
    _serializers = {
        'json': JSONContextSerializer,
        'protobuf': ProtobufContextSerializer,
        'compressed_json': CompressedJSONSerializer
    }
    
    @classmethod
    def create_serializer(cls, serializer_type: str, **kwargs) -> BaseContextSerializer:
        """
        Create a serializer instance.
        
        Args:
            serializer_type (str): Type of serializer
            **kwargs: Additional arguments for serializer
            
        Returns:
            BaseContextSerializer: Serializer instance
        """
        if serializer_type not in cls._serializers:
            raise ValueError(f"Unknown serializer type: {serializer_type}")
        
        serializer_class = cls._serializers[serializer_type]
        return serializer_class(**kwargs)
    
    @classmethod
    def register_serializer(cls, name: str, serializer_class: type) -> None:
        """
        Register a custom serializer.
        
        Args:
            name (str): Serializer name
            serializer_class (type): Serializer class
        """
        cls._serializers[name] = serializer_class
    
    @classmethod
    def get_available_serializers(cls) -> list:
        """
        Get list of available serializers.
        
        Returns:
            list: List of serializer names
        """
        return list(cls._serializers.keys())


# Default serializer instances
json_serializer = JSONContextSerializer(ensure_ascii=False, indent=None)
compressed_json_serializer = CompressedJSONSerializer(compression_level=6)
protobuf_serializer = ProtobufContextSerializer()
