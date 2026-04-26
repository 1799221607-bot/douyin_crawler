from collector.base import BaseCollector
from collector.video_collector import VideoCollector


class CollectorRegistry:
    """
    采集器插件注册表。
    新增采集器只需在此注册，其余代码无需修改。
    """

    def __init__(self):
        self._registry: dict[str, BaseCollector] = {}

    def register(self, collector: BaseCollector):
        self._registry[collector.collector_type] = collector

    def get(self, collector_type: str) -> BaseCollector:
        if collector_type not in self._registry:
            raise ValueError(f"未注册的采集器类型: {collector_type}")
        return self._registry[collector_type]

    def list_types(self) -> list[str]:
        return list(self._registry.keys())


# 全局单例注册表
collector_registry = CollectorRegistry()
collector_registry.register(VideoCollector())

# 后续扩展示例（取消注释即可接入）:
# from collector.keyword_collector import KeywordCollector
# collector_registry.register(KeywordCollector())
# from collector.comment_collector import CommentCollector
# collector_registry.register(CommentCollector())
