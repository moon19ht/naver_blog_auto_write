"""Unit tests for JSON validation."""
import json
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.validation import JSONValidator, validate_json_file, ValidationResult


class TestJSONValidator:
    """Tests for JSONValidator."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return JSONValidator()

    def test_validate_valid_entry(self, validator):
        """Test validating a valid entry."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_pw': 'password',
            'sns_upload_cont': {
                'blog_title': 'Test Post',
            }
        }]
        result = validator.validate_data(data)
        assert result.valid
        assert len(result.entries) == 1

    def test_validate_missing_sns_id(self, validator):
        """Test validation fails without sns_id."""
        data = [{
            'sns_pw': 'password',
            'sns_upload_cont': {
                'blog_title': 'Test Post',
            }
        }]
        result = validator.validate_data(data)
        assert not result.valid
        assert any('sns_id' in e.field for e in result.errors)

    def test_validate_missing_blog_title(self, validator):
        """Test validation fails without blog_title."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_pw': 'password',
            'sns_upload_cont': {}
        }]
        result = validator.validate_data(data)
        assert not result.valid
        assert any('blog_title' in e.field for e in result.errors)

    def test_validate_empty_blog_title(self, validator):
        """Test validation fails with empty blog_title."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_pw': 'password',
            'sns_upload_cont': {
                'blog_title': '',
            }
        }]
        result = validator.validate_data(data)
        assert not result.valid

    def test_validate_missing_password_warning(self, validator):
        """Test that missing password generates warning."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_upload_cont': {
                'blog_title': 'Test Post',
            }
        }]
        result = validator.validate_data(data)
        # Valid but with warning
        assert result.valid
        assert len(result.warnings) > 0
        assert any('sns_pw' in w.field for w in result.warnings)

    def test_validate_invalid_url_warning(self, validator):
        """Test that invalid URL generates warning."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_pw': 'password',
            'sns_upload_cont': {
                'blog_title': 'Test Post',
                'blog_title_img': 'not-a-url',
            }
        }]
        result = validator.validate_data(data)
        assert result.valid  # Still valid, just warning
        assert any('blog_title_img' in w.field for w in result.warnings)

    def test_validate_valid_url(self, validator):
        """Test that valid URLs pass."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_pw': 'password',
            'sns_upload_cont': {
                'blog_title': 'Test Post',
                'blog_title_img': 'https://example.com/image.jpg',
            }
        }]
        result = validator.validate_data(data)
        assert result.valid
        assert not any('blog_title_img' in w.field for w in result.warnings)

    def test_validate_trailing_comma_tags_warning(self, validator):
        """Test that trailing comma in tags generates warning."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_pw': 'password',
            'sns_upload_cont': {
                'blog_title': 'Test Post',
                'site_tag': 'tag1,tag2,',
            }
        }]
        result = validator.validate_data(data)
        assert result.valid
        assert any('site_tag' in w.field for w in result.warnings)

    def test_validate_empty_array(self, validator):
        """Test that empty array fails validation."""
        result = validator.validate_data([])
        assert not result.valid
        assert any('empty' in e.message.lower() for e in result.errors)

    def test_validate_not_array(self, validator):
        """Test that non-array fails validation."""
        result = validator.validate_data({'sns_id': 'test'})
        assert not result.valid
        assert any('array' in e.message.lower() for e in result.errors)

    def test_validate_multiple_entries(self, validator):
        """Test validating multiple entries."""
        data = [
            {
                'sns_id': 'user1@naver.com',
                'sns_pw': 'pass1',
                'sns_upload_cont': {'blog_title': 'Post 1'}
            },
            {
                'sns_id': 'user2@naver.com',
                'sns_pw': 'pass2',
                'sns_upload_cont': {'blog_title': 'Post 2'}
            },
        ]
        result = validator.validate_data(data)
        assert result.valid
        assert len(result.entries) == 2

    def test_error_path_format(self, validator):
        """Test that error path is correctly formatted."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_pw': 'password',
            'sns_upload_cont': {}
        }]
        result = validator.validate_data(data)
        assert not result.valid
        # Should have path like ".sns_upload_cont.blog_title"
        assert any('.sns_upload_cont.blog_title' in e.path for e in result.errors)


class TestValidateFile:
    """Tests for file validation."""

    def test_validate_file_not_found(self):
        """Test validation with non-existent file."""
        result = validate_json_file('/nonexistent/file.json')
        assert not result.valid
        assert any('not found' in e.message.lower() for e in result.errors)

    def test_validate_invalid_json(self, tmp_path):
        """Test validation with invalid JSON."""
        temp_file = tmp_path / "invalid.json"
        temp_file.write_text('{invalid json', encoding='utf-8')

        result = validate_json_file(str(temp_file))
        assert not result.valid
        assert any('syntax' in e.message.lower() for e in result.errors)

    def test_validate_valid_file(self, tmp_path):
        """Test validation with valid JSON file."""
        data = [{
            'sns_id': 'test@naver.com',
            'sns_pw': 'password',
            'sns_upload_cont': {
                'blog_title': 'Test Post',
            }
        }]

        temp_file = tmp_path / "valid.json"
        temp_file.write_text(json.dumps(data), encoding='utf-8')

        result = validate_json_file(str(temp_file))
        assert result.valid
        assert len(result.entries) == 1


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_get_summary_valid(self):
        """Test summary for valid result."""
        result = ValidationResult()
        result.entries = [None, None, None]  # Mock entries
        summary = result.get_summary()
        assert 'passed' in summary.lower()
        assert '3' in summary

    def test_get_summary_invalid(self):
        """Test summary for invalid result."""
        result = ValidationResult()
        from core.validation import ValidationError
        result.add_error(ValidationError(
            index=0, path='.test', field='test', message='Test error'
        ))
        summary = result.get_summary()
        assert 'failed' in summary.lower()

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ValidationResult()
        d = result.to_dict()
        assert 'valid' in d
        assert 'error_count' in d
        assert 'warning_count' in d


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
