"""
Tests verifying that backend modules are importable.

Validates that all backend modules can be imported as top-level attributes
of the memorygraph.backends package, matching the command:
    python -c "from memorygraph.backends import factory, neo4j_backend, memgraph_backend, cloud_backend, falkordb_backend"
"""

import importlib
import types

# The five modules the task command imports directly
_REQUIRED_MODULES = [
    "factory",
    "neo4j_backend",
    "memgraph_backend",
    "cloud_backend",
    "falkordb_backend",
]

# All backend modules that should be importable
_ALL_BACKEND_MODULES = [
    "base",
    "factory",
    "neo4j_backend",
    "memgraph_backend",
    "cloud_backend",
    "falkordb_backend",
    "falkordblite_backend",
    "sqlite_fallback",
    "turso",
    "ladybugdb_backend",
    "_falkordb_shared",
]


class TestBackendModuleImports:
    """Test that backend modules are importable from memorygraph.backends."""

    def test_import_factory(self):
        """Verify factory module is importable."""
        from memorygraph.backends import factory

        assert isinstance(factory, types.ModuleType)

    def test_import_neo4j_backend(self):
        """Verify neo4j_backend module is importable."""
        from memorygraph.backends import neo4j_backend

        assert isinstance(neo4j_backend, types.ModuleType)

    def test_import_memgraph_backend(self):
        """Verify memgraph_backend module is importable."""
        from memorygraph.backends import memgraph_backend

        assert isinstance(memgraph_backend, types.ModuleType)

    def test_import_cloud_backend(self):
        """Verify cloud_backend module is importable."""
        from memorygraph.backends import cloud_backend

        assert isinstance(cloud_backend, types.ModuleType)

    def test_import_falkordb_backend(self):
        """Verify falkordb_backend module is importable."""
        from memorygraph.backends import falkordb_backend

        assert isinstance(falkordb_backend, types.ModuleType)

    def test_import_all_required_modules_together(self):
        """Verify all five required modules import in a single statement."""
        from memorygraph.backends import (
            cloud_backend,
            factory,
            falkordb_backend,
            memgraph_backend,
            neo4j_backend,
        )

        for mod in (factory, neo4j_backend, memgraph_backend, cloud_backend, falkordb_backend):
            assert isinstance(mod, types.ModuleType)

    def test_importlib_import_module(self):
        """Verify all backend modules are importable via importlib."""
        for name in _ALL_BACKEND_MODULES:
            mod = importlib.import_module(f"memorygraph.backends.{name}")
            assert isinstance(mod, types.ModuleType), f"Failed to import memorygraph.backends.{name}"


class TestBackendModuleContents:
    """Test that imported backend modules expose expected classes."""

    def test_factory_has_backend_factory_class(self):
        """Factory module should export BackendFactory."""
        from memorygraph.backends.factory import BackendFactory

        assert hasattr(BackendFactory, "create_backend")

    def test_neo4j_backend_has_class(self):
        """neo4j_backend module should export Neo4jBackend."""
        from memorygraph.backends.neo4j_backend import Neo4jBackend

        assert Neo4jBackend is not None

    def test_memgraph_backend_has_class(self):
        """memgraph_backend module should export MemgraphBackend."""
        from memorygraph.backends.memgraph_backend import MemgraphBackend

        assert MemgraphBackend is not None

    def test_cloud_backend_has_class(self):
        """cloud_backend module should export CloudRESTAdapter."""
        from memorygraph.backends.cloud_backend import CloudRESTAdapter

        assert CloudRESTAdapter is not None

    def test_falkordb_backend_has_class(self):
        """falkordb_backend module should export FalkorDBBackend."""
        from memorygraph.backends.falkordb_backend import FalkorDBBackend

        assert FalkorDBBackend is not None

    def test_base_has_graph_backend(self):
        """base module should export GraphBackend."""
        from memorygraph.backends.base import GraphBackend

        assert GraphBackend is not None

    def test_init_exports_graph_backend_and_factory(self):
        """Package __init__ should export GraphBackend and BackendFactory."""
        from memorygraph.backends import BackendFactory, GraphBackend

        assert GraphBackend is not None
        assert BackendFactory is not None


# Backend modules that had `import os` removed after WP33 config migration
_OS_REMOVED_MODULES = [
    "factory",
    "neo4j_backend",
    "memgraph_backend",
    "cloud_backend",
    "falkordb_backend",
]

# Backend modules that still legitimately use `os`
_OS_REQUIRED_MODULES = [
    "sqlite_fallback",
]


class TestNoUnusedOsImport:
    """Verify that os is not imported in backend files that don't need it.

    After the WP33 config migration to _EnvVar descriptors, these 5 backend
    files no longer reference os.environ / os.getenv / os.path directly.
    """

    def test_os_not_in_cleaned_modules(self):
        """The 5 migrated backend modules should not have 'os' in their namespace."""
        for name in _OS_REMOVED_MODULES:
            mod = importlib.import_module(f"memorygraph.backends.{name}")
            assert "os" not in vars(mod), (
                f"memorygraph.backends.{name} still imports 'os' — "
                "it should have been removed after config migration"
            )

    def test_os_present_in_modules_that_need_it(self):
        """sqlite_fallback and turso still use os and should import it."""
        for name in _OS_REQUIRED_MODULES:
            mod = importlib.import_module(f"memorygraph.backends.{name}")
            assert "os" in vars(mod), (
                f"memorygraph.backends.{name} should import 'os' — "
                "it uses os.path.expanduser / os.path.getsize"
            )
