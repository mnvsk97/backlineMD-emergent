"""
Onboarding Agent (Alias for Intake Agent)
This file exists for backwards compatibility
"""

from intake import intake_agent, intake_workflow

# Export intake agent as onboarding agent
onboarding_agent = intake_agent
onboarding_workflow = intake_workflow
