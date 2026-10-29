"""Session-owned caches; no per-user mutation of LangChain process-global state."""
import hashlib
from pathlib import Path
from langchain_core.caches import InMemoryCache, BaseCache
from langchain_community.cache import SQLiteCache

class ObservedCache(BaseCache):
    """Delegate storage while recording real lookup hits for the UI."""
    def __init__(self, backend):
        self.backend = backend
        self.last_lookup_hit = False

    def lookup(self, prompt, llm_string):
        result = self.backend.lookup(prompt, llm_string)
        self.last_lookup_hit = result is not None
        return result

    def update(self, prompt, llm_string, return_val):
        self.backend.update(prompt, llm_string, return_val)

    def clear(self, **kwargs):
        self.backend.clear(**kwargs)
        self.last_lookup_hit = False

class CacheManager:
    def __init__(self, data_dir: Path, namespace: str):
        self.data_dir = Path(data_dir)
        # The secret namespace must never appear in filenames or prompts.
        self.namespace = hashlib.sha256(namespace.encode()).hexdigest()
        self.memory = ObservedCache(InMemoryCache())
        self.sqlite = None

    def get(self, mode: str):
        if mode == "Off":
            return False
        if mode == "Memory":
            return self.memory
        if mode != "SQLite":
            raise ValueError("Unknown cache mode")
        if self.sqlite is None:
            self.data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            path = self.data_dir / (self.namespace + ".db")
            self.sqlite = ObservedCache(SQLiteCache(database_path=str(path)))
            path.chmod(0o600)
        return self.sqlite

    def clear(self):
        self.memory.clear()
        if self.sqlite is not None:
            self.sqlite.clear()

    def destroy(self):
        """Best-effort cleanup of only this session's cache, used on sign-out."""
        self.memory.clear()
        if self.sqlite is not None:
            self.sqlite.clear()
            engine = getattr(self.sqlite.backend, "engine", None)
            if engine is not None:
                engine.dispose()
            self.sqlite = None
        for suffix in (".db", ".db-wal", ".db-shm", ".db-journal"):
            path = self.data_dir / (self.namespace + suffix)
            path.unlink(missing_ok=True)
