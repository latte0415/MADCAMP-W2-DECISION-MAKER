from app.workers.handlers.notification_handler import (
    handle_proposal_approved,
    handle_proposal_rejected,
    handle_membership_approved,
    handle_membership_rejected,
)

HANDLERS = {
    "proposal.approved.v1": handle_proposal_approved,
    "proposal.rejected.v1": handle_proposal_rejected,
    "membership.approved.v1": handle_membership_approved,
    "membership.rejected.v1": handle_membership_rejected,
}

def get_handler_for_event_type(event_type: str):
    handler = HANDLERS.get(event_type)
    if not handler:
        raise ValueError(f"Unknown event type: {event_type}")
    return handler
