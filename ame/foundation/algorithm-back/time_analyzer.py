"""
时间模式分析模块

分析用户的时间行为模式
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter
import statistics
from loguru import logger


@dataclass
class TimePattern:
    """时间模式"""
    pattern_type: str            # 模式类型 ("hourly", "daily", "weekly", "periodic")
    description: str             # 模式描述
    frequency: int               # 频率
    confidence: float            # 置信度 (0-1)
    metadata: Dict = None        # 额外信息
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ActivityPeriod:
    """活跃时段"""
    start_hour: int              # 开始小时 (0-23)
    end_hour: int                # 结束小时 (0-23)
    activity_level: float        # 活跃度 (0-1)
    event_count: int             # 事件数量


class TimePatternAnalyzer:
    """
    时间模式分析器
    
    Features:
    - 活跃时段分析
    - 周期性检测
    - 习惯识别
    - 时间聚类
    """
    
    def __init__(self, min_confidence: float = 0.6):
        """
        初始化
        
        Args:
            min_confidence: 最小置信度阈值
        """
        self.min_confidence = min_confidence
    
    def analyze_active_hours(
        self,
        timestamps: List[datetime],
        bin_size: int = 1
    ) -> Dict[int, int]:
        """
        分析活跃时段 (小时级统计)
        
        Args:
            timestamps: 时间戳列表
            bin_size: 时间区间大小 (小时)
        
        Returns:
            小时 -> 事件数量的映射
        """
        if not timestamps:
            return {}
        
        # 统计每个小时的事件数
        hour_counts = Counter([ts.hour for ts in timestamps])
        
        logger.debug(f"分析了 {len(timestamps)} 个时间戳, 覆盖 {len(hour_counts)} 个小时")
        
        return dict(hour_counts)
    
    def find_peak_hours(
        self,
        timestamps: List[datetime],
        top_k: int = 3
    ) -> List[Tuple[int, int]]:
        """
        查找活跃高峰时段
        
        Args:
            timestamps: 时间戳列表
            top_k: 返回Top-K高峰时段
        
        Returns:
            [(小时, 事件数), ...] 列表
        """
        hour_counts = self.analyze_active_hours(timestamps)
        
        # 按事件数排序
        sorted_hours = sorted(
            hour_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_hours[:top_k]
    
    def identify_activity_periods(
        self,
        timestamps: List[datetime],
        min_activity_ratio: float = 0.3
    ) -> List[ActivityPeriod]:
        """
        识别活跃时段 (连续的高活跃时间区间)
        
        Args:
            timestamps: 时间戳列表
            min_activity_ratio: 最小活跃度比例
        
        Returns:
            活跃时段列表
        """
        if not timestamps:
            return []
        
        hour_counts = self.analyze_active_hours(timestamps)
        max_count = max(hour_counts.values()) if hour_counts else 0
        
        if max_count == 0:
            return []
        
        # 计算每小时的活跃度
        activity_levels = {
            hour: count / max_count
            for hour, count in hour_counts.items()
        }
        
        # 识别连续的高活跃时段
        periods = []
        current_period = None
        
        for hour in range(24):
            activity = activity_levels.get(hour, 0)
            
            if activity >= min_activity_ratio:
                if current_period is None:
                    current_period = {
                        'start': hour,
                        'end': hour,
                        'total_activity': activity,
                        'count': 1,
                        'events': hour_counts.get(hour, 0)
                    }
                else:
                    current_period['end'] = hour
                    current_period['total_activity'] += activity
                    current_period['count'] += 1
                    current_period['events'] += hour_counts.get(hour, 0)
            else:
                if current_period is not None:
                    # 保存当前时段
                    avg_activity = current_period['total_activity'] / current_period['count']
                    periods.append(ActivityPeriod(
                        start_hour=current_period['start'],
                        end_hour=current_period['end'],
                        activity_level=avg_activity,
                        event_count=current_period['events']
                    ))
                    current_period = None
        
        # 处理跨越午夜的情况
        if current_period is not None:
            avg_activity = current_period['total_activity'] / current_period['count']
            periods.append(ActivityPeriod(
                start_hour=current_period['start'],
                end_hour=current_period['end'],
                activity_level=avg_activity,
                event_count=current_period['events']
            ))
        
        logger.info(f"识别到 {len(periods)} 个活跃时段")
        return periods
    
    def detect_periodicity(
        self,
        timestamps: List[datetime],
        max_period_days: int = 30
    ) -> Optional[TimePattern]:
        """
        检测周期性 (例如每周一开会)
        
        Args:
            timestamps: 时间戳列表
            max_period_days: 最大周期天数
        
        Returns:
            检测到的周期模式,无则返回None
        """
        if len(timestamps) < 3:
            logger.warning("时间戳数量不足,无法检测周期性")
            return None
        
        # 排序时间戳
        sorted_ts = sorted(timestamps)
        
        # 计算相邻事件的时间间隔
        intervals = []
        for i in range(len(sorted_ts) - 1):
            interval = (sorted_ts[i + 1] - sorted_ts[i]).total_seconds() / 3600  # 小时
            intervals.append(interval)
        
        if not intervals:
            return None
        
        # 尝试检测固定周期
        # 1. 每日 (24小时 ± 2小时)
        daily_intervals = [i for i in intervals if 22 <= i <= 26]
        if len(daily_intervals) >= len(intervals) * 0.5:
            return TimePattern(
                pattern_type="daily",
                description="每日固定时间活跃",
                frequency=len(daily_intervals),
                confidence=len(daily_intervals) / len(intervals),
                metadata={"avg_interval_hours": statistics.mean(daily_intervals)}
            )
        
        # 2. 每周 (168小时 ± 12小时)
        weekly_intervals = [i for i in intervals if 156 <= i <= 180]
        if len(weekly_intervals) >= len(intervals) * 0.4:
            return TimePattern(
                pattern_type="weekly",
                description="每周固定时间活跃",
                frequency=len(weekly_intervals),
                confidence=len(weekly_intervals) / len(intervals),
                metadata={"avg_interval_hours": statistics.mean(weekly_intervals)}
            )
        
        # 3. 工作日模式 (检测周末间隔)
        # 简化实现: 检测是否有规律的3天间隔(周五->周一)
        workday_pattern = self._detect_workday_pattern(sorted_ts)
        if workday_pattern:
            return workday_pattern
        
        logger.debug("未检测到明显的周期性模式")
        return None
    
    def _detect_workday_pattern(
        self,
        sorted_timestamps: List[datetime]
    ) -> Optional[TimePattern]:
        """
        检测工作日模式
        
        Args:
            sorted_timestamps: 排序后的时间戳
        
        Returns:
            工作日模式,无则返回None
        """
        if len(sorted_timestamps) < 5:
            return None
        
        # 统计星期几的分布
        weekday_counts = Counter([ts.weekday() for ts in sorted_timestamps])
        
        # 工作日 (0-4: 周一到周五)
        workday_count = sum(weekday_counts[i] for i in range(5))
        # 周末 (5-6: 周六周日)
        weekend_count = sum(weekday_counts.get(i, 0) for i in [5, 6])
        
        total = workday_count + weekend_count
        if total == 0:
            return None
        
        workday_ratio = workday_count / total
        
        # 如果工作日活跃度明显高于周末
        if workday_ratio >= 0.7:
            return TimePattern(
                pattern_type="workday",
                description="工作日活跃模式",
                frequency=workday_count,
                confidence=workday_ratio,
                metadata={
                    "workday_count": workday_count,
                    "weekend_count": weekend_count,
                    "weekday_distribution": dict(weekday_counts)
                }
            )
        
        return None
    
    def analyze_time_gaps(
        self,
        timestamps: List[datetime]
    ) -> Dict[str, float]:
        """
        分析时间间隔统计
        
        Args:
            timestamps: 时间戳列表
        
        Returns:
            统计信息字典
        """
        if len(timestamps) < 2:
            return {}
        
        sorted_ts = sorted(timestamps)
        
        # 计算间隔 (小时)
        gaps = [
            (sorted_ts[i + 1] - sorted_ts[i]).total_seconds() / 3600
            for i in range(len(sorted_ts) - 1)
        ]
        
        return {
            'min_gap_hours': min(gaps),
            'max_gap_hours': max(gaps),
            'avg_gap_hours': statistics.mean(gaps),
            'median_gap_hours': statistics.median(gaps),
            'std_gap_hours': statistics.stdev(gaps) if len(gaps) > 1 else 0.0
        }
    
    def find_all_patterns(
        self,
        timestamps: List[datetime]
    ) -> List[TimePattern]:
        """
        综合分析,查找所有时间模式
        
        Args:
            timestamps: 时间戳列表
        
        Returns:
            时间模式列表
        """
        patterns = []
        
        # 1. 周期性检测
        periodic_pattern = self.detect_periodicity(timestamps)
        if periodic_pattern and periodic_pattern.confidence >= self.min_confidence:
            patterns.append(periodic_pattern)
        
        # 2. 活跃时段分析
        activity_periods = self.identify_activity_periods(timestamps)
        if activity_periods:
            # 生成时段模式
            for period in activity_periods:
                if period.activity_level >= self.min_confidence:
                    patterns.append(TimePattern(
                        pattern_type="hourly",
                        description=f"{period.start_hour}:00-{period.end_hour}:00 活跃时段",
                        frequency=period.event_count,
                        confidence=period.activity_level,
                        metadata={
                            'start_hour': period.start_hour,
                            'end_hour': period.end_hour
                        }
                    ))
        
        logger.info(f"共识别出 {len(patterns)} 个时间模式")
        return patterns
