"""
Enhanced Tutor Agent with Advanced Learning Analytics and Personalization.

This module implements cutting-edge educational AI methodologies:

1. Adaptive Learning Framework:
   - Dynamic difficulty adjustment based on student performance
   - Learning style detection and adaptation
   - Personalized learning paths

2. Cognitive Load Theory Implementation:
   - Intrinsic, extraneous, and germane load management
   - Progressive complexity introduction
   - Scaffolding and fading support

3. Bloom's Taxonomy Integration:
   - Automatic classification of learning objectives
   - Progressive skill building from remembering to creating
   - Assessment alignment with learning goals

4. Spaced Repetition and Retrieval Practice:
   - Intelligent review scheduling
   - Active recall techniques
   - Long-term retention optimization

5. Metacognitive Support:
   - Learning strategy instruction
   - Self-regulation skill development
   - Reflection and goal-setting guidance
"""
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base_agent import LLMAgent
from src.config.agent_config import config_manager
from src.config.settings import LLM_MODEL, LLM_TEMPERATURE
from src.models.state import AcademicAgentState
from src.mcp.integration import with_mcp_context, ContextType, mcp_cache_result
from src.utils.logging import logger
from src.utils.validation import input_validator
from src.utils.metrics import metrics_collector
from src.utils.error_handling import LLMError


class EnhancedTutorAgent(LLMAgent):
    """
    Enhanced Tutor Agent with advanced learning analytics and personalization.
    
    Features:
    - Adaptive learning with dynamic difficulty adjustment
    - Learning style detection and accommodation
    - Cognitive load management
    - Bloom's taxonomy-based progression
    - Spaced repetition scheduling
    - Metacognitive skill development
    """
    
    def __init__(self):
        """Initialize the Enhanced Tutor Agent."""
        super().__init__(
            name="enhanced_tutor",
            description="Provides advanced tutoring with adaptive learning and personalization",
            temperature=0.5
        )
        
        # Get agent configuration
        self.config = config_manager.get_agent_config("tutor")
        if self.config:
            self.timeout_seconds = self.config.timeout_seconds
            self.custom_settings = self.config.custom_settings
        else:
            self.timeout_seconds = 45
            self.custom_settings = {}
        
        # Learning analytics and personalization
        self.student_profiles = {}  # Comprehensive student learning profiles
        self.learning_paths = {}    # Personalized learning sequences
        self.performance_analytics = {}  # Detailed performance tracking
        
        # Cognitive load management
        self.cognitive_load_thresholds = {
            "beginner": {"intrinsic": 3, "extraneous": 2, "total": 5},
            "intermediate": {"intrinsic": 5, "extraneous": 3, "total": 8},
            "advanced": {"intrinsic": 7, "extraneous": 4, "total": 11}
        }
        
        # Bloom's taxonomy levels
        self.blooms_levels = [
            "remembering", "understanding", "applying", 
            "analyzing", "evaluating", "creating"
        ]
        
        # Learning styles framework
        self.learning_styles = {
            "visual": ["diagrams", "charts", "mind_maps", "infographics"],
            "auditory": ["explanations", "discussions", "verbal_examples"],
            "kinesthetic": ["hands_on", "simulations", "practice_problems"],
            "reading_writing": ["text_based", "note_taking", "written_exercises"]
        }

    @with_mcp_context([ContextType.USER_PROFILE, ContextType.CONVERSATION])
    @mcp_cache_result(ttl_seconds=1800)  # Cache for 30 minutes
    def _execute(self, state: AcademicAgentState) -> AcademicAgentState:
        """
        Execute enhanced tutoring with adaptive learning.
        
        Args:
            state (AcademicAgentState): Current state
            
        Returns:
            AcademicAgentState: Updated state with enhanced tutoring
        """
        # Validate input
        validation_result = input_validator.validate_user_query(state["user_query"])
        if not validation_result.is_valid:
            raise LLMError(f"Invalid query: {', '.join(validation_result.errors)}")
        
        # Record metrics
        start_time = time.time()
        
        try:
            # Step 1: Analyze student profile and learning context
            state = self._analyze_student_profile(state)
            
            # Step 2: Classify learning objective using Bloom's taxonomy
            state = self._classify_learning_objective(state)
            
            # Step 3: Assess cognitive load and adjust complexity
            state = self._assess_cognitive_load(state)
            
            # Step 4: Detect and adapt to learning style
            state = self._adapt_to_learning_style(state)
            
            # Step 5: Generate adaptive explanation
            state = self._generate_adaptive_explanation(state)
            
            # Step 6: Create practice opportunities
            state = self._create_practice_opportunities(state)
            
            # Step 7: Schedule spaced repetition
            state = self._schedule_spaced_repetition(state)
            
            # Step 8: Provide metacognitive guidance
            state = self._provide_metacognitive_guidance(state)
            
            # Step 9: Generate comprehensive tutoring response
            state = self._generate_tutoring_response(state)
            
            # Record successful execution
            execution_time = time.time() - start_time
            metrics_collector.record_agent_execution(
                self.name, execution_time, True, False
            )
            
            logger.info(f"Enhanced tutoring completed for subject: {state.get('subject', 'unknown')}")
            
            return state
            
        except Exception as e:
            execution_time = time.time() - start_time
            metrics_collector.record_agent_execution(
                self.name, execution_time, False, False, str(type(e).__name__)
            )
            raise LLMError(f"Enhanced tutoring failed: {str(e)}")

    def _analyze_student_profile(self, state: AcademicAgentState) -> AcademicAgentState:
        """Analyze comprehensive student learning profile."""
        user_id = state.get("user_id", "unknown")
        mcp_context = state.get("mcp_context", {})
        
        # Initialize or update student profile
        if user_id not in self.student_profiles:
            self.student_profiles[user_id] = {
                "learning_level": "beginner",
                "learning_style": "unknown",
                "strengths": [],
                "weaknesses": [],
                "preferred_complexity": "low",
                "performance_history": [],
                "last_interaction": None,
                "total_interactions": 0,
                "mastery_levels": {}
            }
        
        profile = self.student_profiles[user_id]
        profile["last_interaction"] = datetime.now()
        profile["total_interactions"] += 1
        
        # Analyze conversation history for learning patterns
        conversation_history = mcp_context.get("conversation_history", [])
        if conversation_history:
            state["learning_context"] = self._extract_learning_patterns(conversation_history, profile)
        
        # Add profile to state
        state["student_profile"] = profile
        
        logger.info(f"Analyzed student profile for user {user_id}: level={profile['learning_level']}")
        
        return state

    def _extract_learning_patterns(self, conversation_history: List, profile: Dict) -> Dict:
        """Extract learning patterns from conversation history."""
        patterns = {
            "question_complexity": "medium",
            "response_quality": "good",
            "engagement_level": "high",
            "learning_progression": "steady"
        }
        
        # Analyze recent interactions for complexity preference
        recent_interactions = conversation_history[-5:] if len(conversation_history) >= 5 else conversation_history
        
        # Simple heuristics for pattern detection
        complex_keywords = ["advanced", "detailed", "complex", "in-depth"]
        simple_keywords = ["basic", "simple", "easy", "beginner"]
        
        complex_count = sum(1 for interaction in recent_interactions 
                          if any(keyword in str(interaction).lower() for keyword in complex_keywords))
        simple_count = sum(1 for interaction in recent_interactions 
                         if any(keyword in str(interaction).lower() for keyword in simple_keywords))
        
        if complex_count > simple_count:
            patterns["question_complexity"] = "high"
            profile["preferred_complexity"] = "high"
        elif simple_count > complex_count:
            patterns["question_complexity"] = "low"
            profile["preferred_complexity"] = "low"
        
        return patterns

    def _classify_learning_objective(self, state: AcademicAgentState) -> AcademicAgentState:
        """Classify learning objective using Bloom's taxonomy."""
        query = state["user_query"].lower()
        
        # Keyword mapping for Bloom's levels
        bloom_keywords = {
            "remembering": ["what is", "define", "list", "name", "identify", "recall"],
            "understanding": ["explain", "describe", "summarize", "interpret", "compare"],
            "applying": ["solve", "calculate", "demonstrate", "use", "apply", "show"],
            "analyzing": ["analyze", "examine", "compare", "contrast", "break down"],
            "evaluating": ["evaluate", "assess", "judge", "critique", "justify"],
            "creating": ["create", "design", "develop", "compose", "construct"]
        }
        
        # Determine Bloom's level
        bloom_level = "understanding"  # Default
        for level, keywords in bloom_keywords.items():
            if any(keyword in query for keyword in keywords):
                bloom_level = level
                break
        
        state["bloom_level"] = bloom_level
        state["learning_objective"] = {
            "level": bloom_level,
            "complexity": self._get_complexity_for_bloom_level(bloom_level),
            "cognitive_demand": self._get_cognitive_demand(bloom_level)
        }
        
        logger.info(f"Classified learning objective: {bloom_level}")

        return state

    def _get_complexity_for_bloom_level(self, bloom_level: str) -> str:
        """Get complexity level for Bloom's taxonomy level."""
        complexity_mapping = {
            "remembering": "low",
            "understanding": "low",
            "applying": "medium",
            "analyzing": "medium",
            "evaluating": "high",
            "creating": "high"
        }
        return complexity_mapping.get(bloom_level, "medium")

    def _get_cognitive_demand(self, bloom_level: str) -> int:
        """Get cognitive demand score for Bloom's level."""
        demand_mapping = {
            "remembering": 2,
            "understanding": 3,
            "applying": 4,
            "analyzing": 5,
            "evaluating": 6,
            "creating": 7
        }
        return demand_mapping.get(bloom_level, 3)

    def _assess_cognitive_load(self, state: AcademicAgentState) -> AcademicAgentState:
        """Assess and manage cognitive load."""
        profile = state.get("student_profile", {})
        learning_level = profile.get("learning_level", "beginner")
        bloom_level = state.get("bloom_level", "understanding")

        # Calculate cognitive load components
        intrinsic_load = self._calculate_intrinsic_load(state)
        extraneous_load = self._calculate_extraneous_load(state)
        germane_load = self._calculate_germane_load(state)

        total_load = intrinsic_load + extraneous_load + germane_load

        # Get thresholds for student level
        thresholds = self.cognitive_load_thresholds[learning_level]

        # Adjust complexity if load is too high
        load_assessment = {
            "intrinsic_load": intrinsic_load,
            "extraneous_load": extraneous_load,
            "germane_load": germane_load,
            "total_load": total_load,
            "threshold_exceeded": total_load > thresholds["total"],
            "adjustment_needed": total_load > thresholds["total"]
        }

        if load_assessment["adjustment_needed"]:
            load_assessment["adjustments"] = self._suggest_load_adjustments(load_assessment, thresholds)

        state["cognitive_load"] = load_assessment

        logger.info(f"Cognitive load assessment: total={total_load}, threshold={thresholds['total']}")

        return state

    def _calculate_intrinsic_load(self, state: AcademicAgentState) -> int:
        """Calculate intrinsic cognitive load."""
        bloom_level = state.get("bloom_level", "understanding")
        query_complexity = len(state["user_query"].split())

        # Base load from Bloom's level
        base_load = self._get_cognitive_demand(bloom_level)

        # Adjust for query complexity
        if query_complexity > 20:
            base_load += 1
        elif query_complexity < 5:
            base_load -= 1

        return max(1, min(base_load, 7))

    def _calculate_extraneous_load(self, state: AcademicAgentState) -> int:
        """Calculate extraneous cognitive load."""
        # Factors that add unnecessary complexity
        extraneous_factors = 0

        query = state["user_query"].lower()

        # Multiple concepts in one query
        concept_indicators = ["and", "also", "plus", "additionally", "furthermore"]
        if sum(1 for indicator in concept_indicators if indicator in query) > 2:
            extraneous_factors += 1

        # Unclear or ambiguous language
        ambiguous_words = ["thing", "stuff", "something", "somehow", "maybe"]
        if any(word in query for word in ambiguous_words):
            extraneous_factors += 1

        return min(extraneous_factors, 3)

    def _calculate_germane_load(self, state: AcademicAgentState) -> int:
        """Calculate germane cognitive load (productive learning effort)."""
        profile = state.get("student_profile", {})

        # Higher germane load for students ready for challenge
        if profile.get("learning_level") == "advanced":
            return 2
        elif profile.get("learning_level") == "intermediate":
            return 1
        else:
            return 0

    def _suggest_load_adjustments(self, load_assessment: Dict, thresholds: Dict) -> List[str]:
        """Suggest adjustments to reduce cognitive load."""
        adjustments = []

        if load_assessment["intrinsic_load"] > thresholds["intrinsic"]:
            adjustments.append("Break down complex concepts into smaller parts")
            adjustments.append("Provide more scaffolding and examples")

        if load_assessment["extraneous_load"] > thresholds["extraneous"]:
            adjustments.append("Simplify language and remove ambiguity")
            adjustments.append("Focus on one concept at a time")

        if load_assessment["total_load"] > thresholds["total"]:
            adjustments.append("Reduce overall complexity")
            adjustments.append("Provide more guided practice")

        return adjustments


# Create agent instance
enhanced_tutor_agent_instance = EnhancedTutorAgent()


def enhanced_tutor_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Enhanced tutor agent function for backward compatibility.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with enhanced tutoring
    """
    return enhanced_tutor_agent_instance.execute(state)
