"""
JSON validation module for blog post input files.

Validates the fixed JSON schema and provides detailed error reporting.
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from core.models import BlogPostEntry, BlogContent


@dataclass
class ValidationError:
    """Single validation error with path information."""
    index: int  # Position in JSON array
    path: str  # JSON path like "[2].sns_upload_cont.blog_title"
    field: str  # Field name
    message: str  # Error description
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        return f"[{self.index}]{self.path}: {self.message}"

    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'path': self.path,
            'field': self.field,
            'message': self.message,
            'severity': self.severity,
        }


@dataclass
class ValidationResult:
    """Result of JSON validation."""
    valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    entries: List[BlogPostEntry] = field(default_factory=list)

    def add_error(self, error: ValidationError):
        """Add an error and mark as invalid."""
        self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: ValidationError):
        """Add a warning (doesn't affect validity)."""
        warning.severity = "warning"
        self.warnings.append(warning)

    def to_dict(self) -> dict:
        return {
            'valid': self.valid,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': [e.to_dict() for e in self.errors],
            'warnings': [w.to_dict() for w in self.warnings],
        }

    def get_summary(self) -> str:
        """Get human-readable summary."""
        lines = []
        if self.valid:
            lines.append(f"Validation passed: {len(self.entries)} entries")
        else:
            lines.append(f"Validation failed: {len(self.errors)} error(s)")

        if self.warnings:
            lines.append(f"Warnings: {len(self.warnings)}")

        return "\n".join(lines)


class JSONValidator:
    """
    Validator for blog post JSON input files.

    Validates:
    - JSON syntax and structure
    - Required fields (sns_id, sns_upload_cont, blog_title)
    - URL format for image fields
    - Tag normalization
    """

    # URL pattern for validation
    URL_PATTERN = re.compile(r'^https?://.+', re.IGNORECASE)

    # Fields that should contain URLs
    URL_FIELDS = [
        'blog_title_img', 'blog_title_img2', 'blog_title_img3',
        'site_img1', 'site_img2', 'site_cll_img'
    ]

    # Required fields
    REQUIRED_ROOT_FIELDS = ['sns_id', 'sns_upload_cont']
    REQUIRED_CONTENT_FIELDS = ['blog_title']

    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Validate a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            ValidationResult with errors, warnings, and parsed entries
        """
        result = ValidationResult()
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            result.add_error(ValidationError(
                index=-1,
                path="",
                field="file",
                message=f"File not found: {file_path}"
            ))
            return result

        # Check file is readable
        if not path.is_file():
            result.add_error(ValidationError(
                index=-1,
                path="",
                field="file",
                message=f"Not a file: {file_path}"
            ))
            return result

        # Read and parse JSON
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            result.add_error(ValidationError(
                index=-1,
                path="",
                field="json",
                message=f"Invalid JSON syntax: {e}"
            ))
            return result
        except UnicodeDecodeError as e:
            result.add_error(ValidationError(
                index=-1,
                path="",
                field="encoding",
                message=f"File must be UTF-8 encoded: {e}"
            ))
            return result

        return self.validate_data(data)

    def validate_data(self, data) -> ValidationResult:
        """
        Validate parsed JSON data.

        Args:
            data: Parsed JSON data (should be a list)

        Returns:
            ValidationResult with errors, warnings, and parsed entries
        """
        result = ValidationResult()

        # Must be a list
        if not isinstance(data, list):
            result.add_error(ValidationError(
                index=-1,
                path="",
                field="root",
                message="JSON root must be an array"
            ))
            return result

        # Empty list is invalid
        if len(data) == 0:
            result.add_error(ValidationError(
                index=-1,
                path="",
                field="root",
                message="JSON array is empty"
            ))
            return result

        # Validate each entry
        for i, entry_data in enumerate(data):
            entry_errors = self._validate_entry(entry_data, i)
            for error in entry_errors:
                if error.severity == "warning":
                    result.add_warning(error)
                else:
                    result.add_error(error)

            # Parse entry if no fatal errors for this entry
            entry_has_fatal = any(
                e.index == i and e.severity == "error"
                for e in result.errors
            )
            if not entry_has_fatal:
                try:
                    entry = BlogPostEntry.from_dict(entry_data, index=i)
                    result.entries.append(entry)
                except Exception as e:
                    result.add_error(ValidationError(
                        index=i,
                        path="",
                        field="parse",
                        message=f"Failed to parse entry: {e}"
                    ))

        return result

    def _validate_entry(self, entry_data: dict, index: int) -> List[ValidationError]:
        """Validate a single entry."""
        errors = []

        # Must be a dict
        if not isinstance(entry_data, dict):
            errors.append(ValidationError(
                index=index,
                path="",
                field="entry",
                message="Entry must be an object"
            ))
            return errors

        # Check required root fields
        for field in self.REQUIRED_ROOT_FIELDS:
            if field not in entry_data:
                errors.append(ValidationError(
                    index=index,
                    path=f".{field}",
                    field=field,
                    message=f"Required field '{field}' is missing"
                ))
            elif field == 'sns_id' and not entry_data[field]:
                errors.append(ValidationError(
                    index=index,
                    path=f".{field}",
                    field=field,
                    message="sns_id cannot be empty"
                ))

        # sns_pw can be empty (might use env override)
        if 'sns_pw' not in entry_data:
            errors.append(ValidationError(
                index=index,
                path=".sns_pw",
                field="sns_pw",
                message="Field 'sns_pw' is missing (can be provided via environment)",
                severity="warning"
            ))

        # Validate sns_upload_cont
        content = entry_data.get('sns_upload_cont', {})
        if not isinstance(content, dict):
            errors.append(ValidationError(
                index=index,
                path=".sns_upload_cont",
                field="sns_upload_cont",
                message="sns_upload_cont must be an object"
            ))
        else:
            # Check required content fields
            for field in self.REQUIRED_CONTENT_FIELDS:
                if field not in content or not content[field]:
                    errors.append(ValidationError(
                        index=index,
                        path=f".sns_upload_cont.{field}",
                        field=field,
                        message=f"Required field '{field}' is missing or empty"
                    ))

            # Validate URL fields
            for field in self.URL_FIELDS:
                url = content.get(field, '')
                if url and not self._is_valid_url(url):
                    errors.append(ValidationError(
                        index=index,
                        path=f".sns_upload_cont.{field}",
                        field=field,
                        message=f"Invalid URL format: {url[:50]}...",
                        severity="warning"
                    ))

            # Check tags format
            tags = content.get('site_tag', '')
            if tags:
                tag_warnings = self._validate_tags(tags, index)
                errors.extend(tag_warnings)

        return errors

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid (starts with http:// or https://)."""
        if not url:
            return True  # Empty is OK
        return bool(self.URL_PATTERN.match(url))

    def _validate_tags(self, tags: str, index: int) -> List[ValidationError]:
        """Validate and report issues with tags."""
        warnings = []

        # Check for trailing comma
        if tags.endswith(','):
            warnings.append(ValidationError(
                index=index,
                path=".sns_upload_cont.site_tag",
                field="site_tag",
                message="Tags have trailing comma (will be normalized)",
                severity="warning"
            ))

        # Check for empty tags
        tag_list = [t.strip() for t in tags.split(',')]
        empty_count = sum(1 for t in tag_list if not t)
        if empty_count > 0:
            warnings.append(ValidationError(
                index=index,
                path=".sns_upload_cont.site_tag",
                field="site_tag",
                message=f"Found {empty_count} empty tag(s) (will be removed)",
                severity="warning"
            ))

        return warnings


def validate_json_file(file_path: str) -> ValidationResult:
    """
    Convenience function to validate a JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        ValidationResult
    """
    validator = JSONValidator()
    return validator.validate_file(file_path)


def load_and_validate(file_path: str) -> Tuple[List[BlogPostEntry], ValidationResult]:
    """
    Load and validate a JSON file, returning entries and validation result.

    Args:
        file_path: Path to JSON file

    Returns:
        Tuple of (entries list, validation result)
    """
    result = validate_json_file(file_path)
    return result.entries, result
