"""
Blog post data models matching the fixed JSON schema.

This module defines the data models used for batch blog posting.
The JSON schema is fixed and must not be changed.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class BlogContent:
    """
    Blog content schema (sns_upload_cont).

    All fields are optional except blog_title which is required for validation.
    """
    blog_title: str = ""
    blog_title_img: str = ""
    blog_top_word: str = ""
    blog_top_word2: str = ""
    blog_title_img2: str = ""
    blog_basic: str = ""
    blog_feature: str = ""
    blog_title_img3: str = ""
    site_title1: str = ""
    site_cont1: str = ""
    site_img1: str = ""
    site_quote: str = ""
    site_title2: str = ""
    site_cont2: str = ""
    site_img2: str = ""
    site_addr: str = ""
    site_addr2: str = ""
    site_cll_img: str = ""
    site_time: str = ""
    site_bus: str = ""
    site_tag: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> 'BlogContent':
        """Create BlogContent from dictionary."""
        return cls(
            blog_title=data.get('blog_title', ''),
            blog_title_img=data.get('blog_title_img', ''),
            blog_top_word=data.get('blog_top_word', ''),
            blog_top_word2=data.get('blog_top_word2', ''),
            blog_title_img2=data.get('blog_title_img2', ''),
            blog_basic=data.get('blog_basic', ''),
            blog_feature=data.get('blog_feature', ''),
            blog_title_img3=data.get('blog_title_img3', ''),
            site_title1=data.get('site_title1', ''),
            site_cont1=data.get('site_cont1', ''),
            site_img1=data.get('site_img1', ''),
            site_quote=data.get('site_quote', ''),
            site_title2=data.get('site_title2', ''),
            site_cont2=data.get('site_cont2', ''),
            site_img2=data.get('site_img2', ''),
            site_addr=data.get('site_addr', ''),
            site_addr2=data.get('site_addr2', ''),
            site_cll_img=data.get('site_cll_img', ''),
            site_time=data.get('site_time', ''),
            site_bus=data.get('site_bus', ''),
            site_tag=data.get('site_tag', ''),
        )

    def get_tags(self) -> List[str]:
        """Parse comma-separated tags into a list."""
        if not self.site_tag:
            return []
        # Split by comma and clean up
        tags = [tag.strip() for tag in self.site_tag.split(',')]
        # Remove empty strings
        return [tag for tag in tags if tag]

    def get_image_urls(self) -> List[str]:
        """Get all image URLs from the content."""
        urls = []
        for field_name in ['blog_title_img', 'blog_title_img2', 'blog_title_img3',
                          'site_img1', 'site_img2', 'site_cll_img']:
            url = getattr(self, field_name, '')
            if url:
                urls.append(url)
        return urls

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'blog_title': self.blog_title,
            'blog_title_img': self.blog_title_img,
            'blog_top_word': self.blog_top_word,
            'blog_top_word2': self.blog_top_word2,
            'blog_title_img2': self.blog_title_img2,
            'blog_basic': self.blog_basic,
            'blog_feature': self.blog_feature,
            'blog_title_img3': self.blog_title_img3,
            'site_title1': self.site_title1,
            'site_cont1': self.site_cont1,
            'site_img1': self.site_img1,
            'site_quote': self.site_quote,
            'site_title2': self.site_title2,
            'site_cont2': self.site_cont2,
            'site_img2': self.site_img2,
            'site_addr': self.site_addr,
            'site_addr2': self.site_addr2,
            'site_cll_img': self.site_cll_img,
            'site_time': self.site_time,
            'site_bus': self.site_bus,
            'site_tag': self.site_tag,
        }


@dataclass
class BlogPostEntry:
    """
    Single blog post entry from JSON input.

    Attributes:
        sns_id: Naver account email/ID
        sns_pw: Naver account password (should be handled securely)
        sns_upload_cont: Blog content to post
        index: Original index in JSON array (for error reporting)
    """
    sns_id: str
    sns_pw: str
    sns_upload_cont: BlogContent
    index: int = 0  # Position in original JSON array

    @classmethod
    def from_dict(cls, data: dict, index: int = 0) -> 'BlogPostEntry':
        """Create BlogPostEntry from dictionary."""
        content_data = data.get('sns_upload_cont', {})
        return cls(
            sns_id=data.get('sns_id', ''),
            sns_pw=data.get('sns_pw', ''),
            sns_upload_cont=BlogContent.from_dict(content_data),
            index=index
        )

    def to_dict(self, include_password: bool = False) -> dict:
        """
        Convert to dictionary.

        Args:
            include_password: If False, password is masked
        """
        return {
            'sns_id': self.sns_id,
            'sns_pw': self.sns_pw if include_password else '****',
            'sns_upload_cont': self.sns_upload_cont.to_dict(),
        }

    def get_sanitized_email(self) -> str:
        """Get sanitized email for use in environment variable names."""
        return self.sns_id.replace('@', '_at_').replace('.', '_')

    def __repr__(self) -> str:
        """Safe string representation without password."""
        return f"BlogPostEntry(sns_id='{self.sns_id}', index={self.index}, title='{self.sns_upload_cont.blog_title[:30]}...')"


@dataclass
class PostResult:
    """Result of posting a single blog entry."""
    entry: BlogPostEntry
    success: bool
    error_message: str = ""
    post_url: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON report."""
        return {
            'index': self.entry.index,
            'sns_id': self.entry.sns_id,
            'blog_title': self.entry.sns_upload_cont.blog_title,
            'success': self.success,
            'error_message': self.error_message,
            'post_url': self.post_url,
            'timestamp': self.timestamp,
        }


@dataclass
class BatchPostResult:
    """Result of batch posting operation."""
    total: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    results: List[PostResult] = field(default_factory=list)

    def add_result(self, result: PostResult):
        """Add a result and update counters."""
        self.results.append(result)
        self.total += 1
        if result.success:
            self.successful += 1
        else:
            self.failed += 1

    def add_skipped(self):
        """Mark an entry as skipped."""
        self.skipped += 1

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON report."""
        return {
            'summary': {
                'total': self.total,
                'successful': self.successful,
                'failed': self.failed,
                'skipped': self.skipped,
            },
            'results': [r.to_dict() for r in self.results],
        }
