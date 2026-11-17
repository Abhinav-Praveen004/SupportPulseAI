"""M2 Routing Engine: Recommends team from predicted category and live queue workload."""

from typing import Dict, Optional, Tuple

PRIMARY_TEAM_MAPPING = {
    "Password/Access": "IT Helpdesk",
    "Network/VPN": "Network Ops",
    "Email": "IT Helpdesk",
    "Hardware": "Endpoint Services",
    "Software Install": "Endpoint Services",
    "Application Error": "Application Support",
    "Security Incident": "Security Ops",
    "Printer": "IT Helpdesk",
    "Cloud/Infrastructure": "Cloud Infrastructure",
    "Service Request": "IT Helpdesk",
}

SECONDARY_TEAM_MAPPING = {
    "Service Request": "Endpoint Services",
    "Password/Access": "Endpoint Services",
    "Software Install": "IT Helpdesk",
}


class RoutingEngine:
    """Workload-aware routing recommendation engine."""

    def __init__(self, overload_threshold: int = 50):
        self.overload_threshold = overload_threshold

    def recommend_team(
        self,
        predicted_category: str,
        category_confidence: float = 0.85,
        team_workload: Optional[Dict[str, int]] = None,
    ) -> Tuple[str, str]:
        """Recommend optimal team assignment with explicit reasoning."""
        primary_team = PRIMARY_TEAM_MAPPING.get(predicted_category, "IT Helpdesk")
        workload = team_workload or {}
        primary_load = workload.get(primary_team, 0)

        # Check for team overload and eligible overflow
        if primary_load > self.overload_threshold and predicted_category in SECONDARY_TEAM_MAPPING:
            secondary_team = SECONDARY_TEAM_MAPPING[predicted_category]
            secondary_load = workload.get(secondary_team, 0)
            if secondary_load < primary_load * 0.7:
                reason = (
                    f"Recommended '{secondary_team}' (load: {secondary_load}) as overflow assignment. "
                    f"Primary team '{primary_team}' is currently congested with {primary_load} open tickets. "
                    f"Category: '{predicted_category}' ({category_confidence * 100:.1f}% confidence)."
                )
                return secondary_team, reason

        # Standard primary team recommendation
        load_desc = f"{primary_load} open tickets" if team_workload else "normal workload"
        reason = (
            f"Assigned to specialized team '{primary_team}' based on predicted category '{predicted_category}' "
            f"({category_confidence * 100:.1f}% confidence). Current team queue: {load_desc}."
        )
        return primary_team, reason
