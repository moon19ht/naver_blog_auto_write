"""Unit tests for Reporter module."""
import json
import pytest
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from adapters.report.reporter import Reporter, create_reporter
from adapters.secrets.credential_manager import CredentialManager
from core.models import BlogContent, BlogPostEntry, PostResult, BatchPostResult
from core.validation import ValidationResult, ValidationError


class TestReporter:
    """Tests for Reporter class."""

    @pytest.fixture
    def reporter(self):
        """Create a reporter instance."""
        return Reporter()

    @pytest.fixture
    def quiet_reporter(self):
        """Create a quiet reporter instance."""
        return Reporter(quiet=True)

    @pytest.fixture
    def sample_entry(self):
        """Create a sample blog post entry."""
        content = BlogContent(
            blog_title="Test Blog Post Title",
            blog_top_word="Introduction text",
            site_tag="tag1,tag2,tag3"
        )
        return BlogPostEntry(
            sns_id="test@naver.com",
            sns_pw="secret_password",
            sns_upload_cont=content,
            index=0
        )

    @pytest.fixture
    def sample_post_result(self, sample_entry):
        """Create a sample post result."""
        return PostResult(
            entry=sample_entry,
            success=True,
            error_message="",
            post_url="https://blog.naver.com/test/12345",
            timestamp="2024-01-15T10:30:00"
        )

    @pytest.fixture
    def sample_batch_result(self, sample_post_result):
        """Create a sample batch result."""
        result = BatchPostResult()
        result.add_result(sample_post_result)
        return result


class TestReporterJSONOutput:
    """Tests for Reporter JSON output schema compliance."""

    @pytest.fixture
    def reporter_with_output(self, tmp_path):
        """Create a reporter with JSON output file."""
        output_file = tmp_path / "report.json"
        return Reporter(output_file=str(output_file)), output_file

    def test_json_report_schema(self, reporter_with_output, tmp_path):
        """Test that JSON report follows expected schema."""
        reporter, output_file = reporter_with_output

        # Create test data
        content = BlogContent(blog_title="Test Post")
        entry = BlogPostEntry(
            sns_id="user@naver.com",
            sns_pw="password123",
            sns_upload_cont=content,
            index=0
        )
        post_result = PostResult(
            entry=entry,
            success=True,
            timestamp="2024-01-15T10:30:00"
        )
        batch_result = BatchPostResult()
        batch_result.add_result(post_result)

        reporter.start()
        reporter.report_batch_result(batch_result)

        # Verify JSON was written
        assert output_file.exists()

        # Parse and verify schema
        with open(output_file, 'r', encoding='utf-8') as f:
            report = json.load(f)

        # Check required top-level keys
        assert 'timestamp' in report
        assert 'summary' in report
        assert 'results' in report

        # Check summary schema
        summary = report['summary']
        assert 'total' in summary
        assert 'successful' in summary
        assert 'failed' in summary
        assert 'skipped' in summary

        # Check results schema
        assert isinstance(report['results'], list)
        if report['results']:
            result_item = report['results'][0]
            assert 'index' in result_item
            assert 'sns_id' in result_item
            assert 'blog_title' in result_item
            assert 'success' in result_item

    def test_json_report_duration(self, reporter_with_output):
        """Test that JSON report includes duration when start() was called."""
        reporter, output_file = reporter_with_output

        batch_result = BatchPostResult()
        reporter.start()
        reporter.report_batch_result(batch_result)

        with open(output_file, 'r', encoding='utf-8') as f:
            report = json.load(f)

        assert 'duration_seconds' in report
        assert report['duration_seconds'] is not None


class TestReporterPasswordMasking:
    """Tests for password masking across all output formats."""

    @pytest.fixture
    def entry_with_password(self):
        """Create entry with a known password."""
        content = BlogContent(blog_title="Test Post")
        return BlogPostEntry(
            sns_id="user@naver.com",
            sns_pw="my_secret_password",
            sns_upload_cont=content,
            index=0
        )

    def test_password_not_in_console_output(self, entry_with_password):
        """Test that password doesn't appear in console output."""
        reporter = Reporter()
        post_result = PostResult(
            entry=entry_with_password,
            success=True,
            timestamp="2024-01-15T10:30:00"
        )

        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_post_result(post_result)
            output = mock_stdout.getvalue()

        # Password should not appear in output
        assert "my_secret_password" not in output

    def test_password_not_in_json_report(self, entry_with_password, tmp_path):
        """Test that password doesn't appear in JSON report."""
        output_file = tmp_path / "report.json"
        reporter = Reporter(output_file=str(output_file))

        post_result = PostResult(
            entry=entry_with_password,
            success=True,
            timestamp="2024-01-15T10:30:00"
        )
        batch_result = BatchPostResult()
        batch_result.add_result(post_result)

        reporter.start()
        reporter.report_batch_result(batch_result)

        # Read the entire file as string to check for password
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "my_secret_password" not in content

    def test_password_not_in_dry_run_output(self, entry_with_password):
        """Test that password doesn't appear in dry-run output."""
        reporter = Reporter()
        credential_manager = CredentialManager()

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_dry_run([entry_with_password], credential_manager)
            output = mock_stdout.getvalue()

        assert "my_secret_password" not in output

    def test_password_not_in_doctor_output(self, entry_with_password):
        """Test that password doesn't appear in doctor output."""
        reporter = Reporter()
        credential_manager = CredentialManager()

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_doctor([entry_with_password], credential_manager, browser_ok=True)
            output = mock_stdout.getvalue()

        assert "my_secret_password" not in output


class TestReporterValidation:
    """Tests for validation report output."""

    def test_report_validation_valid(self):
        """Test validation report for valid result."""
        reporter = Reporter()
        result = ValidationResult()
        result.entries = [None, None]  # Mock entries

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_validation(result, "test.json")
            output = mock_stdout.getvalue()

        assert "VALID" in output
        assert "test.json" in output

    def test_report_validation_invalid(self):
        """Test validation report for invalid result."""
        reporter = Reporter()
        result = ValidationResult()
        result.add_error(ValidationError(
            index=0,
            path=".sns_id",
            field="sns_id",
            message="Required field missing"
        ))

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_validation(result, "test.json")
            output = mock_stdout.getvalue()

        assert "INVALID" in output
        assert "Required field missing" in output

    def test_report_validation_quiet_mode_valid(self):
        """Test that valid result produces no output in quiet mode."""
        reporter = Reporter(quiet=True)
        result = ValidationResult()
        result.entries = [None]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_validation(result, "test.json")
            output = mock_stdout.getvalue()

        assert output == ""

    def test_report_validation_quiet_mode_invalid(self):
        """Test that invalid result still shows output in quiet mode."""
        reporter = Reporter(quiet=True)
        result = ValidationResult()
        result.add_error(ValidationError(
            index=0,
            path=".test",
            field="test",
            message="Error"
        ))

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_validation(result, "test.json")
            output = mock_stdout.getvalue()

        assert "INVALID" in output


class TestReporterBatchResult:
    """Tests for batch result reporting."""

    def test_report_batch_result_success(self):
        """Test batch result report with successful posts."""
        reporter = Reporter()
        reporter.start()

        content = BlogContent(blog_title="Test Post")
        entry = BlogPostEntry(
            sns_id="user@naver.com",
            sns_pw="password",
            sns_upload_cont=content,
            index=0
        )
        batch_result = BatchPostResult()
        batch_result.add_result(PostResult(entry=entry, success=True, timestamp=""))

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_batch_result(batch_result)
            output = mock_stdout.getvalue()

        assert "Successful: 1" in output
        assert "Failed:     0" in output

    def test_report_batch_result_with_failures(self):
        """Test batch result report with failed posts."""
        reporter = Reporter()
        reporter.start()

        content = BlogContent(blog_title="Test Post")
        entry = BlogPostEntry(
            sns_id="user@naver.com",
            sns_pw="password",
            sns_upload_cont=content,
            index=0
        )
        batch_result = BatchPostResult()
        batch_result.add_result(PostResult(
            entry=entry,
            success=False,
            error_message="Login failed",
            timestamp=""
        ))

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            reporter.report_batch_result(batch_result)
            output = mock_stdout.getvalue()

        assert "Failed:     1" in output
        assert "Login failed" in output


class TestCreateReporter:
    """Tests for create_reporter factory function."""

    def test_create_reporter_default(self):
        """Test creating reporter with defaults."""
        reporter = create_reporter()
        assert reporter.output_file is None
        assert reporter.quiet is False

    def test_create_reporter_with_output(self, tmp_path):
        """Test creating reporter with output file."""
        output_file = tmp_path / "report.json"
        reporter = create_reporter(output_file=str(output_file))
        assert reporter.output_file == str(output_file)

    def test_create_reporter_quiet(self):
        """Test creating reporter in quiet mode."""
        reporter = create_reporter(quiet=True)
        assert reporter.quiet is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
