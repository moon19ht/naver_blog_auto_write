"""Unit tests for core models."""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models import BlogContent, BlogPostEntry, PostResult, BatchPostResult


class TestBlogContent:
    """Tests for BlogContent model."""

    def test_from_dict_basic(self):
        """Test creating BlogContent from dictionary."""
        data = {
            'blog_title': 'Test Title',
            'blog_basic': 'Test content',
        }
        content = BlogContent.from_dict(data)
        assert content.blog_title == 'Test Title'
        assert content.blog_basic == 'Test content'

    def test_from_dict_empty(self):
        """Test creating BlogContent from empty dictionary."""
        content = BlogContent.from_dict({})
        assert content.blog_title == ''
        assert content.blog_basic == ''

    def test_get_tags_comma_separated(self):
        """Test parsing comma-separated tags."""
        content = BlogContent(site_tag='tag1,tag2,tag3')
        tags = content.get_tags()
        assert tags == ['tag1', 'tag2', 'tag3']

    def test_get_tags_with_trailing_comma(self):
        """Test parsing tags with trailing comma."""
        content = BlogContent(site_tag='tag1,tag2,')
        tags = content.get_tags()
        assert tags == ['tag1', 'tag2']

    def test_get_tags_with_spaces(self):
        """Test parsing tags with spaces."""
        content = BlogContent(site_tag='tag1, tag2 , tag3')
        tags = content.get_tags()
        assert tags == ['tag1', 'tag2', 'tag3']

    def test_get_tags_empty(self):
        """Test getting tags from empty string."""
        content = BlogContent(site_tag='')
        tags = content.get_tags()
        assert tags == []

    def test_get_image_urls(self):
        """Test getting all image URLs."""
        content = BlogContent(
            blog_title_img='http://example.com/1.jpg',
            blog_title_img2='http://example.com/2.jpg',
            site_img1='',  # Empty should be excluded
        )
        urls = content.get_image_urls()
        assert len(urls) == 2
        assert 'http://example.com/1.jpg' in urls

    def test_to_dict(self):
        """Test converting to dictionary."""
        content = BlogContent(blog_title='Test', blog_basic='Content')
        d = content.to_dict()
        assert d['blog_title'] == 'Test'
        assert d['blog_basic'] == 'Content'


class TestBlogPostEntry:
    """Tests for BlogPostEntry model."""

    def test_from_dict_basic(self):
        """Test creating BlogPostEntry from dictionary."""
        data = {
            'sns_id': 'test@naver.com',
            'sns_pw': 'password123',
            'sns_upload_cont': {
                'blog_title': 'Test Post',
            }
        }
        entry = BlogPostEntry.from_dict(data, index=0)
        assert entry.sns_id == 'test@naver.com'
        assert entry.sns_pw == 'password123'
        assert entry.sns_upload_cont.blog_title == 'Test Post'
        assert entry.index == 0

    def test_to_dict_masks_password(self):
        """Test that to_dict masks password by default."""
        entry = BlogPostEntry(
            sns_id='test@naver.com',
            sns_pw='secret123',
            sns_upload_cont=BlogContent(blog_title='Test'),
        )
        d = entry.to_dict()
        assert d['sns_pw'] == '****'

    def test_to_dict_includes_password(self):
        """Test that to_dict can include password."""
        entry = BlogPostEntry(
            sns_id='test@naver.com',
            sns_pw='secret123',
            sns_upload_cont=BlogContent(blog_title='Test'),
        )
        d = entry.to_dict(include_password=True)
        assert d['sns_pw'] == 'secret123'

    def test_get_sanitized_email(self):
        """Test email sanitization."""
        entry = BlogPostEntry(
            sns_id='test@naver.com',
            sns_pw='',
            sns_upload_cont=BlogContent(),
        )
        sanitized = entry.get_sanitized_email()
        assert sanitized == 'test_at_naver_com'

    def test_repr_hides_password(self):
        """Test that repr doesn't show password."""
        entry = BlogPostEntry(
            sns_id='test@naver.com',
            sns_pw='secret',
            sns_upload_cont=BlogContent(blog_title='My Title'),
        )
        r = repr(entry)
        assert 'secret' not in r
        assert 'test@naver.com' in r


class TestBatchPostResult:
    """Tests for BatchPostResult model."""

    def test_add_result_success(self):
        """Test adding successful result."""
        batch = BatchPostResult()
        entry = BlogPostEntry(
            sns_id='test@naver.com',
            sns_pw='',
            sns_upload_cont=BlogContent(blog_title='Test'),
        )
        result = PostResult(entry=entry, success=True)
        batch.add_result(result)

        assert batch.total == 1
        assert batch.successful == 1
        assert batch.failed == 0

    def test_add_result_failure(self):
        """Test adding failed result."""
        batch = BatchPostResult()
        entry = BlogPostEntry(
            sns_id='test@naver.com',
            sns_pw='',
            sns_upload_cont=BlogContent(blog_title='Test'),
        )
        result = PostResult(entry=entry, success=False, error_message='Test error')
        batch.add_result(result)

        assert batch.total == 1
        assert batch.successful == 0
        assert batch.failed == 1

    def test_to_dict(self):
        """Test converting to dictionary."""
        batch = BatchPostResult()
        d = batch.to_dict()
        assert 'summary' in d
        assert 'results' in d
        assert d['summary']['total'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
