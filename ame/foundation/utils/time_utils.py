"""
时间工具函数
"""
from datetime import datetime, timedelta
from typing import Optional


def now() -> datetime:
    """获取当前时间"""
    return datetime.now()


def to_iso(dt: datetime) -> str:
    """转换为 ISO 格式字符串"""
    return dt.isoformat()


def from_iso(iso_str: str) -> datetime:
    """从 ISO 格式字符串解析"""
    return datetime.fromisoformat(iso_str)


def days_ago(days: int) -> datetime:
    """获取 N 天前的时间"""
    return now() - timedelta(days=days)


def hours_ago(hours: int) -> datetime:
    """获取 N 小时前的时间"""
    return now() - timedelta(hours=hours)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间"""
    return dt.strftime(fmt)


def parse_datetime(dt_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """解析时间字符串"""
    return datetime.strptime(dt_str, fmt)


def time_diff_seconds(dt1: datetime, dt2: datetime) -> int:
    """计算两个时间的秒数差"""
    return int(abs((dt1 - dt2).total_seconds()))


def is_recent(dt: datetime, hours: int = 24) -> bool:
    """判断时间是否在最近 N 小时内"""
    return dt > hours_ago(hours)
