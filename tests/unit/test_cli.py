"""Unit tests for CLI module."""
import json
import pytest
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.main import create_parser


class TestCLIParser:
    """Tests for CLI argument parser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return create_parser()

    def test_validate_command(self, parser):
        """Test validate command parsing."""
        args = parser.parse_args(['validate', 'input.json'])
        assert args.command == 'validate'
        assert args.input_file == 'input.json'

    def test_validate_command_quiet(self, parser):
        """Test validate command with quiet flag."""
        args = parser.parse_args(['validate', 'input.json', '--quiet'])
        assert args.quiet is True

    def test_post_command_all(self, parser):
        """Test post command with --all."""
        args = parser.parse_args(['post', 'input.json', '--all'])
        assert args.command == 'post'
        assert args.input_file == 'input.json'
        assert args.post_all is True

    def test_post_command_account_index(self, parser):
        """Test post command with --account-index."""
        args = parser.parse_args(['post', 'input.json', '--account-index', '2'])
        assert args.account_index == 2

    def test_post_command_filter_email(self, parser):
        """Test post command with --filter-email."""
        args = parser.parse_args(['post', 'input.json', '--filter-email', 'test@naver.com'])
        assert args.filter_email == 'test@naver.com'

    def test_post_command_dry_run(self, parser):
        """Test post command with --dry-run."""
        args = parser.parse_args(['post', 'input.json', '--all', '--dry-run'])
        assert args.dry_run is True

    def test_post_command_output_file(self, parser):
        """Test post command with --out."""
        args = parser.parse_args(['post', 'input.json', '--all', '--out', 'report.json'])
        assert args.out == 'report.json'

    def test_post_command_secrets_file(self, parser):
        """Test post command with --secrets-file."""
        args = parser.parse_args(['post', 'input.json', '--all', '--secrets-file', 'secrets.json'])
        assert args.secrets_file == 'secrets.json'

    def test_post_command_retries(self, parser):
        """Test post command with --retries."""
        args = parser.parse_args(['post', 'input.json', '--all', '--retries', '5'])
        assert args.retries == 5

    def test_post_command_headless_default(self, parser):
        """Test that headless defaults to True."""
        args = parser.parse_args(['post', 'input.json', '--all'])
        assert args.headless is True

    def test_post_command_no_headless(self, parser):
        """Test post command with --no-headless."""
        args = parser.parse_args(['post', 'input.json', '--all', '--no-headless'])
        assert args.headless is False

    def test_doctor_command(self, parser):
        """Test doctor command."""
        args = parser.parse_args(['doctor'])
        assert args.command == 'doctor'

    def test_doctor_command_with_file(self, parser):
        """Test doctor command with optional file."""
        args = parser.parse_args(['doctor', 'input.json'])
        assert args.command == 'doctor'
        assert args.input_file == 'input.json'

    def test_post_requires_selection(self, parser):
        """Test that post command requires selection option."""
        with pytest.raises(SystemExit):
            parser.parse_args(['post', 'input.json'])

    def test_post_selection_mutually_exclusive(self, parser):
        """Test that selection options are mutually exclusive."""
        with pytest.raises(SystemExit):
            parser.parse_args(['post', 'input.json', '--all', '--account-index', '0'])

    def test_no_command_shows_help(self, parser):
        """Test that no command returns None."""
        args = parser.parse_args([])
        assert args.command is None


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_validate_valid_file(self):
        """Test validate command with valid file."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_pw': 'password',
            'sns_upload_cont': {
                'blog_title': 'Test Post',
            }
        }]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            from cli.main import cmd_validate
            import argparse
            args = argparse.Namespace(input_file=temp_path, quiet=False)
            result = cmd_validate(args)
            assert result == 0
        finally:
            Path(temp_path).unlink()

    def test_validate_invalid_file(self):
        """Test validate command with invalid file."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_upload_cont': {}  # Missing blog_title
        }]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            from cli.main import cmd_validate
            import argparse
            args = argparse.Namespace(input_file=temp_path, quiet=False)
            result = cmd_validate(args)
            assert result == 1
        finally:
            Path(temp_path).unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
