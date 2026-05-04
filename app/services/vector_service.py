import os
import hashlib
import json
import google.generativeai as genai
from app.models import Item
from app.extensions import db, cache
from sqlalchemy import text
from app.utils.resilience import ai_circuit_breaker, retry, CircuitBreakerOpenException

class VectorService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = "models/gemini-embedding-001"
        else:
            self.model = None
    #إدارة "النسخ الاحتياطية" للكاش
    def _get_search_namespace(self) -> str:
        """Get the current cache namespace version for search."""
        try:
            ns = cache.get("vec:search_ns")
            if not ns:
                ns = "1"
                cache.set("vec:search_ns", ns, timeout=None)
            return ns
        except Exception:
            return "1"

    def invalidate_search_cache(self):
        """Invalidates all semantic search caches by incrementing the namespace."""
        try:
            current_ns = int(self._get_search_namespace())
            cache.set("vec:search_ns", str(current_ns + 1), timeout=None)
        except Exception:
            pass

    def _cache_key(self, prefix: str, text_content: str) -> str:
        """Generate a stable cache key from text content."""
        h = hashlib.sha256(text_content.encode("utf-8")).hexdigest()[:16]
        if prefix == "search":
            ns = self._get_search_namespace()
            return f"vec:{prefix}:v{ns}:{h}"
        return f"vec:{prefix}:{h}"

    @ai_circuit_breaker
    @retry(max_attempts=3, delay=1.0, backoff=2.0)
    def _call_gemini_api(self, text_content: str):
        """Wrapped API call with Circuit Breaker and Retry."""
        # Note: request_options is only supported in google-generativeai>=0.5
        # We use a compatible call that works across versions
        result = genai.embed_content(
            model=self.model,
            content=text_content,
            task_type="retrieval_document",
        )
        return result["embedding"]

    def generate_embedding(self, text_content: str):
        """
        Generate a 768-dimensional vector for the given text.
        Results are cached for 24 hours to avoid redundant API calls.
        Includes Graceful Degradation.
        """
        if not self.model or not text_content:
            return None

        # ── Cache check ───────────────────────────────────────────────────────
        cache_key = self._cache_key("emb", text_content)
        try:
            cached = cache.get(cache_key)
            if cached is not None:
                return json.loads(cached)
        except Exception:
            pass  # Cache unavailable — continue without it

        # ── API call with Resilience ──────────────────────────────────────────
        try:
            embedding = self._call_gemini_api(text_content)

            # Cache for 24 hours
            try:
                cache.set(cache_key, json.dumps(embedding), timeout=86400)
            except Exception:
                pass

            return embedding
        except CircuitBreakerOpenException:
            import logging
            logging.getLogger(__name__).critical("AI Circuit Breaker is OPEN. Fallback to cached/degraded state.")
            return None
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Embedding Error after retries: {e}")
            return None

    def semantic_search(self, query: str, limit: int = 5) -> list:
        """
        Find items most semantically similar to the query.
        Full search results are cached for 1 hour per unique query+limit combo.
        """
        # ── Cache check for full search result ───────────────────────────────
        search_cache_key = self._cache_key("search", f"{query}:{limit}")
        try:
            cached_ids = cache.get(search_cache_key)
            if cached_ids is not None:
                item_ids = json.loads(cached_ids)
                if item_ids:
                    return Item.query.filter(Item.id.in_(item_ids)).all()
        except Exception:
            pass

        # ── Generate query embedding (also cached internally) ─────────────────
        query_vector = self.generate_embedding(query)
        if not query_vector:
            return []

        vector_str = "[" + ",".join(map(str, query_vector)) + "]"

        try:
            rows = db.session.execute(
                text(
                    "SELECT id FROM items "
                    "WHERE embedding IS NOT NULL "
                    "ORDER BY embedding <=> :vec "
                    "LIMIT :limit"
                ),
                {"vec": vector_str, "limit": limit},
            ).fetchall()

            item_ids = [r[0] for r in rows]

            # Cache search results for 1 hour
            try:
                cache.set(search_cache_key, json.dumps(item_ids), timeout=3600)
            except Exception:
                pass

            return Item.query.filter(Item.id.in_(item_ids)).all() if item_ids else []

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Semantic search error: {e}")
            return []

    def sync_all_items(self, batch_size: int = 100):
        """
        Batch-process all items to generate and store embeddings.
        Uses LIMIT/OFFSET batching to avoid loading the entire table into
        memory at once — safe for large catalogs.
        """
        count  = 0
        offset = 0

        while True:
            # Fetch one batch — no .all() on the full table
            batch = Item.query.order_by(Item.id).limit(batch_size).offset(offset).all()
            if not batch:
                break  # No more rows

            for item in batch:
                content = (
                    f"Name: {item.name}. "
                    f"Brand: {item.brand.name if item.brand else ''}. "
                    f"Description: {item.description or ''}. "
                    f"Notes: {item.normalized_notes or ''}"
                )
                vector = self.generate_embedding(content)
                if vector:
                    vector_str = "[" + ",".join(map(str, vector)) + "]"
                    db.session.execute(
                        text("UPDATE items SET embedding = :vec WHERE id = :id"),
                        {"vec": vector_str, "id": item.id},
                    )
                    count += 1

            # Commit each batch independently to avoid a single giant transaction
            db.session.commit()
            offset += batch_size

        return count


vector_service = VectorService()
