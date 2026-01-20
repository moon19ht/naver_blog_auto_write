"""Credential management adapters."""
from .credential_manager import (
    CredentialManager,
    ResolvedCredentials,
    create_secrets_template,
)

__all__ = [
    'CredentialManager',
    'ResolvedCredentials',
    'create_secrets_template',
]
