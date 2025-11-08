"""
Cognitive PID Framework

A three-agent AI orchestration system for automated incremental application development
using PID feedback control.
"""

__version__ = '0.1.0'
__author__ = 'Cognitive PID Framework Team'

from src.main import CognitivePIDOrchestrator
from src.controller import PIDController
from src.agent_keeper import call_keeper
from src.agent_developer import call_developer
from src.agent_qa import call_qa

__all__ = [
    'CognitivePIDOrchestrator',
    'PIDController',
    'call_keeper',
    'call_developer',
    'call_qa',
]
