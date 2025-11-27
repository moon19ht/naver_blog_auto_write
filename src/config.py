"""
네이버 블로그 자동 글쓰기 프로그램
설정 관리 모듈
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    """설정 클래스"""
    naver_id: str
    naver_pw: str
    browser_type: str
    headless: bool
    blog_id: str
    blog_category: str
    writer_mode: str  # 'selenium' 또는 'cdp'
    
    @classmethod
    def from_env(cls) -> 'Config':
        """환경 변수에서 설정 로드"""
        load_dotenv()
        
        naver_id = os.getenv('NAVER_ID', '')
        naver_pw = os.getenv('NAVER_PW', '')
        browser_type = os.getenv('BROWSER_TYPE', 'chrome').lower()
        headless = os.getenv('HEADLESS', 'False').lower() == 'true'
        blog_id = os.getenv('BLOG_ID', '').strip()
        blog_category = os.getenv('BLOG_CATEGORY', '일상')
        writer_mode = os.getenv('WRITER_MODE', 'cdp').lower()  # 'selenium' or 'cdp'
        
        if not naver_id or not naver_pw:
            raise ValueError("NAVER_ID와 NAVER_PW를 .env 파일에 설정해주세요.")
        
        # BLOG_ID가 비어있으면 NAVER_ID 사용
        if not blog_id:
            blog_id = naver_id
        
        return cls(
            naver_id=naver_id,
            naver_pw=naver_pw,
            browser_type=browser_type,
            headless=headless,
            blog_id=blog_id,
            blog_category=blog_category,
            writer_mode=writer_mode
        )


def get_config() -> Config:
    """설정 인스턴스 반환"""
    return Config.from_env()
