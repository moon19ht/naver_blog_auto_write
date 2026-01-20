"""
Report generation adapter.

Generates execution reports in various formats:
- JSON file
- Console output
- Summary statistics
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO

from core.models import BatchPostResult, PostResult
from core.validation import ValidationResult


class Reporter:
    """
    Generates and outputs execution reports.
    """

    def __init__(self, output_file: Optional[str] = None, quiet: bool = False):
        """
        Initialize reporter.

        Args:
            output_file: Optional path for JSON report output
            quiet: If True, minimize console output
        """
        self.output_file = output_file
        self.quiet = quiet
        self._start_time: Optional[datetime] = None

    def start(self):
        """Mark the start of execution."""
        self._start_time = datetime.now()

    def report_validation(self, result: ValidationResult, file_path: str):
        """
        Report validation results.

        Args:
            result: ValidationResult
            file_path: Path of validated file
        """
        if self.quiet and result.valid:
            return

        print(f"\nValidation Report: {file_path}")
        print("=" * 60)

        if result.valid:
            print(f"  Status: VALID")
            print(f"  Entries: {len(result.entries)}")
        else:
            print(f"  Status: INVALID")
            print(f"  Errors: {len(result.errors)}")

        if result.warnings:
            print(f"  Warnings: {len(result.warnings)}")

        # Print errors
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  [{error.index}]{error.path}: {error.message}")

        # Print warnings
        if result.warnings and not self.quiet:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  [{warning.index}]{warning.path}: {warning.message}")

        print("=" * 60)

    def report_post_result(self, result: PostResult):
        """
        Report a single post result.

        Args:
            result: PostResult
        """
        if self.quiet and result.success:
            return

        entry = result.entry
        status = "SUCCESS" if result.success else "FAILED"
        icon = "[OK]" if result.success else "[!!]"

        print(f"\n{icon} [{entry.index}] {entry.sns_id}")
        print(f"    Title: {entry.sns_upload_cont.blog_title[:50]}...")
        print(f"    Status: {status}")

        if result.error_message:
            print(f"    Error: {result.error_message}")
        if result.post_url:
            print(f"    URL: {result.post_url}")

    def report_batch_result(self, result: BatchPostResult):
        """
        Report batch posting results.

        Args:
            result: BatchPostResult
        """
        duration = ""
        if self._start_time:
            elapsed = datetime.now() - self._start_time
            duration = f" in {elapsed.total_seconds():.1f}s"

        print("\n")
        print("=" * 60)
        print("BATCH POSTING REPORT")
        print("=" * 60)
        print(f"  Total:      {result.total}")
        print(f"  Successful: {result.successful}")
        print(f"  Failed:     {result.failed}")
        print(f"  Skipped:    {result.skipped}")
        print(f"  Duration:   {duration}")
        print("=" * 60)

        # Summary of failed
        if result.failed > 0:
            print("\nFailed entries:")
            for r in result.results:
                if not r.success:
                    print(f"  [{r.entry.index}] {r.entry.sns_id}: {r.error_message}")

        # Write JSON report if output file specified
        if self.output_file:
            self._write_json_report(result)

    def _write_json_report(self, result: BatchPostResult):
        """Write JSON report to file."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': None,
            **result.to_dict()
        }

        if self._start_time:
            elapsed = datetime.now() - self._start_time
            report['duration_seconds'] = elapsed.total_seconds()

        try:
            path = Path(self.output_file)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n[INFO] Report written to: {self.output_file}")
        except Exception as e:
            print(f"\n[ERROR] Failed to write report: {e}")

    def report_dry_run(self, entries, credentials_manager):
        """
        Report what would be posted in dry-run mode.

        Args:
            entries: List of BlogPostEntry
            credentials_manager: CredentialManager for credential status
        """
        print("\n")
        print("=" * 60)
        print("DRY RUN - No posts will be made")
        print("=" * 60)
        print(f"Total entries: {len(entries)}")
        print("\nEntries to post:")

        for entry in entries:
            creds = credentials_manager.resolve_password(entry)
            cred_status = "OK" if creds.sns_pw else "MISSING"
            print(f"\n  [{entry.index}] {entry.sns_id}")
            print(f"      Title: {entry.sns_upload_cont.blog_title[:50]}...")
            print(f"      Tags: {', '.join(entry.sns_upload_cont.get_tags()[:5])}")
            print(f"      Credentials: {cred_status} (source: {creds.source})")

        print("\n" + "=" * 60)

    def report_doctor(self, entries, credentials_manager, browser_ok: bool):
        """
        Report system health check results.

        Args:
            entries: List of BlogPostEntry (can be empty)
            credentials_manager: CredentialManager
            browser_ok: Whether browser is available
        """
        print("\n")
        print("=" * 60)
        print("SYSTEM HEALTH CHECK")
        print("=" * 60)

        # Browser check
        browser_status = "OK" if browser_ok else "FAILED"
        browser_icon = "[OK]" if browser_ok else "[!!]"
        print(f"\n{browser_icon} Browser: {browser_status}")

        # Python version
        import platform
        print(f"[OK] Python: {platform.python_version()}")

        # Dependencies
        deps_ok = True
        required = ['selenium', 'webdriver_manager', 'dotenv']
        for dep in required:
            try:
                __import__(dep.replace('-', '_'))
                print(f"[OK] {dep}: installed")
            except ImportError:
                print(f"[!!] {dep}: NOT INSTALLED")
                deps_ok = False

        # Credentials check
        if entries:
            print("\nCredential Status:")
            missing = credentials_manager.check_credentials(entries)
            if missing:
                print(f"[!!] {len(missing)} account(s) missing credentials:")
                for email in missing:
                    env_var = credentials_manager.get_env_var_name(email)
                    print(f"     - {email}")
                    print(f"       Set: export {env_var}=<password>")
            else:
                print(f"[OK] All {len(entries)} account(s) have credentials")

        print("\n" + "=" * 60)


def create_reporter(output_file: Optional[str] = None, quiet: bool = False) -> Reporter:
    """
    Factory function to create a reporter.

    Args:
        output_file: Optional path for JSON report
        quiet: Minimize console output

    Returns:
        Reporter instance
    """
    return Reporter(output_file=output_file, quiet=quiet)
