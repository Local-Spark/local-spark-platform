from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessEvent:
    event_id: str
    tenant_id: str
    business_id: str
    actor_id: str
    operation_id: str
