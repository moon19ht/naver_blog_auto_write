"""
네이버 블로그 자동 글쓰기 프로그램
웹드라이버 관리 모듈
"""
import os
import platform
import subprocess
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from src.config import Config


def is_wsl() -> bool:
    """WSL 환경인지 확인"""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower() or 'wsl' in f.read().lower()
    except:
        return False


def get_windows_chrome_path() -> Optional[str]:
    """Windows Chrome 실행 파일 경로 찾기"""
    possible_paths = [
        '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe',
        '/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe',
        '/mnt/c/Users/{}/AppData/Local/Google/Chrome/Application/chrome.exe',
    ]
    
    for path in possible_paths:
        if '{' in path:
            # 사용자명 찾기
            try:
                result = subprocess.run(['cmd.exe', '/c', 'echo %USERNAME%'], 
                                       capture_output=True, text=True)
                username = result.stdout.strip()
                path = path.format(username)
            except:
                continue
        
        if os.path.exists(path):
            return path
    
    return None


def get_windows_chromedriver_path() -> Optional[str]:
    """Windows용 ChromeDriver 다운로드 및 경로 반환"""
    try:
        # webdriver-manager로 Windows용 드라이버 다운로드
        driver_path = ChromeDriverManager().install()
        
        # WSL에서 Windows 드라이버를 사용하려면 .exe 버전 필요
        # Windows 경로로 변환 시도
        if driver_path and os.path.exists(driver_path):
            return driver_path
    except Exception as e:
        print(f"[WARNING] ChromeDriver 다운로드 실패: {e}")
    
    return None


class WebDriverManager:
    """웹드라이버 관리 클래스"""
    
    def __init__(self, config: Config):
        self.config = config
        self.driver: Optional[webdriver.Remote] = None
        self.is_wsl = is_wsl()
    
    def create_driver(self) -> webdriver.Remote:
        """브라우저 타입에 따른 웹드라이버 생성"""
        browser_type = self.config.browser_type
        
        if self.is_wsl:
            print("[INFO] WSL 환경 감지됨 - Windows 브라우저 사용")
        
        if browser_type == 'chrome':
            self.driver = self._create_chrome_driver()
        elif browser_type == 'edge':
            self.driver = self._create_edge_driver()
        elif browser_type == 'firefox':
            self.driver = self._create_firefox_driver()
        else:
            raise ValueError(f"지원하지 않는 브라우저입니다: {browser_type}")
        
        # 암묵적 대기 설정
        self.driver.implicitly_wait(10)
        return self.driver
    
    def _create_chrome_driver(self) -> webdriver.Chrome:
        """크롬 드라이버 생성"""
        options = ChromeOptions()
        
        # 자동화 탐지 우회 설정
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 기본 설정
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')
        
        # GPU 및 그래픽 관련 오류 방지
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--use-gl=swiftshader')
        options.add_argument('--disable-accelerated-2d-canvas')
        
        # User-Agent 설정
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
        
        if self.config.headless:
            options.add_argument('--headless=new')
            # 원격 모드(SSH)에서는 추가 안정성 옵션
            if hasattr(self.config, 'remote_mode') and self.config.remote_mode:
                print("[INFO] SSH 원격 모드 - 헤드리스 최적화 적용")
                options.add_argument('--disable-setuid-sandbox')
                options.add_argument('--single-process')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--disable-infobars')
        
        # 한글 글꼴 지원
        options.add_argument('--lang=ko-KR')
        options.add_argument('--font-render-hinting=none')  # 한글 폰트 렌더링
        
        # Wayland/X11 환경 감지 및 설정
        session_type = os.environ.get('XDG_SESSION_TYPE', '')
        if session_type == 'wayland':
            print("[INFO] Wayland 세션 감지 - Ozone 플랫폼 설정")
            options.add_argument('--ozone-platform=wayland')
            # Wayland에서 클립보드 사용을 위한 추가 설정
            options.add_argument('--enable-features=UseOzonePlatform')
        elif not self.config.headless:
            # X11 또는 기타 환경에서 DISPLAY 확인
            display = os.environ.get('DISPLAY')
            if not display:
                print("[WARNING] DISPLAY 환경변수가 설정되지 않음. :0으로 설정합니다.")
                os.environ['DISPLAY'] = ':0'
        
        # WSL 환경 설정
        if self.is_wsl:
            print("[INFO] WSL 환경 - Linux Chrome (WSLg) 사용")
            # WSLg를 통해 Linux Chrome GUI 실행
            # DISPLAY 환경변수 확인
            display = os.environ.get('DISPLAY', ':0')
            if not display:
                os.environ['DISPLAY'] = ':0'
            
            # WSL 추가 옵션
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--remote-debugging-port=9222')
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # webdriver 속성 제거
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _create_edge_driver(self) -> webdriver.Edge:
        """엣지 드라이버 생성"""
        options = EdgeOptions()
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--start-maximized')
        
        if self.config.headless:
            options.add_argument('--headless=new')
        
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _create_firefox_driver(self) -> webdriver.Firefox:
        """파이어폭스 드라이버 생성"""
        options = FirefoxOptions()
        
        options.set_preference('dom.webdriver.enabled', False)
        options.set_preference('useAutomationExtension', False)
        
        if self.config.headless:
            options.add_argument('--headless')
        
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.maximize_window()
        
        return driver
    
    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        return self.create_driver()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
