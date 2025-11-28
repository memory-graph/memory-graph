"""
Proactive Features for Claude Code Memory Server.

This module provides AI-powered proactive features including:
- Session start intelligence and briefing
- Predictive suggestions based on current context
- Outcome learning and effectiveness tracking
- Advanced analytics queries

Phase 7 Implementation
"""

from .session_briefing import (
    SessionBriefing,
    generate_session_briefing,
    get_session_briefing_resource,
)
from .predictive import (
    Suggestion,
    Warning,
    predict_needs,
    warn_potential_issues,
    suggest_related_context,
)
from .outcome_learning import (
    record_outcome,
    update_pattern_effectiveness,
    calculate_effectiveness_score,
)

__all__ = [
    # Session briefing
    "SessionBriefing",
    "generate_session_briefing",
    "get_session_briefing_resource",
    # Predictive suggestions
    "Suggestion",
    "Warning",
    "predict_needs",
    "warn_potential_issues",
    "suggest_related_context",
    # Outcome learning
    "record_outcome",
    "update_pattern_effectiveness",
    "calculate_effectiveness_score",
]
