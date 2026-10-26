from typing import Protocol

from ..models.monitored_subscription import MonitoredSubscription


class MonitoredSubscriptionReader(Protocol):
    def list_active_subscriptions(self) -> list[MonitoredSubscription]: ...
