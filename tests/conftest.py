"""
Pytest configuration and fixtures for memorygraph tests.
"""

import sys
from contextlib import contextmanager

import pytest

import memorygraph.config as _config_module
from memorygraph.config import Config

# Save the original Config class reference. Tests that call
# reload(memorygraph.config) create a NEW Config class in the module,
# which disconnects it from the one we (and backend modules) imported.
_ORIGINAL_CONFIG_CLASS = Config

# Store original Config descriptor objects (not resolved values) at module load time.
# Config.__dict__ returns the raw _EnvVar descriptors before they're invoked.
# Uses duck typing (hasattr 'is_set') to auto-detect _EnvVar descriptors,
# matching the pattern in Config.is_env_set() and avoiding a fragile hardcoded list.
_ORIGINAL_CONFIG = {
    key: value
    for key, value in Config.__dict__.items()
    if hasattr(value, "is_set")
}

# Backend modules whose module-level 'Config' reference may be replaced by
# reload(). Does NOT include memorygraph.config or src.memorygraph.config --
# those are handled separately because src.memorygraph.config.Config is a
# legitimately different class from _ORIGINAL_CONFIG_CLASS.
_BACKEND_MODULES = [
    "memorygraph.backends.sqlite_fallback",
    "memorygraph.backends.neo4j_backend",
    "memorygraph.backends.memgraph_backend",
    "memorygraph.backends.turso",
    "memorygraph.backends.cloud_backend",
    "memorygraph.backends.falkordb_backend",
    "memorygraph.backends.falkordblite_backend",
    "memorygraph.backends.ladybugdb_backend",
    "memorygraph.backends.factory",
]


@pytest.fixture(autouse=True)
def reset_config():
    """Reset Config class attributes to their original descriptors after each test.

    This prevents test pollution where one test modifies Config.BACKEND
    and subsequent tests see the modified value instead of the dynamic
    _EnvVar descriptor.

    Also restores module-level Config references that may have been replaced
    by reload(memorygraph.config) in tests. When a module is reloaded, a new
    Config class is created. Backend modules that are also reloaded will then
    reference this new class via their module globals, causing patch_config
    (which patches the original class) to have no effect on them.
    """
    yield

    # Restore the original Config class in the memorygraph.config module.
    # reload() replaces it with a new class; we need the original back.
    _config_module.Config = _ORIGINAL_CONFIG_CLASS

    # Restore Config reference in backend modules whose module-level 'Config'
    # was replaced by a reload.
    for mod_name in _BACKEND_MODULES:
        mod = sys.modules.get(mod_name)
        if mod is None:
            continue
        mod_config = mod.__dict__.get("Config")
        if mod_config is not None and mod_config is not _ORIGINAL_CONFIG_CLASS:
            mod.Config = _ORIGINAL_CONFIG_CLASS

    # Restore original descriptors on the Config class
    for key, descriptor in _ORIGINAL_CONFIG.items():
        setattr(_ORIGINAL_CONFIG_CLASS, key, descriptor)


def _get_all_config_classes():
    """Return all loaded Config class objects (handles src. and non-src. import paths)."""
    classes = [Config]
    src_mod = sys.modules.get("src.memorygraph.config")
    if src_mod is not None:
        src_config = getattr(src_mod, "Config", None)
        if src_config is not None and src_config is not Config:
            classes.append(src_config)
    return classes


@contextmanager
def patch_config(**kwargs):
    """Context manager to temporarily patch Config class attributes.

    Saves raw class dict entries (including _EnvVar descriptors) so that
    dynamic env var resolution is restored on exit.  Keys that did not
    previously exist in ``Config.__dict__`` are deleted on exit so they
    don't leak into subsequent tests.

    Patches all loaded Config classes (both ``memorygraph.config.Config``
    and ``src.memorygraph.config.Config``) to avoid divergence when test
    files mix import paths.

    Usage:
        with patch_config(NEO4J_URI="bolt://test:7687", NEO4J_PASSWORD="test"):
            backend = Neo4jBackend()
            assert backend.uri == "bolt://test:7687"

    Args:
        **kwargs: Config attributes to patch (e.g., NEO4J_URI="value")
    """
    configs = _get_all_config_classes()
    saved = []  # list of (cls, key, original_descriptor) tuples
    new_keys = []  # list of (cls, key) for attrs that didn't exist before

    for cfg in configs:
        for key, value in kwargs.items():
            if key in cfg.__dict__:
                saved.append((cfg, key, cfg.__dict__[key]))
            else:
                new_keys.append((cfg, key))
            setattr(cfg, key, value)

    try:
        yield
    finally:
        for cfg, key, original in saved:
            setattr(cfg, key, original)
        for cfg, key in new_keys:
            try:
                delattr(cfg, key)
            except AttributeError:
                pass
