"""
语义搜索引擎 - 使用向量嵌入进行语义相似度搜索

Story 1.7: 集成 AI 语义搜索
- 使用 sentence-transformers 生成文本嵌入
- 支持向量相似度搜索
- 支持中英文语义理解
- 提供混合搜索 (关键词 + 语义)
"""

import os
import logging
import pickle
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SemanticSearchResult:
    """语义搜索结果"""
    document_id: int
    file_path: str
    file_name: str
    content_snippet: str
    similarity_score: float
    rank: int
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'document_id': self.document_id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'content_snippet': self.content_snippet,
            'similarity_score': self.similarity_score,
            'rank': self.rank,
            'metadata': self.metadata or {}
        }


class EmbeddingModel:
    """
    文本嵌入模型包装器

    支持多种嵌入模型:
    - sentence-transformers (本地模型)
    - paraphrase-multilingual-MiniLM-L12-v2 (推荐,支持中文)
    - all-MiniLM-L6-v2 (轻量级,英文)
    """

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        cache_dir: Optional[str] = None,
        device: str = "cpu"
    ):
        """
        初始化嵌入模型

        Args:
            model_name: 模型名称
            cache_dir: 模型缓存目录
            device: 计算设备 ('cpu' 或 'cuda')
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".cache", "sentence_transformers")
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self):
        """加载模型"""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=self.cache_dir,
                device=self.device
            )
            logger.info(f"Model loaded successfully, embedding dimension: {self.get_embedding_dimension()}")

        except ImportError:
            logger.error("sentence-transformers not installed. Please install: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        将文本编码为向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小
            show_progress: 是否显示进度

        Returns:
            嵌入向量数组 (n_texts, embedding_dim)
        """
        if not self.model:
            raise RuntimeError("Model not loaded")

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode texts: {e}")
            raise

    def encode_single(self, text: str) -> np.ndarray:
        """编码单个文本"""
        return self.encode([text])[0]

    def get_embedding_dimension(self) -> int:
        """获取嵌入维度"""
        if not self.model:
            raise RuntimeError("Model not loaded")
        return self.model.get_sentence_embedding_dimension()


class SemanticSearchEngine:
    """
    语义搜索引擎

    功能:
    1. 构建文档向量索引
    2. 语义相似度搜索
    3. 混合搜索 (关键词 + 语义)
    4. 向量索引持久化
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        index_path: Optional[str] = None
    ):
        """
        初始化语义搜索引擎

        Args:
            embedding_model: 嵌入模型
            index_path: 向量索引保存路径
        """
        self.embedding_model = embedding_model
        self.index_path = index_path

        # 向量索引: document_id -> embedding
        self.embeddings_index: Dict[int, np.ndarray] = {}

        # 文档元数据: document_id -> metadata
        self.documents_metadata: Dict[int, Dict[str, Any]] = {}

        # 加载已有索引
        if self.index_path and os.path.exists(self.index_path):
            self.load_index()

    def add_document(
        self,
        document_id: int,
        content: str,
        metadata: Dict[str, Any]
    ):
        """
        添加文档到索引

        Args:
            document_id: 文档ID
            content: 文档内容
            metadata: 文档元数据 (file_path, file_name等)
        """
        try:
            # 生成嵌入向量
            embedding = self.embedding_model.encode_single(content)

            # 添加到索引
            self.embeddings_index[document_id] = embedding
            self.documents_metadata[document_id] = metadata

            logger.debug(f"Added document {document_id} to semantic index")

        except Exception as e:
            logger.error(f"Failed to add document {document_id}: {e}")
            raise

    def add_documents_batch(
        self,
        documents: List[Tuple[int, str, Dict[str, Any]]],
        batch_size: int = 32
    ):
        """
        批量添加文档

        Args:
            documents: [(document_id, content, metadata), ...]
            batch_size: 批处理大小
        """
        if not documents:
            return

        try:
            # 提取内容
            doc_ids = [doc[0] for doc in documents]
            contents = [doc[1] for doc in documents]
            metadatas = [doc[2] for doc in documents]

            # 批量生成嵌入
            logger.info(f"Generating embeddings for {len(documents)} documents...")
            embeddings = self.embedding_model.encode(
                contents,
                batch_size=batch_size,
                show_progress=True
            )

            # 添加到索引
            for doc_id, embedding, metadata in zip(doc_ids, embeddings, metadatas):
                self.embeddings_index[doc_id] = embedding
                self.documents_metadata[doc_id] = metadata

            logger.info(f"Added {len(documents)} documents to semantic index")

        except Exception as e:
            logger.error(f"Failed to add documents batch: {e}")
            raise

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.3
    ) -> List[SemanticSearchResult]:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            min_similarity: 最小相似度阈值

        Returns:
            搜索结果列表
        """
        if not self.embeddings_index:
            logger.warning("Semantic index is empty")
            return []

        try:
            # 生成查询向量
            query_embedding = self.embedding_model.encode_single(query)

            # 计算相似度
            similarities = []
            for doc_id, doc_embedding in self.embeddings_index.items():
                similarity = self._cosine_similarity(query_embedding, doc_embedding)

                if similarity >= min_similarity:
                    similarities.append((doc_id, similarity))

            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            similarities = similarities[:top_k]

            # 构建结果
            results = []
            for rank, (doc_id, similarity) in enumerate(similarities, 1):
                metadata = self.documents_metadata.get(doc_id, {})

                result = SemanticSearchResult(
                    document_id=doc_id,
                    file_path=metadata.get('file_path', ''),
                    file_name=metadata.get('file_name', ''),
                    content_snippet=metadata.get('content_snippet', ''),
                    similarity_score=float(similarity),
                    rank=rank,
                    metadata=metadata
                )
                results.append(result)

            logger.info(f"Semantic search found {len(results)} results for query: {query[:50]}")
            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def save_index(self, path: Optional[str] = None):
        """
        保存向量索引到磁盘

        Args:
            path: 保存路径,如果为None则使用初始化时的路径
        """
        save_path = path or self.index_path
        if not save_path:
            raise ValueError("No save path specified")

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 保存索引
            index_data = {
                'embeddings': self.embeddings_index,
                'metadata': self.documents_metadata,
                'model_name': self.embedding_model.model_name,
                'embedding_dim': self.embedding_model.get_embedding_dimension()
            }

            with open(save_path, 'wb') as f:
                pickle.dump(index_data, f)

            logger.info(f"Saved semantic index to {save_path}")

        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise

    def load_index(self, path: Optional[str] = None):
        """
        从磁盘加载向量索引

        Args:
            path: 加载路径,如果为None则使用初始化时的路径
        """
        load_path = path or self.index_path
        if not load_path or not os.path.exists(load_path):
            logger.warning(f"Index file not found: {load_path}")
            return

        try:
            with open(load_path, 'rb') as f:
                index_data = pickle.load(f)

            # 验证模型兼容性
            if index_data['model_name'] != self.embedding_model.model_name:
                logger.warning(
                    f"Model mismatch: index uses {index_data['model_name']}, "
                    f"but current model is {self.embedding_model.model_name}"
                )

            self.embeddings_index = index_data['embeddings']
            self.documents_metadata = index_data['metadata']

            logger.info(f"Loaded semantic index from {load_path}, {len(self.embeddings_index)} documents")

        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            raise

    def clear_index(self):
        """清空索引"""
        self.embeddings_index.clear()
        self.documents_metadata.clear()
        logger.info("Semantic index cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        return {
            'total_documents': len(self.embeddings_index),
            'model_name': self.embedding_model.model_name,
            'embedding_dimension': self.embedding_model.get_embedding_dimension(),
            'index_size_mb': self._calculate_index_size() / (1024 * 1024)
        }

    def _calculate_index_size(self) -> int:
        """计算索引占用内存大小(字节)"""
        size = 0
        for embedding in self.embeddings_index.values():
            size += embedding.nbytes
        return size


# 混合搜索辅助函数
def combine_search_results(
    keyword_results: List[Dict[str, Any]],
    semantic_results: List[SemanticSearchResult],
    keyword_weight: float = 0.5,
    semantic_weight: float = 0.5,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    合并关键词搜索和语义搜索结果

    Args:
        keyword_results: 关键词搜索结果
        semantic_results: 语义搜索结果
        keyword_weight: 关键词搜索权重
        semantic_weight: 语义搜索权重
        top_k: 返回结果数量

    Returns:
        合并后的结果列表
    """
    # 归一化权重
    total_weight = keyword_weight + semantic_weight
    keyword_weight /= total_weight
    semantic_weight /= total_weight

    # 创建文档ID到分数的映射
    scores: Dict[int, float] = {}
    doc_info: Dict[int, Dict[str, Any]] = {}

    # 处理关键词搜索结果 (使用排名作为分数)
    for rank, result in enumerate(keyword_results, 1):
        doc_id = result.get('id')
        if doc_id:
            # 排名转分数: 第1名 = 1.0, 第10名 = 0.1
            rank_score = 1.0 / rank
            scores[doc_id] = scores.get(doc_id, 0) + rank_score * keyword_weight
            doc_info[doc_id] = result

    # 处理语义搜索结果
    for result in semantic_results:
        doc_id = result.document_id
        # 直接使用相似度分数
        semantic_score = result.similarity_score
        scores[doc_id] = scores.get(doc_id, 0) + semantic_score * semantic_weight

        if doc_id not in doc_info:
            doc_info[doc_id] = result.to_dict()

    # 按分数排序
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    # 构建最终结果
    combined_results = []
    for rank, (doc_id, score) in enumerate(sorted_docs, 1):
        result = doc_info[doc_id].copy()
        result['combined_score'] = score
        result['rank'] = rank
        combined_results.append(result)

    return combined_results
