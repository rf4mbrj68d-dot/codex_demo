from __future__ import annotations

from backend.data_sources.adapters.chinamoney_adapter import ChinaMoneyAdapter
from backend.data_sources.core.source_models import SourceHealth, SourceManifest


class NafmiiAdapter(ChinaMoneyAdapter):
    def __init__(self):
        super().__init__()
        self.manifest = SourceManifest.from_dict({
            "source_id": "nafmii",
            "source_name": "交易商协会",
            "enabled": True,
            "markets": ["CN"],
            "source_types": ["bond"],
            "capabilities": ["search", "fetch"],
            "ttl": {"bond_index": "7d"},
            "priority": 50,
        })

    def healthcheck(self) -> SourceHealth:
        return SourceHealth("nafmii", "ready", "交易商协会适配器可用，当前启用稳定摘要回退")
