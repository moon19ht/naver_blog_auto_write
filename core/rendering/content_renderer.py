"""
Content rendering module.

Converts the structured JSON content into HTML or plain text
suitable for the Naver blog editor.
"""
from typing import List, Optional
from core.models import BlogContent


class ContentRenderer:
    """
    Renders BlogContent into various formats.

    The renderer converts the structured fields from the JSON schema
    into a coherent blog post content.
    """

    def __init__(self):
        pass

    def render_html(self, content: BlogContent) -> str:
        """
        Render content as HTML.

        Args:
            content: BlogContent to render

        Returns:
            HTML string for the blog post body
        """
        sections = []

        # Title image
        if content.blog_title_img:
            sections.append(self._render_image(content.blog_title_img))

        # Top words (intro)
        if content.blog_top_word:
            sections.append(f'<p>{self._escape_html(content.blog_top_word)}</p>')

        if content.blog_top_word2:
            sections.append(f'<p>{self._escape_html(content.blog_top_word2)}</p>')

        # Second title image
        if content.blog_title_img2:
            sections.append(self._render_image(content.blog_title_img2))

        # Basic content
        if content.blog_basic:
            sections.append(f'<p>{self._escape_html(content.blog_basic)}</p>')

        # Feature content
        if content.blog_feature:
            sections.append(f'<p>{self._escape_html(content.blog_feature)}</p>')

        # Third title image
        if content.blog_title_img3:
            sections.append(self._render_image(content.blog_title_img3))

        # Site section 1
        if content.site_title1:
            sections.append(f'<h3>{self._escape_html(content.site_title1)}</h3>')
        if content.site_cont1:
            sections.append(f'<p>{self._escape_html(content.site_cont1)}</p>')
        if content.site_img1:
            sections.append(self._render_image(content.site_img1))

        # Quote
        if content.site_quote:
            sections.append(f'<blockquote>{self._escape_html(content.site_quote)}</blockquote>')

        # Site section 2
        if content.site_title2:
            sections.append(f'<h3>{self._escape_html(content.site_title2)}</h3>')
        if content.site_cont2:
            sections.append(f'<p>{self._escape_html(content.site_cont2)}</p>')
        if content.site_img2:
            sections.append(self._render_image(content.site_img2))

        # Address info
        if content.site_addr or content.site_addr2:
            addr_section = '<div class="address-info">'
            if content.site_addr:
                addr_section += f'<p><strong>Address:</strong> {self._escape_html(content.site_addr)}</p>'
            if content.site_addr2:
                addr_section += f'<p>{self._escape_html(content.site_addr2)}</p>'
            addr_section += '</div>'
            sections.append(addr_section)

        # Call image
        if content.site_cll_img:
            sections.append(self._render_image(content.site_cll_img))

        # Time/Hours
        if content.site_time:
            sections.append(f'<p><strong>Hours:</strong> {self._escape_html(content.site_time)}</p>')

        # Business info
        if content.site_bus:
            sections.append(f'<p>{self._escape_html(content.site_bus)}</p>')

        return '\n'.join(sections)

    def render_plain_text(self, content: BlogContent) -> str:
        """
        Render content as plain text.

        Args:
            content: BlogContent to render

        Returns:
            Plain text string for the blog post body
        """
        lines = []

        # Top words (intro)
        if content.blog_top_word:
            lines.append(content.blog_top_word)
            lines.append('')

        if content.blog_top_word2:
            lines.append(content.blog_top_word2)
            lines.append('')

        # Basic content
        if content.blog_basic:
            lines.append(content.blog_basic)
            lines.append('')

        # Feature content
        if content.blog_feature:
            lines.append(content.blog_feature)
            lines.append('')

        # Site section 1
        if content.site_title1:
            lines.append(f'=== {content.site_title1} ===')
        if content.site_cont1:
            lines.append(content.site_cont1)
            lines.append('')

        # Quote
        if content.site_quote:
            lines.append(f'"{content.site_quote}"')
            lines.append('')

        # Site section 2
        if content.site_title2:
            lines.append(f'=== {content.site_title2} ===')
        if content.site_cont2:
            lines.append(content.site_cont2)
            lines.append('')

        # Address info
        if content.site_addr:
            lines.append(f'Address: {content.site_addr}')
        if content.site_addr2:
            lines.append(content.site_addr2)

        # Time/Hours
        if content.site_time:
            lines.append(f'Hours: {content.site_time}')

        # Business info
        if content.site_bus:
            lines.append(content.site_bus)

        return '\n'.join(lines)

    def _render_image(self, url: str) -> str:
        """Render an image tag."""
        return f'<img src="{self._escape_html(url)}" alt="" />'

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ''
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


def render_content(content: BlogContent, format: str = 'plain') -> str:
    """
    Convenience function to render content.

    Args:
        content: BlogContent to render
        format: 'html' or 'plain'

    Returns:
        Rendered content string
    """
    renderer = ContentRenderer()
    if format == 'html':
        return renderer.render_html(content)
    return renderer.render_plain_text(content)
