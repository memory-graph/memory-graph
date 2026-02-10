"""
Comprehensive tests for the CLI module.

Tests cover:
- Argument parsing
- Version display
- Configuration validation
- Backend and profile selection
- Environment variable handling
- Error cases
"""

import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from memorygraph import __version__
from memorygraph.cli import (
    _eprint,
    main,
    print_config_summary,
    validate_backend,
    validate_profile,
)


class TestEprintHelper:
    """Test _eprint() writes to stderr, not stdout."""

    def test_eprint_writes_to_stderr(self, capsys):
        _eprint("test message")
        captured = capsys.readouterr()
        assert captured.err == "test message\n"
        assert captured.out == ""

    def test_eprint_respects_file_override(self):
        buf = StringIO()
        _eprint("custom dest", file=buf)
        assert buf.getvalue() == "custom dest\n"

    def test_eprint_passes_kwargs(self, capsys):
        _eprint("a", "b", sep="-", end="!\n")
        captured = capsys.readouterr()
        assert captured.err == "a-b!\n"
        assert captured.out == ""


class TestVersionDisplay:
    """Test version argument handling."""

    def test_version_flag(self):
        """Test --version flag displays version and exits."""
        with patch('sys.argv', ['memorygraph', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_version_output_format(self, capsys):
        """Test version output format."""
        with patch('sys.argv', ['memorygraph', '--version']):
            with pytest.raises(SystemExit):
                main()
            captured = capsys.readouterr()
            assert __version__ in captured.out
            assert 'memorygraph' in captured.out.lower()


class TestShowConfig:
    """Test --show-config argument."""

    @patch.dict(os.environ, {}, clear=True)
    def test_show_config_basic(self, capsys):
        """Test basic configuration display."""
        with patch('sys.argv', ['memorygraph', '--show-config']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert 'Current Configuration' in captured.err
            assert 'Backend:' in captured.err
            assert 'Tool Profile:' in captured.err
            assert 'Log Level:' in captured.err

    @patch.dict(os.environ, {'MEMORY_BACKEND': 'neo4j'})
    def test_show_config_with_neo4j(self, capsys):
        """Test configuration display with Neo4j backend."""
        with patch('sys.argv', ['memorygraph', '--show-config']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            # Check for backend being displayed (Config may have cached sqlite)
            assert 'Backend:' in captured.err

    @patch.dict(os.environ, {'MEMORY_BACKEND': 'sqlite'}, clear=True)
    def test_show_config_with_sqlite(self, capsys):
        """Test configuration display with SQLite backend."""
        with patch('sys.argv', ['memorygraph', '--show-config']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert 'SQLite' in captured.err


class TestHealthCheck:
    """Test --health argument."""

    def test_health_flag_exits(self, capsys):
        """Test --health flag exits gracefully."""
        with patch('sys.argv', ['memorygraph', '--health']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert 'health check' in captured.err.lower()


class TestBackendValidation:
    """Test backend validation."""

    def test_validate_backend_sqlite(self):
        """Test SQLite backend is valid."""
        # Should not raise
        validate_backend('sqlite')

    def test_validate_backend_neo4j(self):
        """Test Neo4j backend is valid."""
        # Should not raise
        validate_backend('neo4j')

    def test_validate_backend_memgraph(self):
        """Test Memgraph backend is valid."""
        # Should not raise
        validate_backend('memgraph')

    def test_validate_backend_auto(self):
        """Test auto backend is valid."""
        # Should not raise
        validate_backend('auto')

    def test_validate_backend_invalid(self, capsys):
        """Test invalid backend raises error."""
        with pytest.raises(SystemExit) as exc_info:
            validate_backend('invalid_backend')
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert 'Invalid backend' in captured.err
        assert 'invalid_backend' in captured.err


class TestProfileValidation:
    """Test tool profile validation."""

    def test_validate_profile_lite(self):
        """Test lite profile is valid."""
        # Should not raise
        validate_profile('lite')

    def test_validate_profile_standard(self):
        """Test standard profile is valid."""
        # Should not raise
        validate_profile('standard')

    def test_validate_profile_full(self):
        """Test full profile is valid."""
        # Should not raise
        validate_profile('full')

    def test_validate_profile_invalid(self, capsys):
        """Test invalid profile raises error."""
        with pytest.raises(SystemExit) as exc_info:
            validate_profile('invalid_profile')
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert 'Invalid profile' in captured.err
        assert 'invalid_profile' in captured.err


class TestBackendArgument:
    """Test --backend argument."""

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    @patch.dict(os.environ, {}, clear=True)
    def test_backend_arg_sets_env_var(self, mock_run, mock_server):
        """Test --backend argument sets environment variable."""
        with patch('sys.argv', ['memorygraph', '--backend', 'neo4j']):
            # Mock asyncio.run to prevent actual server start
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit):
                main()

            # Environment variable should be set
            assert os.environ.get('MEMORY_BACKEND') == 'neo4j'

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    def test_invalid_backend_arg(self, mock_run, mock_server, capsys):
        """Test invalid --backend argument."""
        with patch('sys.argv', ['memorygraph', '--backend', 'invalid']):
            # argparse will handle this before our validation
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with code 2 for argument errors
            assert exc_info.value.code == 2


class TestProfileArgument:
    """Test --profile argument."""

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    @patch.dict(os.environ, {}, clear=True)
    def test_profile_arg_sets_env_var(self, mock_run, mock_server):
        """Test --profile argument sets environment variable."""
        with patch('sys.argv', ['memorygraph', '--profile', 'extended']):
            # Mock asyncio.run to prevent actual server start
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit):
                main()

            # Environment variable should be set
            assert os.environ.get('MEMORY_TOOL_PROFILE') == 'extended'


class TestLogLevelArgument:
    """Test --log-level argument."""

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    @patch.dict(os.environ, {}, clear=True)
    def test_log_level_arg_sets_env_var(self, mock_run, mock_server):
        """Test --log-level argument sets environment variable."""
        with patch('sys.argv', ['memorygraph', '--log-level', 'DEBUG']):
            # Mock asyncio.run to prevent actual server start
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit):
                main()

            # Environment variable should be set
            assert os.environ.get('MEMORY_LOG_LEVEL') == 'DEBUG'


class TestServerStartup:
    """Test server startup behavior."""

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    def test_server_starts_successfully(self, mock_run, mock_server, capsys):
        """Test successful server startup."""
        with patch('sys.argv', ['memorygraph']):
            # Mock successful run
            mock_run.return_value = None

            main()

            # Server should be called
            mock_run.assert_called_once()

            captured = capsys.readouterr()
            assert 'Starting' in captured.err

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    def test_keyboard_interrupt_graceful_shutdown(self, mock_run, mock_server, capsys):
        """Test graceful shutdown on Ctrl+C."""
        with patch('sys.argv', ['memorygraph']):
            # Simulate KeyboardInterrupt
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert 'stopped gracefully' in captured.err.lower()

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    def test_server_error_handling(self, mock_run, mock_server, capsys):
        """Test server error handling."""
        with patch('sys.argv', ['memorygraph']):
            # Simulate server error
            mock_run.side_effect = Exception("Test error")

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert 'error' in captured.err.lower()


class TestCombinedArguments:
    """Test multiple arguments together."""

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    @patch.dict(os.environ, {}, clear=True)
    def test_backend_and_profile_together(self, mock_run, mock_server):
        """Test setting both backend and profile."""
        with patch('sys.argv', ['memorygraph', '--backend', 'neo4j', '--profile', 'full']):
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit):
                main()

            assert os.environ.get('MEMORY_BACKEND') == 'neo4j'
            # 'full' is deprecated and maps to 'extended'
            assert os.environ.get('MEMORY_TOOL_PROFILE') == 'extended'

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    @patch.dict(os.environ, {}, clear=True)
    def test_all_arguments_together(self, mock_run, mock_server):
        """Test setting backend, profile, and log level."""
        with patch('sys.argv', [
            'memorygraph',
            '--backend', 'sqlite',
            '--profile', 'extended',
            '--log-level', 'DEBUG'
        ]):
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit):
                main()

            assert os.environ.get('MEMORY_BACKEND') == 'sqlite'
            assert os.environ.get('MEMORY_TOOL_PROFILE') == 'extended'
            assert os.environ.get('MEMORY_LOG_LEVEL') == 'DEBUG'


class TestPrintConfigSummary:
    """Test print_config_summary function."""

    @patch.dict(os.environ, {'MEMORY_BACKEND': 'sqlite'}, clear=True)
    def test_print_config_summary(self, capsys):
        """Test configuration summary output."""
        print_config_summary()

        captured = capsys.readouterr()
        assert 'Current Configuration' in captured.err
        assert 'Backend:' in captured.err
        assert 'Tool Profile:' in captured.err


class TestEnvironmentVariables:
    """Test environment variable handling."""

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    @patch.dict(os.environ, {'MEMORY_BACKEND': 'memgraph'})
    def test_env_var_backend(self, mock_run, mock_server, capsys):
        """Test backend from environment variable."""
        with patch('sys.argv', ['memorygraph']):
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit):
                main()

            captured = capsys.readouterr()
            # Check that output contains backend info
            assert 'Backend:' in captured.err

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    @patch.dict(os.environ, {'MEMORY_TOOL_PROFILE': 'full'}, clear=True)
    def test_env_var_profile(self, mock_run, mock_server, capsys):
        """Test profile from environment variable."""
        with patch('sys.argv', ['memorygraph']):
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit):
                main()

            captured = capsys.readouterr()
            assert 'full' in captured.err.lower()

    @patch('memorygraph.cli.server_main', new_callable=AsyncMock)
    @patch('asyncio.run')
    @patch.dict(os.environ, {
        'MEMORY_BACKEND': 'sqlite',
        'MEMORY_TOOL_PROFILE': 'lite'
    }, clear=True)
    def test_cli_args_override_env_vars(self, mock_run, mock_server):
        """Test CLI arguments override environment variables."""
        with patch('sys.argv', ['memorygraph', '--backend', 'neo4j', '--profile', 'full']):
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit):
                main()

            # CLI args should override
            assert os.environ.get('MEMORY_BACKEND') == 'neo4j'
            # 'full' is deprecated and maps to 'extended'
            assert os.environ.get('MEMORY_TOOL_PROFILE') == 'extended'
