"""
Browser driver adapter.

Wraps the WebDriver management for browser automation.
This adapter provides a clean interface for the CLI to interact with browsers.
"""
import os
from dataclasses import dataclass
from typing import Optional

from selenium import webdriver


@dataclass
class BrowserConfig:
    """Browser configuration."""
    browser_type: str = 'chrome'
    headless: bool = False
    remote_mode: bool = False
    remote_debug_port: int = 9222
    window_size: str = '1920,1080'
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

    @classmethod
    def for_automation(cls, headless: bool = True) -> 'BrowserConfig':
        """Create config optimized for automation."""
        return cls(
            browser_type='chrome',
            headless=headless,
            remote_mode=headless,  # Remote mode implies headless
        )


class BrowserAdapter:
    """
    Adapter for browser driver management.

    Provides browser lifecycle management and health checking.
    """

    def __init__(self, config: Optional[BrowserConfig] = None):
        """
        Initialize browser adapter.

        Args:
            config: BrowserConfig, defaults to automation-friendly config
        """
        self.config = config or BrowserConfig.for_automation()
        self.driver: Optional[webdriver.Remote] = None

    def create_driver(self) -> webdriver.Remote:
        """
        Create and configure a browser driver.

        Returns:
            Configured WebDriver instance
        """
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from webdriver_manager.chrome import ChromeDriverManager

        options = ChromeOptions()

        # Anti-detection settings
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # Basic stability settings
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')

        # User agent
        options.add_argument(f'--user-agent={self.config.user_agent}')

        # Headless mode
        if self.config.headless:
            options.add_argument('--headless=new')
            options.add_argument(f'--window-size={self.config.window_size}')
            options.add_argument('--disable-setuid-sandbox')
            options.add_argument('--single-process')

        # Remote/SSH mode optimizations
        if self.config.remote_mode:
            options.add_argument('--disable-infobars')
            options.add_argument(f'--remote-debugging-port={self.config.remote_debug_port}')

        # Language settings
        options.add_argument('--lang=ko-KR')

        # Handle display environment
        if not self.config.headless:
            display = os.environ.get('DISPLAY')
            if not display:
                os.environ['DISPLAY'] = ':0'

        # Create driver
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        # Remove webdriver detection
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # Set implicit wait
        self.driver.implicitly_wait(10)

        return self.driver

    def get_driver(self) -> webdriver.Remote:
        """
        Get existing driver or create new one.

        Returns:
            WebDriver instance
        """
        if self.driver is None:
            return self.create_driver()
        return self.driver

    def close(self):
        """Close the browser driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def is_healthy(self) -> bool:
        """
        Check if driver is healthy.

        Returns:
            True if driver is responsive
        """
        if self.driver is None:
            return False
        try:
            # Try to get current URL as health check
            _ = self.driver.current_url
            return True
        except Exception:
            return False

    def __enter__(self):
        """Context manager entry."""
        return self.create_driver()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def check_browser_available() -> bool:
    """
    Check if browser automation is available.

    Returns:
        True if Chrome can be started
    """
    try:
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager

        options = ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.quit()
        return True
    except Exception as e:
        print(f"[DEBUG] Browser check failed: {e}")
        return False
