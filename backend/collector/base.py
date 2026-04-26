from abc import ABC, abstractmethod
from typing import Any


class BaseCollector(ABC):
    """
    采集器插件基类。
    新增采集类型只需继承此类并实现 collect()，
    然后在 registry.py 中注册即可，无需修改现有代码。
    """

    @property
    @abstractmethod
    def collector_type(self) -> str:
        """
        采集器类型标识，全局唯一。
        例: 'video' | 'keyword' | 'comment'
        """
        pass

    @abstractmethod
    async def collect(self, target: dict, config: dict) -> list[dict]:
        """
        执行采集，返回原始数据字典列表。

        Args:
            target: 采集目标信息
                - video collector:   {'user_url': str, 'sec_user_id': str}
                - keyword collector: {'keyword': str, 'max_count': int}
                - comment collector: {'aweme_id': str}
            config: 全局采集配置
                - cookie: str
                - proxy: str | None
                - download: bool
                - download_dir: str

        Returns:
            list[dict]: 统一格式的数据列表，每项至少含 'aweme_id'
        """
        pass

    async def on_new_items(self, items: list[dict], context: dict) -> None:
        """
        钩子：新数据采集完成后调用（可选实现）。
        用于触发通知、AI处理等后置动作。
        """
        pass
