"""
语义搜索引擎测试

测试 Story 1.7 的实现
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from src.ai.semantic_search import (
    EmbeddingModel,
    SemanticSearchEngine,
    SemanticSearchResult,
    combine_search_results
)


class TestEmbeddingModel:
    """嵌入模型测试"""

    @pytest.fixture
    def mock_sentence_transformer(self):
        """模拟 SentenceTransformer"""
        with patch('src.ai.semantic_search.SentenceTransformer') as mock:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = np.random.rand(10, 384)
            mock.return_value = mock_model
            yield mock

    def test_embedding_model_init(self, mock_sentence_transformer):
        """测试模型初始化"""
        model = EmbeddingModel(model_name="test-model")

        assert model.model_name == "test-model"
        assert model.model is not None
        assert model.get_embedding_dimension() == 384

    def test_encode_texts(self, mock_sentence_transformer):
        """测试文本编码"""
        model = EmbeddingModel()

        texts = ["Hello world", "Test document"]
        embeddings = model.encode(texts)

        assert embeddings.shape == (10, 384)  # Mock返回的形状
        model.model.encode.assert_called_once()

    def test_encode_single(self, mock_sentence_transformer):
        """测试单个文本编码"""
        model = EmbeddingModel()
        model.model.encode.return_value = np.array([[0.1, 0.2, 0.3]])

        embedding = model.encode_single("Test text")

        assert embedding.shape == (3,)
        assert isinstance(embedding, np.ndarray)


class TestSemanticSearchEngine:
    """语义搜索引擎测试"""

    @pytest.fixture
    def mock_embedding_model(self):
        """模拟嵌入模型"""
        model = Mock(spec=EmbeddingModel)
        model.model_name = "test-model"
        model.get_embedding_dimension.return_value = 384
        model.encode_single.return_value = np.random.rand(384)
        model.encode.return_value = np.random.rand(5, 384)
        return model

    @pytest.fixture
    def search_engine(self, mock_embedding_model):
        """创建搜索引擎实例"""
        return SemanticSearchEngine(
            embedding_model=mock_embedding_model
        )

    def test_init(self, mock_embedding_model):
        """测试初始化"""
        engine = SemanticSearchEngine(mock_embedding_model)

        assert engine.embedding_model == mock_embedding_model
        assert len(engine.embeddings_index) == 0
        assert len(engine.documents_metadata) == 0

    def test_add_document(self, search_engine, mock_embedding_model):
        """测试添加文档"""
        doc_id = 1
        content = "This is a test document"
        metadata = {'file_path': '/test/doc.txt', 'file_name': 'doc.txt'}

        search_engine.add_document(doc_id, content, metadata)

        assert doc_id in search_engine.embeddings_index
        assert doc_id in search_engine.documents_metadata
        assert search_engine.documents_metadata[doc_id] == metadata
        mock_embedding_model.encode_single.assert_called_once_with(content)

    def test_add_documents_batch(self, search_engine, mock_embedding_model):
        """测试批量添加文档"""
        documents = [
            (1, "Doc 1", {'file_path': '/test/1.txt'}),
            (2, "Doc 2", {'file_path': '/test/2.txt'}),
            (3, "Doc 3", {'file_path': '/test/3.txt'}),
        ]

        search_engine.add_documents_batch(documents)

        assert len(search_engine.embeddings_index) == 3
        assert len(search_engine.documents_metadata) == 3
        assert 1 in search_engine.embeddings_index
        assert 2 in search_engine.embeddings_index
        assert 3 in search_engine.embeddings_index

    def test_search_empty_index(self, search_engine):
        """测试空索引搜索"""
        results = search_engine.search("test query")

        assert results == []

    def test_search_with_results(self, search_engine, mock_embedding_model):
        """测试搜索返回结果"""
        # 添加文档
        documents = [
            (1, "Python programming", {'file_path': '/test/1.txt', 'file_name': '1.txt'}),
            (2, "Machine learning", {'file_path': '/test/2.txt', 'file_name': '2.txt'}),
        ]
        search_engine.add_documents_batch(documents)

        # 模拟查询向量
        query_embedding = np.array([0.5] * 384)
        mock_embedding_model.encode_single.return_value = query_embedding

        # 执行搜索
        results = search_engine.search("Python", top_k=2)

        assert len(results) <= 2
        for result in results:
            assert isinstance(result, SemanticSearchResult)
            assert result.similarity_score >= 0
            assert result.similarity_score <= 1

    def test_cosine_similarity(self, search_engine):
        """测试余弦相似度计算"""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        similarity = search_engine._cosine_similarity(vec1, vec2)

        assert abs(similarity - 1.0) < 0.0001

        vec3 = np.array([1.0, 0.0, 0.0])
        vec4 = np.array([0.0, 1.0, 0.0])

        similarity2 = search_engine._cosine_similarity(vec3, vec4)

        assert abs(similarity2) < 0.0001

    def test_save_and_load_index(self, search_engine, mock_embedding_model):
        """测试索引保存和加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = os.path.join(tmpdir, "test_index.pkl")

            # 添加文档
            search_engine.add_document(
                1,
                "Test document",
                {'file_path': '/test.txt'}
            )

            # 保存索引
            search_engine.save_index(index_path)
            assert os.path.exists(index_path)

            # 创建新引擎并加载索引
            new_engine = SemanticSearchEngine(
                mock_embedding_model,
                index_path=index_path
            )
            new_engine.load_index()

            assert len(new_engine.embeddings_index) == 1
            assert 1 in new_engine.embeddings_index

    def test_clear_index(self, search_engine):
        """测试清空索引"""
        search_engine.add_document(1, "Test", {'file_path': '/test.txt'})
        assert len(search_engine.embeddings_index) == 1

        search_engine.clear_index()

        assert len(search_engine.embeddings_index) == 0
        assert len(search_engine.documents_metadata) == 0

    def test_get_statistics(self, search_engine, mock_embedding_model):
        """测试获取统计信息"""
        search_engine.add_document(1, "Test", {'file_path': '/test.txt'})

        stats = search_engine.get_statistics()

        assert stats['total_documents'] == 1
        assert 'model_name' in stats
        assert stats['embedding_dimension'] == 384


class TestCombineSearchResults:
    """测试混合搜索结果合并"""

    def test_combine_results(self):
        """测试结果合并"""
        keyword_results = [
            {'id': 1, 'file_path': '/doc1.txt', 'score': 10},
            {'id': 2, 'file_path': '/doc2.txt', 'score': 8},
        ]

        semantic_results = [
            SemanticSearchResult(
                document_id=1,
                file_path='/doc1.txt',
                file_name='doc1.txt',
                content_snippet='Test content',
                similarity_score=0.9,
                rank=1
            ),
            SemanticSearchResult(
                document_id=3,
                file_path='/doc3.txt',
                file_name='doc3.txt',
                content_snippet='Other content',
                similarity_score=0.7,
                rank=2
            ),
        ]

        combined = combine_search_results(
            keyword_results,
            semantic_results,
            keyword_weight=0.5,
            semantic_weight=0.5,
            top_k=3
        )

        assert len(combined) <= 3
        assert all('combined_score' in result for result in combined)
        assert all('rank' in result for result in combined)

    def test_combine_with_weights(self):
        """测试权重调整"""
        keyword_results = [{'id': 1, 'score': 10}]
        semantic_results = [
            SemanticSearchResult(
                document_id=1,
                file_path='/doc1.txt',
                file_name='doc1.txt',
                content_snippet='',
                similarity_score=0.5,
                rank=1
            )
        ]

        # 关键词权重高
        combined1 = combine_search_results(
            keyword_results,
            semantic_results,
            keyword_weight=0.9,
            semantic_weight=0.1
        )

        # 语义权重高
        combined2 = combine_search_results(
            keyword_results,
            semantic_results,
            keyword_weight=0.1,
            semantic_weight=0.9
        )

        assert len(combined1) == 1
        assert len(combined2) == 1


@pytest.mark.integration
class TestSemanticSearchIntegration:
    """集成测试 - 需要实际的模型"""

    @pytest.mark.skip(reason="Requires sentence-transformers installation")
    def test_real_model_encoding(self):
        """测试真实模型编码"""
        model = EmbeddingModel(model_name="all-MiniLM-L6-v2")

        texts = ["Hello world", "Machine learning"]
        embeddings = model.encode(texts)

        assert embeddings.shape[0] == 2
        assert embeddings.shape[1] > 0

    @pytest.mark.skip(reason="Requires sentence-transformers installation")
    def test_real_semantic_search(self):
        """测试真实语义搜索"""
        model = EmbeddingModel(model_name="all-MiniLM-L6-v2")
        engine = SemanticSearchEngine(model)

        # 添加文档
        documents = [
            (1, "Python is a programming language", {'file_path': '/1.txt', 'file_name': '1.txt', 'content_snippet': 'Python...'}),
            (2, "Machine learning with scikit-learn", {'file_path': '/2.txt', 'file_name': '2.txt', 'content_snippet': 'ML...'}),
            (3, "Cooking recipes for beginners", {'file_path': '/3.txt', 'file_name': '3.txt', 'content_snippet': 'Cooking...'}),
        ]
        engine.add_documents_batch(documents)

        # 搜索
        results = engine.search("programming", top_k=2)

        assert len(results) > 0
        assert results[0].document_id in [1, 2]  # 应该返回编程相关文档
