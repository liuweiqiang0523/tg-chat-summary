"""话题聚类模块"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from .summarizer import Message


@dataclass
class TopicCluster:
    """话题聚类结果"""
    title: str
    keywords: list[str]
    message_count: int
    messages: list[Message]
    summary: Optional[str] = None


class TopicExtractor:
    """话题提取器"""

    # 中文停用词
    STOPWORDS_ZH = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
        "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
        "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她",
        "吗", "那", "么", "啊", "哦", "嗯", "吧", "呢", "哈", "呀",
        "把", "被", "比", "从", "对", "给", "跟", "和", "及", "就",
        "可以", "可是", "来", "里", "没", "们", "那", "能", "你",
        "年", "让", "什么", "时候", "他们", "她们", "我们", "向",
        "要", "也", "已经", "因为", "用", "又", "在", "这个", "这个",
        "之", "中", "自己", "走", "最", "做", "个", "各", "给",
    }

    # 英文停用词
    STOPWORDS_EN = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above", "below",
        "between", "out", "off", "over", "under", "again", "further", "then",
        "once", "here", "there", "when", "where", "why", "how", "all", "both",
        "each", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "just",
        "because", "but", "and", "or", "if", "while", "about", "up", "down",
        "that", "this", "these", "those", "what", "which", "who", "whom",
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
        "you", "your", "yours", "yourself", "yourselves",
        "he", "him", "his", "himself", "she", "her", "hers", "herself",
        "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
    }

    def __init__(self):
        pass

    def extract_topics(
        self,
        messages: list[Message],
        max_topics: int = 5,
        language: str = "zh"
    ) -> list[TopicCluster]:
        """提取话题聚类"""
        if not messages:
            return []

        # 提取关键词
        keywords = self._extract_keywords(messages, language)

        # 基于关键词聚类
        clusters = self._cluster_by_keywords(messages, keywords, max_topics)

        # 为每个聚类生成标题
        for cluster in clusters:
            cluster.title = self._generate_title(cluster.keywords, language)

        return clusters

    def _extract_keywords(
        self,
        messages: list[Message],
        language: str
    ) -> list[tuple[str, int]]:
        """提取关键词"""
        # 合并所有消息文本
        text = " ".join([msg.text for msg in messages])

        # 分词并统计
        if language == "zh":
            words = self._tokenize_chinese(text)
            stopwords = self.STOPWORDS_ZH
        else:
            words = self._tokenize_english(text)
            stopwords = self.STOPWORDS_EN

        # 过滤停用词和短词
        filtered_words = [
            w for w in words
            if w not in stopwords and len(w) > 1
        ]

        # 统计词频
        word_counts = Counter(filtered_words)

        # 返回前 N 个关键词
        return word_counts.most_common(20)

    def _tokenize_chinese(self, text: str) -> list[str]:
        """中文分词（简单实现）"""
        # 使用正则提取中文词组
        # 这里使用简单的 2-4 字词组提取
        words = []

        # 提取 2 字词
        for i in range(len(text) - 1):
            word = text[i:i+2]
            if re.match(r'^[\u4e00-\u9fa5]{2}$', word):
                words.append(word)

        # 提取 3 字词
        for i in range(len(text) - 2):
            word = text[i:i+3]
            if re.match(r'^[\u4e00-\u9fa5]{3}$', word):
                words.append(word)

        # 提取 4 字词
        for i in range(len(text) - 3):
            word = text[i:i+4]
            if re.match(r'^[\u4e00-\u9fa5]{4}$', word):
                words.append(word)

        return words

    def _tokenize_english(self, text: str) -> list[str]:
        """英文分词"""
        # 转小写并分割
        text = text.lower()
        words = re.findall(r'\b[a-z]+\b', text)
        return words

    def _cluster_by_keywords(
        self,
        messages: list[Message],
        keywords: list[tuple[str, int]],
        max_clusters: int
    ) -> list[TopicCluster]:
        """基于关键词聚类"""
        clusters = []

        # 取前 max_clusters 个关键词作为聚类中心
        top_keywords = keywords[:max_clusters * 2]

        # 为每个关键词创建聚类
        for keyword, count in top_keywords:
            # 找出包含该关键词的消息
            related_messages = [
                msg for msg in messages
                if keyword in msg.text
            ]

            if len(related_messages) >= 3:  # 至少 3 条消息才算一个话题
                # 找出相关关键词
                related_keywords = self._find_related_keywords(
                    keyword, related_messages, top_keywords
                )

                clusters.append(TopicCluster(
                    title="",  # 稍后生成
                    keywords=[keyword] + related_keywords,
                    message_count=len(related_messages),
                    messages=related_messages
                ))

        # 合并相似的聚类
        clusters = self._merge_similar_clusters(clusters)

        return clusters[:max_clusters]

    def _find_related_keywords(
        self,
        main_keyword: str,
        messages: list[Message],
        all_keywords: list[tuple[str, int]]
    ) -> list[str]:
        """找出相关关键词"""
        related = []

        # 统计共现
        co_occurrence = Counter()
        for msg in messages:
            for word, _ in all_keywords:
                if word != main_keyword and word in msg.text:
                    co_occurrence[word] += 1

        # 返回共现最多的关键词
        for word, count in co_occurrence.most_common(3):
            if count >= 2:  # 至少共现 2 次
                related.append(word)

        return related

    def _merge_similar_clusters(
        self,
        clusters: list[TopicCluster]
    ) -> list[TopicCluster]:
        """合并相似的聚类"""
        if len(clusters) <= 1:
            return clusters

        merged = []
        used = set()

        for i, cluster1 in enumerate(clusters):
            if i in used:
                continue

            # 找相似的聚类
            similar_indices = [i]
            for j, cluster2 in enumerate(clusters[i+1:], i+1):
                if j in used:
                    continue

                # 计算关键词重叠度
                overlap = len(
                    set(cluster1.keywords) & set(cluster2.keywords)
                )
                if overlap > 0:
                    similar_indices.append(j)

            # 合并相似聚类
            if len(similar_indices) > 1:
                merged_messages = []
                merged_keywords = set()
                for idx in similar_indices:
                    merged_messages.extend(clusters[idx].messages)
                    merged_keywords.update(clusters[idx].keywords)
                    used.add(idx)

                merged.append(TopicCluster(
                    title="",
                    keywords=list(merged_keywords)[:5],
                    message_count=len(merged_messages),
                    messages=merged_messages
                ))
            else:
                merged.append(cluster1)
                used.add(i)

        return merged

    def _generate_title(self, keywords: list[str], language: str) -> str:
        """生成话题标题"""
        if not keywords:
            return "其他讨论" if language == "zh" else "Other Discussion"

        # 取前 2-3 个关键词组合成标题
        title_keywords = keywords[:3]

        if language == "zh":
            return "、".join(title_keywords) + "相关讨论"
        else:
            return "Discussion about " + ", ".join(title_keywords)
