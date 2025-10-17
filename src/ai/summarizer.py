"""
文档智能摘要 - 使用 AI 生成文档摘要和关键信息提取

Story 1.8: 实现文档智能摘要
- 自动生成文档摘要
- 提取关键点和实体
- 支持多种摘要策略
- 缓存摘要结果
"""

import os
import logging
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class SummaryStrategy(Enum):
    """摘要策略"""
    EXTRACTIVE = "extractive"  # 抽取式摘要 (选择重要句子)
    ABSTRACTIVE = "abstractive"  # 生成式摘要 (生成新句子)
    HYBRID = "hybrid"  # 混合策略


@dataclass
class SummaryResult:
    """摘要结果"""
    document_id: int
    summary: str
    key_points: List[str] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0
    strategy: str = "extractive"
    word_count: int = 0
    original_length: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'document_id': self.document_id,
            'summary': self.summary,
            'key_points': self.key_points,
            'entities': self.entities,
            'keywords': self.keywords,
            'confidence': self.confidence,
            'strategy': self.strategy,
            'word_count': self.word_count,
            'original_length': self.original_length
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class DocumentSummarizer:
    """
    文档摘要生成器

    支持多种摘要方法:
    1. 抽取式摘要 (基于句子重要性评分)
    2. 生成式摘要 (使用 Transformers 模型)
    3. 关键词提取
    4. 实体识别
    """

    def __init__(
        self,
        strategy: SummaryStrategy = SummaryStrategy.EXTRACTIVE,
        model_name: Optional[str] = None,
        max_summary_length: int = 300,
        cache_dir: Optional[str] = None
    ):
        """
        初始化摘要生成器

        Args:
            strategy: 摘要策略
            model_name: 模型名称 (生成式摘要使用)
            max_summary_length: 最大摘要长度
            cache_dir: 缓存目录
        """
        self.strategy = strategy
        self.model_name = model_name
        self.max_summary_length = max_summary_length
        self.cache_dir = cache_dir

        # 摘要缓存: content_hash -> SummaryResult
        self.cache: Dict[str, SummaryResult] = {}

        # 模型初始化
        self.model = None
        self.tokenizer = None

        if self.strategy in [SummaryStrategy.ABSTRACTIVE, SummaryStrategy.HYBRID]:
            self._load_model()

    def _load_model(self):
        """加载生成式摘要模型"""
        if not self.model_name:
            # 默认使用中英文摘要模型
            self.model_name = "google/mt5-small"

        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

            logger.info(f"Loading summarization model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            logger.info("Summarization model loaded successfully")

        except ImportError:
            logger.error("transformers not installed. Please install: pip install transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load summarization model: {e}")
            # 降级到抽取式摘要
            logger.warning("Falling back to extractive summarization")
            self.strategy = SummaryStrategy.EXTRACTIVE

    def summarize(
        self,
        document_id: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SummaryResult:
        """
        生成文档摘要

        Args:
            document_id: 文档ID
            content: 文档内容
            metadata: 文档元数据

        Returns:
            摘要结果
        """
        # 检查缓存
        content_hash = self._hash_content(content)
        if content_hash in self.cache:
            logger.debug(f"Using cached summary for document {document_id}")
            cached_result = self.cache[content_hash]
            cached_result.document_id = document_id  # 更新文档ID
            return cached_result

        try:
            # 根据策略生成摘要
            if self.strategy == SummaryStrategy.EXTRACTIVE:
                summary_text = self._extractive_summarize(content)
            elif self.strategy == SummaryStrategy.ABSTRACTIVE:
                summary_text = self._abstractive_summarize(content)
            else:  # HYBRID
                summary_text = self._hybrid_summarize(content)

            # 提取关键点
            key_points = self._extract_key_points(content)

            # 提取关键词
            keywords = self._extract_keywords(content)

            # 实体识别 (简化版)
            entities = self._extract_entities(content)

            # 构建结果
            result = SummaryResult(
                document_id=document_id,
                summary=summary_text,
                key_points=key_points,
                entities=entities,
                keywords=keywords,
                confidence=0.8,  # 简化实现,固定置信度
                strategy=self.strategy.value,
                word_count=len(summary_text),
                original_length=len(content)
            )

            # 缓存结果
            self.cache[content_hash] = result

            logger.info(f"Generated summary for document {document_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to generate summary for document {document_id}: {e}")
            raise

    def _extractive_summarize(self, content: str) -> str:
        """
        抽取式摘要 - 选择最重要的句子

        算法:
        1. 分句
        2. 计算句子重要性 (基于TF-IDF)
        3. 选择top-N句子
        """
        # 分句
        sentences = self._split_sentences(content)

        if not sentences:
            return ""

        # 如果内容很短,直接返回
        if len(content) <= self.max_summary_length:
            return content

        # 计算句子重要性
        sentence_scores = self._score_sentences(sentences, content)

        # 选择最重要的句子
        num_sentences = max(3, min(5, len(sentences) // 3))
        top_sentences = sorted(
            sentence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:num_sentences]

        # 按原文顺序排列
        top_sentences.sort(key=lambda x: sentences.index(x[0]))

        # 组合摘要
        summary = ' '.join([sent for sent, score in top_sentences])

        # 截断到最大长度
        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length] + "..."

        return summary

    def _abstractive_summarize(self, content: str) -> str:
        """
        生成式摘要 - 使用模型生成新文本

        注意: 需要加载 Transformers 模型
        """
        if not self.model or not self.tokenizer:
            logger.warning("Model not loaded, falling back to extractive summarization")
            return self._extractive_summarize(content)

        try:
            # 截断输入
            max_input_length = 512
            inputs = self.tokenizer(
                content,
                max_length=max_input_length,
                truncation=True,
                return_tensors="pt"
            )

            # 生成摘要
            summary_ids = self.model.generate(
                inputs["input_ids"],
                max_length=self.max_summary_length,
                min_length=50,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )

            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            return summary

        except Exception as e:
            logger.error(f"Abstractive summarization failed: {e}")
            return self._extractive_summarize(content)

    def _hybrid_summarize(self, content: str) -> str:
        """
        混合摘要 - 结合抽取式和生成式

        先用抽取式缩减内容,再用生成式生成流畅摘要
        """
        # 先抽取重要句子
        extractive_summary = self._extractive_summarize(content)

        # 如果抽取式摘要已经很短,直接返回
        if len(extractive_summary) <= self.max_summary_length * 0.8:
            return extractive_summary

        # 对抽取式摘要进行生成式重写
        return self._abstractive_summarize(extractive_summary)

    def _split_sentences(self, text: str) -> List[str]:
        """
        分句

        简化实现,基于标点符号
        """
        import re

        # 中英文句子分隔符
        sentence_delimiters = r'[。！？!?;；\n]+'

        sentences = re.split(sentence_delimiters, text)
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _score_sentences(self, sentences: List[str], full_text: str) -> Dict[str, float]:
        """
        计算句子重要性分数

        使用简单的启发式方法:
        1. 句子长度 (中等长度句子更重要)
        2. 位置 (开头和结尾的句子更重要)
        3. 关键词频率
        """
        scores = {}

        # 提取关键词
        keywords = self._extract_keywords(full_text, top_k=20)
        keyword_set = set(keywords)

        for i, sentence in enumerate(sentences):
            score = 0.0

            # 位置分数 (开头和结尾更重要)
            if i < 3:
                score += 2.0
            elif i >= len(sentences) - 3:
                score += 1.5

            # 长度分数 (中等长度)
            length = len(sentence)
            if 50 <= length <= 200:
                score += 1.5
            elif 20 <= length <= 300:
                score += 1.0

            # 关键词分数
            sentence_words = set(sentence.split())
            keyword_count = len(sentence_words & keyword_set)
            score += keyword_count * 0.5

            scores[sentence] = score

        return scores

    def _extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """
        提取关键点

        简化实现: 选择包含关键词最多的句子
        """
        sentences = self._split_sentences(content)

        if len(sentences) <= max_points:
            return sentences

        # 计算句子分数
        sentence_scores = self._score_sentences(sentences, content)

        # 选择top-N
        top_sentences = sorted(
            sentence_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:max_points]

        # 保持原文顺序
        top_sentences.sort(key=lambda x: sentences.index(x[0]))

        return [sent for sent, score in top_sentences]

    def _extract_keywords(self, content: str, top_k: int = 10) -> List[str]:
        """
        提取关键词

        简化实现: 基于词频和长度
        """
        import re
        from collections import Counter

        # 分词 (简单空格分词)
        words = re.findall(r'\b\w+\b', content.lower())

        # 过滤停用词和短词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were'}
        words = [w for w in words if len(w) > 2 and w not in stop_words]

        # 统计词频
        word_counts = Counter(words)

        # 返回最常见的词
        keywords = [word for word, count in word_counts.most_common(top_k)]

        return keywords

    def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """
        实体识别

        简化实现: 提取大写开头的词作为潜在实体
        后续可集成 NER 模型
        """
        import re

        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'other': []
        }

        # 提取大写开头的词组 (2-4个词)
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b'
        potential_entities = re.findall(pattern, content)

        # 去重
        potential_entities = list(set(potential_entities))[:10]

        # 简单分类 (基于关键词)
        for entity in potential_entities:
            entity_lower = entity.lower()

            if any(word in entity_lower for word in ['公司', 'company', 'corp', 'inc', '集团']):
                entities['organizations'].append(entity)
            elif any(word in entity_lower for word in ['市', 'city', '省', '国', 'country']):
                entities['locations'].append(entity)
            else:
                entities['other'].append(entity)

        return entities

    def _hash_content(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("Summary cache cleared")

    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


# 批量摘要生成辅助函数
def batch_summarize_documents(
    summarizer: DocumentSummarizer,
    documents: List[Dict[str, Any]],
    save_to_db: bool = True,
    db_manager = None
) -> List[SummaryResult]:
    """
    批量生成文档摘要

    Args:
        summarizer: 摘要生成器
        documents: 文档列表 [{'id': ..., 'content': ..., 'metadata': ...}, ...]
        save_to_db: 是否保存到数据库
        db_manager: 数据库管理器

    Returns:
        摘要结果列表
    """
    results = []

    for doc in documents:
        try:
            result = summarizer.summarize(
                document_id=doc['id'],
                content=doc['content'],
                metadata=doc.get('metadata')
            )
            results.append(result)

            # 保存到数据库
            if save_to_db and db_manager:
                db_manager.save_summary(result)

        except Exception as e:
            logger.error(f"Failed to summarize document {doc.get('id')}: {e}")
            continue

    logger.info(f"Batch summarized {len(results)}/{len(documents)} documents")
    return results
