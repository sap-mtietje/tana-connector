"""Unit tests for DeltaCacheService"""

import json
import tempfile
from pathlib import Path

import pytest

from app.services.delta_cache_service import DeltaCacheService


class TestDeltaCacheService:
    """Tests for DeltaCacheService"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cache_service(self, temp_cache_dir):
        """Create a cache service with temp directory"""
        return DeltaCacheService(cache_dir=temp_cache_dir)

    def test_get_token_returns_none_when_no_cache(self, cache_service):
        """Test get_token returns None when no cache exists"""
        result = cache_service.get_token("inbox")
        assert result is None

    def test_save_and_get_token(self, cache_service):
        """Test saving and retrieving a delta token"""
        delta_link = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages/delta?$deltatoken=abc123"

        cache_service.save_token("inbox", delta_link)
        result = cache_service.get_token("inbox")

        assert result == delta_link

    def test_save_token_creates_file(self, cache_service, temp_cache_dir):
        """Test save_token creates a JSON file"""
        delta_link = "https://example.com/delta?token=xyz"

        cache_service.save_token("inbox", delta_link)

        cache_file = temp_cache_dir / "inbox.json"
        assert cache_file.exists()

        with open(cache_file) as f:
            data = json.load(f)
            assert data["delta_link"] == delta_link
            assert "updated_at" in data
            assert data["folder_id"] == "inbox"

    def test_clear_token_removes_cache(self, cache_service, temp_cache_dir):
        """Test clear_token removes the cache file"""
        cache_service.save_token("inbox", "https://example.com/delta")

        result = cache_service.clear_token("inbox")

        assert result is True
        assert not (temp_cache_dir / "inbox.json").exists()
        assert cache_service.get_token("inbox") is None

    def test_clear_token_returns_false_when_no_cache(self, cache_service):
        """Test clear_token returns False when no cache exists"""
        result = cache_service.clear_token("nonexistent")
        assert result is False

    def test_clear_all_removes_all_caches(self, cache_service, temp_cache_dir):
        """Test clear_all removes all cache files"""
        cache_service.save_token("inbox", "https://example.com/inbox")
        cache_service.save_token("sent", "https://example.com/sent")
        cache_service.save_token("drafts", "https://example.com/drafts")

        count = cache_service.clear_all()

        assert count == 3
        assert cache_service.get_token("inbox") is None
        assert cache_service.get_token("sent") is None
        assert cache_service.get_token("drafts") is None

    def test_get_cache_info_returns_metadata(self, cache_service):
        """Test get_cache_info returns full metadata"""
        delta_link = "https://example.com/delta?token=xyz"
        cache_service.save_token("inbox", delta_link)

        info = cache_service.get_cache_info("inbox")

        assert info is not None
        assert info["delta_link"] == delta_link
        assert info["folder_id"] == "inbox"
        assert "updated_at" in info

    def test_get_cache_info_returns_none_when_no_cache(self, cache_service):
        """Test get_cache_info returns None when no cache exists"""
        info = cache_service.get_cache_info("nonexistent")
        assert info is None

    def test_folder_id_sanitization(self, cache_service, temp_cache_dir):
        """Test folder IDs with special characters are sanitized"""
        # Folder IDs with slashes should be sanitized
        cache_service.save_token("folder/with/slashes", "https://example.com/delta")

        # Should create a file with sanitized name
        cache_file = temp_cache_dir / "folder_with_slashes.json"
        assert cache_file.exists()

        # Should be retrievable with original ID
        result = cache_service.get_token("folder/with/slashes")
        assert result == "https://example.com/delta"

    def test_corrupted_cache_file_returns_none(self, cache_service, temp_cache_dir):
        """Test corrupted cache file is handled gracefully"""
        cache_file = temp_cache_dir / "inbox.json"
        cache_file.write_text("not valid json {{{")

        result = cache_service.get_token("inbox")
        assert result is None

    def test_multiple_folders_independent(self, cache_service):
        """Test multiple folders have independent caches"""
        cache_service.save_token("inbox", "https://example.com/inbox")
        cache_service.save_token("sent", "https://example.com/sent")

        assert cache_service.get_token("inbox") == "https://example.com/inbox"
        assert cache_service.get_token("sent") == "https://example.com/sent"

        # Clearing one doesn't affect the other
        cache_service.clear_token("inbox")
        assert cache_service.get_token("inbox") is None
        assert cache_service.get_token("sent") == "https://example.com/sent"

    def test_overwrite_existing_token(self, cache_service):
        """Test saving a new token overwrites the old one"""
        cache_service.save_token("inbox", "https://example.com/old")
        cache_service.save_token("inbox", "https://example.com/new")

        result = cache_service.get_token("inbox")
        assert result == "https://example.com/new"
