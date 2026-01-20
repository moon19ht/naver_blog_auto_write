"""
Batch posting orchestrator for Naver Blog.

Handles the complete workflow of posting multiple blog entries:
1. Login to each account
2. Post content
3. Track results
4. Handle errors and retries
"""
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Callable

from core.models import BlogPostEntry, PostResult, BatchPostResult
from core.rendering import render_content
from adapters.secrets import CredentialManager, ResolvedCredentials
from adapters.browser import BrowserAdapter, BrowserConfig


@dataclass
class PostingConfig:
    """Configuration for batch posting."""
    max_retries: int = 2
    delay_between_posts: float = 5.0  # seconds
    delay_between_accounts: float = 10.0  # seconds
    headless: bool = True
    writer_mode: str = 'cdp'  # 'cdp' or 'selenium'


class BatchPostingOrchestrator:
    """
    Orchestrates batch posting to Naver Blog.

    This class manages the complete workflow of logging in,
    posting content, and tracking results for multiple accounts.
    """

    def __init__(
        self,
        credential_manager: CredentialManager,
        config: Optional[PostingConfig] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ):
        """
        Initialize orchestrator.

        Args:
            credential_manager: CredentialManager for password resolution
            config: PostingConfig for posting behavior
            progress_callback: Optional callback(current, total, message) for progress
        """
        self.credential_manager = credential_manager
        self.config = config or PostingConfig()
        self.progress_callback = progress_callback
        self._browser_adapter: Optional[BrowserAdapter] = None

    def _report_progress(self, current: int, total: int, message: str):
        """Report progress to callback if set."""
        if self.progress_callback:
            self.progress_callback(current, total, message)
        print(f"[{current}/{total}] {message}")

    def post_all(
        self,
        entries: List[BlogPostEntry],
        filter_email: Optional[str] = None,
        account_index: Optional[int] = None
    ) -> BatchPostResult:
        """
        Post all entries (or filtered subset).

        Args:
            entries: List of BlogPostEntry to post
            filter_email: Only post entries matching this email
            account_index: Only post entry at this index

        Returns:
            BatchPostResult with all posting results
        """
        result = BatchPostResult()

        # Filter entries if requested
        filtered_entries = self._filter_entries(entries, filter_email, account_index)
        total = len(filtered_entries)

        if total == 0:
            print("[WARNING] No entries to post after filtering")
            return result

        # Group by account for efficient login handling
        by_account = self._group_by_account(filtered_entries)

        current = 0
        for sns_id, account_entries in by_account.items():
            self._report_progress(current, total, f"Processing account: {sns_id}")

            # Resolve credentials
            creds = self.credential_manager.resolve_password(account_entries[0])
            if not creds.sns_pw:
                # Skip entries without credentials
                for entry in account_entries:
                    post_result = PostResult(
                        entry=entry,
                        success=False,
                        error_message="No credentials available",
                        timestamp=datetime.now().isoformat()
                    )
                    result.add_result(post_result)
                    current += 1
                continue

            # Post all entries for this account
            account_results = self._post_account_entries(account_entries, creds)
            for post_result in account_results:
                result.add_result(post_result)
                current += 1
                self._report_progress(
                    current, total,
                    f"Posted: {post_result.entry.sns_upload_cont.blog_title[:30]}... - "
                    f"{'SUCCESS' if post_result.success else 'FAILED'}"
                )

            # Delay between accounts
            if current < total:
                time.sleep(self.config.delay_between_accounts)

        return result

    def _filter_entries(
        self,
        entries: List[BlogPostEntry],
        filter_email: Optional[str],
        account_index: Optional[int]
    ) -> List[BlogPostEntry]:
        """Filter entries based on criteria."""
        result = entries

        if account_index is not None:
            result = [e for e in result if e.index == account_index]

        if filter_email:
            result = [e for e in result if e.sns_id == filter_email]

        return result

    def _group_by_account(self, entries: List[BlogPostEntry]) -> dict:
        """Group entries by account for efficient login handling."""
        by_account = {}
        for entry in entries:
            if entry.sns_id not in by_account:
                by_account[entry.sns_id] = []
            by_account[entry.sns_id].append(entry)
        return by_account

    def _post_account_entries(
        self,
        entries: List[BlogPostEntry],
        creds: ResolvedCredentials
    ) -> List[PostResult]:
        """
        Post all entries for a single account.

        This creates a browser session, logs in once, then posts all entries.
        """
        results = []

        try:
            # Create browser
            browser_config = BrowserConfig.for_automation(headless=self.config.headless)
            self._browser_adapter = BrowserAdapter(browser_config)
            driver = self._browser_adapter.create_driver()

            # Login to account
            if not self._login(driver, creds):
                # Login failed - mark all entries as failed
                for entry in entries:
                    results.append(PostResult(
                        entry=entry,
                        success=False,
                        error_message="Login failed",
                        timestamp=datetime.now().isoformat()
                    ))
                return results

            # Post each entry
            for entry in entries:
                post_result = self._post_single(driver, entry, creds)
                results.append(post_result)

                # Delay between posts
                if entry != entries[-1]:
                    time.sleep(self.config.delay_between_posts)

        except Exception as e:
            # Handle any unhandled errors
            for entry in entries:
                if not any(r.entry.index == entry.index for r in results):
                    results.append(PostResult(
                        entry=entry,
                        success=False,
                        error_message=f"Unexpected error: {str(e)}",
                        timestamp=datetime.now().isoformat()
                    ))
        finally:
            # Clean up browser
            if self._browser_adapter:
                self._browser_adapter.close()
                self._browser_adapter = None

        return results

    def _login(self, driver, creds: ResolvedCredentials) -> bool:
        """
        Login to Naver account.

        Uses the existing NaverLogin class from src.naver_login.
        """
        try:
            # Import here to avoid circular imports
            from src.naver_login import NaverLogin
            from src.config import Config

            # Create a minimal config for login
            # We create a Config-like object with required attributes
            class LoginConfig:
                def __init__(self, naver_id, naver_pw, headless):
                    self.naver_id = naver_id
                    self.naver_pw = naver_pw
                    self.headless = headless

            config = LoginConfig(creds.sns_id, creds.sns_pw, self.config.headless)
            login = NaverLogin(driver, config)

            return login.login()

        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            return False

    def _post_single(
        self,
        driver,
        entry: BlogPostEntry,
        creds: ResolvedCredentials
    ) -> PostResult:
        """
        Post a single blog entry.

        Uses the existing blog writer classes.
        """
        try:
            # Import writer
            if self.config.writer_mode == 'cdp':
                from src.blog_writer_cdp import NaverBlogWriterCDP as Writer
            else:
                from src.blog_writer import NaverBlogWriter as Writer

            # Create config-like object for writer
            class WriterConfig:
                def __init__(self, blog_id):
                    self.blog_id = blog_id

            # Extract blog ID from email (username part)
            blog_id = creds.sns_id.split('@')[0]
            config = WriterConfig(blog_id)

            writer = Writer(driver, config)

            # Render content
            content_text = render_content(entry.sns_upload_cont, format='plain')

            # Get tags
            tags = entry.sns_upload_cont.get_tags()

            # Default publish settings
            publish_settings = {
                'visibility': 'public',
                'allow_comment': True,
                'allow_sympathy': True,
                'allow_search': True,
                'blog_cafe_share': 'link',
                'allow_external_share': True,
                'is_notice': False
            }

            # Post
            if self.config.writer_mode == 'cdp':
                success = writer.write_post(
                    title=entry.sns_upload_cont.blog_title,
                    content=content_text,
                    tags=tags if tags else None,
                    publish_settings=publish_settings,
                    max_retries=self.config.max_retries
                )
            else:
                success = writer.write_post(
                    title=entry.sns_upload_cont.blog_title,
                    content=content_text,
                    tags=tags if tags else None,
                    is_public=True
                )

            return PostResult(
                entry=entry,
                success=success,
                error_message="" if success else "Post failed",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return PostResult(
                entry=entry,
                success=False,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )


def create_orchestrator(
    secrets_file: Optional[str] = None,
    config: Optional[PostingConfig] = None
) -> BatchPostingOrchestrator:
    """
    Factory function to create an orchestrator.

    Args:
        secrets_file: Optional path to secrets JSON file
        config: Optional PostingConfig

    Returns:
        BatchPostingOrchestrator instance
    """
    credential_manager = CredentialManager(secrets_file=secrets_file)
    return BatchPostingOrchestrator(
        credential_manager=credential_manager,
        config=config
    )
