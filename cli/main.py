#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Naver Blog Automation CLI (nblog)

A CLI-first tool for batch posting to Naver Blog.

Commands:
    validate    Validate a JSON input file
    post        Post blog entries from JSON file
    doctor      Check system health and dependencies
"""
import argparse
import sys
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog='nblog',
        description='Naver Blog Automation CLI - Batch post to Naver Blog',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    # Validate input JSON
    nblog validate input.json

    # Post all entries
    nblog post input.json --all

    # Post specific account by index
    nblog post input.json --account-index 0

    # Post entries for specific email
    nblog post input.json --filter-email user@naver.com

    # Dry run (show what would be posted)
    nblog post input.json --all --dry-run

    # Post and save report
    nblog post input.json --all --out report.json

    # Check system health
    nblog doctor
'''
    )

    # Add version
    parser.add_argument(
        '--version', '-V',
        action='version',
        version='nblog 2.0.0'
    )

    # Create subparsers
    subparsers = parser.add_subparsers(
        dest='command',
        title='Commands',
        description='Available commands'
    )

    # -------------------------
    # validate command
    # -------------------------
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate a JSON input file',
        description='Validate blog post JSON file against the schema'
    )
    validate_parser.add_argument(
        'input_file',
        type=str,
        help='Path to JSON input file'
    )
    validate_parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only show errors, suppress warnings'
    )

    # -------------------------
    # post command
    # -------------------------
    post_parser = subparsers.add_parser(
        'post',
        help='Post blog entries from JSON file',
        description='Post blog entries from a JSON input file'
    )
    post_parser.add_argument(
        'input_file',
        type=str,
        help='Path to JSON input file'
    )

    # Selection options (mutually exclusive group)
    selection_group = post_parser.add_mutually_exclusive_group(required=True)
    selection_group.add_argument(
        '--all',
        action='store_true',
        dest='post_all',
        help='Post all entries in the file'
    )
    selection_group.add_argument(
        '--account-index',
        type=int,
        metavar='INDEX',
        help='Post only the entry at this index (0-based)'
    )
    selection_group.add_argument(
        '--filter-email',
        type=str,
        metavar='EMAIL',
        help='Post only entries matching this email'
    )

    # Posting options
    post_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be posted without actually posting'
    )
    post_parser.add_argument(
        '--out', '-o',
        type=str,
        metavar='FILE',
        help='Write JSON report to this file'
    )
    post_parser.add_argument(
        '--secrets-file',
        type=str,
        metavar='FILE',
        help='Path to external secrets JSON file'
    )
    post_parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run browser in headless mode (default: True)'
    )
    post_parser.add_argument(
        '--no-headless',
        action='store_false',
        dest='headless',
        help='Run browser with visible window'
    )
    post_parser.add_argument(
        '--retries',
        type=int,
        default=2,
        metavar='N',
        help='Max retries per post (default: 2)'
    )
    post_parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimize output'
    )

    # -------------------------
    # doctor command
    # -------------------------
    doctor_parser = subparsers.add_parser(
        'doctor',
        help='Check system health and dependencies',
        description='Verify that all dependencies and configurations are correct'
    )
    doctor_parser.add_argument(
        'input_file',
        type=str,
        nargs='?',
        help='Optional JSON file to check credentials for'
    )

    return parser


def cmd_validate(args) -> int:
    """Execute validate command."""
    from core.validation import validate_json_file
    from adapters.report import create_reporter

    reporter = create_reporter(quiet=args.quiet)
    result = validate_json_file(args.input_file)
    reporter.report_validation(result, args.input_file)

    return 0 if result.valid else 1


def cmd_post(args) -> int:
    """Execute post command."""
    from core.validation import load_and_validate
    from adapters.report import create_reporter
    from adapters.secrets import CredentialManager

    # Create reporter
    reporter = create_reporter(output_file=args.out, quiet=args.quiet)
    reporter.start()

    # Validate input
    entries, validation = load_and_validate(args.input_file)
    if not validation.valid:
        reporter.report_validation(validation, args.input_file)
        return 1

    # Report validation success
    if not args.quiet:
        print(f"[INFO] Loaded {len(entries)} entries from {args.input_file}")

    # Create credential manager
    credential_manager = CredentialManager(secrets_file=args.secrets_file)

    # Check credentials
    missing = credential_manager.check_credentials(entries)
    if missing:
        print(f"\n[WARNING] {len(missing)} account(s) missing credentials:")
        for email in missing:
            env_var = credential_manager.get_env_var_name(email)
            print(f"  - {email}")
            print(f"    Set: export {env_var}=<password>")

        if not args.dry_run:
            print("\n[ERROR] Cannot post without credentials. Use --dry-run to preview.")
            return 1

    # Dry run mode
    if args.dry_run:
        reporter.report_dry_run(entries, credential_manager)
        return 0

    # Import posting modules (requires selenium)
    from automation.naver_blog import PostingConfig, create_orchestrator

    # Create posting config
    config = PostingConfig(
        max_retries=args.retries,
        headless=args.headless,
    )

    # Create orchestrator
    orchestrator = create_orchestrator(
        secrets_file=args.secrets_file,
        config=config
    )

    # Post
    result = orchestrator.post_all(
        entries=entries,
        filter_email=args.filter_email,
        account_index=args.account_index
    )

    # Report results
    reporter.report_batch_result(result)

    return 0 if result.failed == 0 else 1


def cmd_doctor(args) -> int:
    """Execute doctor command."""
    from adapters.report import create_reporter
    from adapters.secrets import CredentialManager

    reporter = create_reporter()

    # Try to check browser availability (may fail if selenium not installed)
    browser_ok = False
    try:
        from adapters.browser import check_browser_available
        browser_ok = check_browser_available()
    except ImportError:
        print("[!!] Selenium not installed - browser check skipped")
        browser_ok = False

    # Load entries if file provided
    entries = []
    if args.input_file:
        from core.validation import load_and_validate
        entries, validation = load_and_validate(args.input_file)
        if not validation.valid:
            reporter.report_validation(validation, args.input_file)

    # Create credential manager
    credential_manager = CredentialManager()

    # Report
    reporter.report_doctor(entries, credential_manager, browser_ok)

    return 0 if browser_ok else 1


def main():
    """Main entry point."""
    # Add project root to path for imports
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    # Dispatch to command handlers
    if args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'post':
        return cmd_post(args)
    elif args.command == 'doctor':
        return cmd_doctor(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
