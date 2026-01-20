"""
Credential management adapter.

Handles secure credential resolution with multiple sources:
1. Environment variable override (NBLOG_PW_<sanitized_email>)
2. External secrets file
3. JSON input (fallback)

Security features:
- Never logs passwords
- Masks passwords in output
- Clears sensitive data from memory
"""
import os
import json
import re
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

from core.models import BlogPostEntry


@dataclass
class ResolvedCredentials:
    """Resolved credentials with source tracking."""
    sns_id: str
    sns_pw: str
    source: str  # 'env', 'secrets_file', 'json'
    masked_pw: str = "****"

    def __post_init__(self):
        # Always set masked password
        if self.sns_pw:
            self.masked_pw = "*" * min(len(self.sns_pw), 8)


class CredentialManager:
    """
    Manages credential resolution and security.

    Priority order:
    1. Environment variables (NBLOG_PW_<sanitized_email>=password)
    2. External secrets file (JSON format)
    3. Password from input JSON (least preferred)
    """

    ENV_PREFIX = "NBLOG_PW_"

    def __init__(self, secrets_file: Optional[str] = None):
        """
        Initialize credential manager.

        Args:
            secrets_file: Optional path to external secrets JSON file
        """
        self.secrets_file = secrets_file
        self._secrets_cache: Dict[str, str] = {}
        self._load_secrets_file()

    def _load_secrets_file(self):
        """Load secrets from external file if provided."""
        if not self.secrets_file:
            return

        path = Path(self.secrets_file)
        if not path.exists():
            print(f"[WARNING] Secrets file not found: {self.secrets_file}")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._secrets_cache = data
                print(f"[INFO] Loaded {len(self._secrets_cache)} credentials from secrets file")
        except Exception as e:
            print(f"[WARNING] Failed to load secrets file: {e}")

    def _sanitize_email(self, email: str) -> str:
        """
        Sanitize email for environment variable name.

        example@naver.com -> example_at_naver_com
        """
        sanitized = email.replace('@', '_at_').replace('.', '_')
        # Remove any characters not suitable for env var names
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', sanitized)
        return sanitized.upper()

    def resolve_password(self, entry: BlogPostEntry) -> ResolvedCredentials:
        """
        Resolve password for an entry from available sources.

        Args:
            entry: BlogPostEntry to resolve password for

        Returns:
            ResolvedCredentials with password and source
        """
        sns_id = entry.sns_id

        # 1. Try environment variable
        env_var = f"{self.ENV_PREFIX}{self._sanitize_email(sns_id)}"
        env_pw = os.environ.get(env_var)
        if env_pw:
            return ResolvedCredentials(
                sns_id=sns_id,
                sns_pw=env_pw,
                source='env'
            )

        # 2. Try secrets file
        if sns_id in self._secrets_cache:
            return ResolvedCredentials(
                sns_id=sns_id,
                sns_pw=self._secrets_cache[sns_id],
                source='secrets_file'
            )

        # 3. Use JSON input
        if entry.sns_pw:
            return ResolvedCredentials(
                sns_id=sns_id,
                sns_pw=entry.sns_pw,
                source='json'
            )

        # No password found
        return ResolvedCredentials(
            sns_id=sns_id,
            sns_pw='',
            source='none'
        )

    def resolve_all(self, entries: List[BlogPostEntry]) -> Dict[str, ResolvedCredentials]:
        """
        Resolve passwords for all entries.

        Args:
            entries: List of BlogPostEntry

        Returns:
            Dict mapping sns_id to ResolvedCredentials
        """
        resolved = {}
        for entry in entries:
            creds = self.resolve_password(entry)
            resolved[entry.sns_id] = creds
        return resolved

    def check_credentials(self, entries: List[BlogPostEntry]) -> List[str]:
        """
        Check which entries have missing credentials.

        Args:
            entries: List of BlogPostEntry

        Returns:
            List of sns_ids with missing passwords
        """
        missing = []
        for entry in entries:
            creds = self.resolve_password(entry)
            if not creds.sns_pw:
                missing.append(entry.sns_id)
        return missing

    @staticmethod
    def mask_password(password: str) -> str:
        """Mask a password for safe display."""
        if not password:
            return "(empty)"
        return "*" * min(len(password), 8)

    @staticmethod
    def get_env_var_name(email: str) -> str:
        """Get the environment variable name for an email."""
        sanitized = email.replace('@', '_at_').replace('.', '_')
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', sanitized)
        return f"NBLOG_PW_{sanitized.upper()}"

    def print_credential_sources(self, entries: List[BlogPostEntry]):
        """Print credential resolution status (for debugging/doctor command)."""
        print("\nCredential Resolution Status:")
        print("-" * 60)
        for entry in entries:
            creds = self.resolve_password(entry)
            status = "OK" if creds.sns_pw else "MISSING"
            env_var = self.get_env_var_name(entry.sns_id)
            print(f"  {entry.sns_id}")
            print(f"    Status: {status}")
            print(f"    Source: {creds.source}")
            print(f"    Env var: {env_var}")
        print("-" * 60)


def create_secrets_template(entries: List[BlogPostEntry], output_path: str):
    """
    Create a secrets file template from entries.

    Args:
        entries: List of BlogPostEntry
        output_path: Path to write template
    """
    template = {}
    for entry in entries:
        template[entry.sns_id] = "YOUR_PASSWORD_HERE"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Secrets template created: {output_path}")
    print("[WARNING] Fill in passwords and store securely!")
