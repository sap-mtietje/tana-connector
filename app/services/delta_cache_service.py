"""Delta token cache service for MS Graph delta queries.

Delta queries allow syncing changes incrementally instead of fetching all data.
This service persists delta tokens to disk so sync state survives restarts.

## How Delta Queries Work

1. **Initial Request**: First call to a delta endpoint (e.g., /messages/delta)
   returns all current items plus a `@odata.deltaLink` URL.

2. **Subsequent Requests**: Use the deltaLink URL to get only items that
   changed since the last sync. MS Graph returns:
   - New items (created since last sync)
   - Modified items (updated since last sync)
   - Deleted items (marked with `@removed` property)
   - A new deltaLink for the next sync

3. **Pagination**: If there are many changes, MS Graph returns `@odata.nextLink`
   instead of deltaLink. Keep following nextLink until you get a deltaLink.

## Cache Strategy

- Delta tokens are stored as JSON files per folder (e.g., `inbox.json`)
- Each file contains: `{"delta_link": "...", "updated_at": "..."}`
- Tokens are folder-specific since each folder has its own sync state
- Cache is invalidated by deleting the file or calling `clear_token()`

## Usage Example

```python
# Get cached token (returns None on first sync)
token = delta_cache.get_token("inbox")

# After successful sync, save the new delta link
delta_cache.save_token("inbox", response.odata_delta_link)

# Clear cache to force full resync
delta_cache.clear_token("inbox")
```
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import DELTA_CACHE_DIR


class DeltaCacheService:
    """Manages persistent storage of delta tokens for incremental sync."""

    def __init__(self, cache_dir: Path = DELTA_CACHE_DIR):
        """
        Initialize the cache service.

        Args:
            cache_dir: Directory to store delta token files.
                       Defaults to configured DELTA_CACHE_DIR.
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, folder_id: str) -> Path:
        """Get the cache file path for a folder."""
        # Sanitize folder_id to be filesystem-safe
        safe_id = folder_id.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_id}.json"

    def get_token(self, folder_id: str) -> Optional[str]:
        """
        Retrieve cached delta token for a folder.

        Args:
            folder_id: Mail folder ID (e.g., 'inbox', 'sentitems')

        Returns:
            Delta link URL if cached, None otherwise
        """
        cache_path = self._get_cache_path(folder_id)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
                return data.get("delta_link")
        except (json.JSONDecodeError, IOError):
            # Corrupted cache file, treat as no cache
            return None

    def save_token(self, folder_id: str, delta_link: str) -> None:
        """
        Save delta token for a folder.

        Args:
            folder_id: Mail folder ID (e.g., 'inbox', 'sentitems')
            delta_link: The @odata.deltaLink URL from MS Graph response
        """
        cache_path = self._get_cache_path(folder_id)

        data = {
            "delta_link": delta_link,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "folder_id": folder_id,
        }

        with open(cache_path, "w") as f:
            json.dump(data, f, indent=2)

    def clear_token(self, folder_id: str) -> bool:
        """
        Clear cached delta token for a folder (forces full resync).

        Args:
            folder_id: Mail folder ID to clear

        Returns:
            True if cache was cleared, False if no cache existed
        """
        cache_path = self._get_cache_path(folder_id)

        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    def clear_all(self) -> int:
        """
        Clear all cached delta tokens.

        Returns:
            Number of cache files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count

    def get_cache_info(self, folder_id: str) -> Optional[dict]:
        """
        Get metadata about cached token (for debugging).

        Args:
            folder_id: Mail folder ID

        Returns:
            Dict with delta_link, updated_at, folder_id or None
        """
        cache_path = self._get_cache_path(folder_id)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
