"""
文本相似度计算模块

提供多种文本相似度算法
"""

from typing import List, Set
import re
from loguru import logger


class TextSimilarity:
    """
    文本相似度计算器
    
    Features:
    - 余弦相似度
    - Jaccard相似度
    - 编辑距离(Levenshtein)
    - TF-IDF相似度(可选)
    """
    
    @staticmethod
    def cosine(text1: str, text2: str, use_char: bool = False) -> float:
        """
        余弦相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            use_char: 是否使用字符级别(否则使用词级别)
        
        Returns:
            相似度 (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # 分词或分字
        if use_char:
            tokens1 = list(text1)
            tokens2 = list(text2)
        else:
            tokens1 = TextSimilarity._simple_tokenize(text1)
            tokens2 = TextSimilarity._simple_tokenize(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # 构建词汇表
        vocab = set(tokens1) | set(tokens2)
        
        # 构建词频向量
        vec1 = [tokens1.count(word) for word in vocab]
        vec2 = [tokens2.count(word) for word in vocab]
        
        # 计算余弦相似度
        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
        magnitude1 = sum(v * v for v in vec1) ** 0.5
        magnitude2 = sum(v * v for v in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    @staticmethod
    def jaccard(text1: str, text2: str, use_char: bool = False) -> float:
        """
        Jaccard相似度 (集合相似度)
        
        Args:
            text1: 文本1
            text2: 文本2
            use_char: 是否使用字符级别
        
        Returns:
            相似度 (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # 分词或分字
        if use_char:
            set1 = set(text1)
            set2 = set(text2)
        else:
            tokens1 = TextSimilarity._simple_tokenize(text1)
            tokens2 = TextSimilarity._simple_tokenize(text2)
            set1 = set(tokens1)
            set2 = set(tokens2)
        
        if not set1 or not set2:
            return 0.0
        
        # Jaccard = |A ∩ B| / |A ∪ B|
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def edit_distance(text1: str, text2: str) -> int:
        """
        编辑距离 (Levenshtein距离)
        
        计算将text1转换为text2所需的最少编辑操作次数
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            编辑距离
        """
        if not text1:
            return len(text2)
        if not text2:
            return len(text1)
        
        m, n = len(text1), len(text2)
        
        # 动态规划表
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # 初始化边界
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        # 填充DP表
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if text1[i - 1] == text2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],      # 删除
                        dp[i][j - 1],      # 插入
                        dp[i - 1][j - 1]   # 替换
                    )
        
        return dp[m][n]
    
    @staticmethod
    def edit_similarity(text1: str, text2: str) -> float:
        """
        基于编辑距离的相似度 (归一化到0-1)
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            相似度 (0-1)
        """
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        
        distance = TextSimilarity.edit_distance(text1, text2)
        max_len = max(len(text1), len(text2))
        
        return 1.0 - (distance / max_len) if max_len > 0 else 0.0
    
    @staticmethod
    def longest_common_subsequence(text1: str, text2: str) -> int:
        """
        最长公共子序列 (LCS)
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            LCS长度
        """
        if not text1 or not text2:
            return 0
        
        m, n = len(text1), len(text2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if text1[i - 1] == text2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        
        return dp[m][n]
    
    @staticmethod
    def lcs_similarity(text1: str, text2: str) -> float:
        """
        基于LCS的相似度
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            相似度 (0-1)
        """
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        
        lcs_len = TextSimilarity.longest_common_subsequence(text1, text2)
        max_len = max(len(text1), len(text2))
        
        return lcs_len / max_len if max_len > 0 else 0.0
    
    @staticmethod
    def ngram_similarity(
        text1: str,
        text2: str,
        n: int = 2,
        use_char: bool = True
    ) -> float:
        """
        N-gram相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            n: N-gram的n值
            use_char: 是否使用字符级别
        
        Returns:
            相似度 (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # 生成n-gram
        ngrams1 = TextSimilarity._generate_ngrams(text1, n, use_char)
        ngrams2 = TextSimilarity._generate_ngrams(text2, n, use_char)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        # 计算Jaccard相似度
        set1 = set(ngrams1)
        set2 = set(ngrams2)
        
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def _simple_tokenize(text: str) -> List[str]:
        """
        简单分词 (基于空格和标点)
        
        Args:
            text: 文本
        
        Returns:
            词列表
        """
        # 移除标点并转小写
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # 分割
        tokens = text.split()
        return [t for t in tokens if t]
    
    @staticmethod
    def _generate_ngrams(
        text: str,
        n: int,
        use_char: bool = True
    ) -> List[str]:
        """
        生成N-gram
        
        Args:
            text: 文本
            n: N值
            use_char: 是否使用字符级别
        
        Returns:
            N-gram列表
        """
        if use_char:
            items = list(text)
        else:
            items = TextSimilarity._simple_tokenize(text)
        
        if len(items) < n:
            return []
        
        ngrams = []
        for i in range(len(items) - n + 1):
            ngram = ''.join(items[i:i+n]) if use_char else ' '.join(items[i:i+n])
            ngrams.append(ngram)
        
        return ngrams
    
    @staticmethod
    def compare_all(text1: str, text2: str) -> dict:
        """
        使用所有算法比较两个文本
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            各种相似度分数的字典
        """
        return {
            'cosine': TextSimilarity.cosine(text1, text2),
            'jaccard': TextSimilarity.jaccard(text1, text2),
            'edit_similarity': TextSimilarity.edit_similarity(text1, text2),
            'lcs_similarity': TextSimilarity.lcs_similarity(text1, text2),
            'bigram_similarity': TextSimilarity.ngram_similarity(text1, text2, n=2),
            'trigram_similarity': TextSimilarity.ngram_similarity(text1, text2, n=3),
        }
