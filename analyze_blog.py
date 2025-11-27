#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
블로그 페이지 HTML 분석 스크립트
글쓰기 버튼 요소를 찾기 위한 디버깅용
"""
import time
import re
from src.config import get_config
from src.driver import WebDriverManager
from src.naver_login import NaverLogin

def analyze_blog_page():
    config = get_config()
    driver_manager = WebDriverManager(config)
    
    try:
        print("[INFO] 브라우저 시작...")
        driver = driver_manager.create_driver()
        
        # 로그인
        print("[INFO] 네이버 로그인...")
        login = NaverLogin(driver, config)
        if not login.login():
            print("[ERROR] 로그인 실패")
            return
        
        time.sleep(2)
        
        # 블로그 메인으로 이동
        blog_url = f"https://blog.naver.com/{config.blog_id}"
        print(f"[INFO] 블로그로 이동: {blog_url}")
        driver.get(blog_url)
        time.sleep(5)
        
        # 전체 HTML 가져오기
        html = driver.page_source
        
        # HTML 파일로 저장
        with open("blog_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("[INFO] HTML 저장됨: blog_page.html")
        
        # 글쓰기 관련 요소 찾기
        print("\n" + "="*50)
        print("글쓰기 관련 요소 분석")
        print("="*50)
        
        # 글쓰기 텍스트가 포함된 부분 찾기
        write_patterns = [
            r'글쓰기',
            r'write',
            r'post',
            r'img_write',
        ]
        
        for pattern in write_patterns:
            matches = re.findall(f'.{{0,100}}{pattern}.{{0,100}}', html, re.IGNORECASE)
            if matches:
                print(f"\n[{pattern}] 관련 요소:")
                for match in matches[:5]:  # 최대 5개만
                    clean = match.replace('\n', ' ').replace('\r', ' ')
                    clean = re.sub(r'\s+', ' ', clean)
                    print(f"  - {clean[:150]}...")
        
        # 모든 a 태그와 button 태그 중 글쓰기 관련 찾기
        from selenium.webdriver.common.by import By
        
        print("\n" + "="*50)
        print("클릭 가능한 글쓰기 요소")
        print("="*50)
        
        # 모든 링크와 버튼 검사
        elements = driver.find_elements(By.CSS_SELECTOR, "a, button, img")
        
        for elem in elements:
            try:
                text = elem.text.strip()
                href = elem.get_attribute("href") or ""
                src = elem.get_attribute("src") or ""
                alt = elem.get_attribute("alt") or ""
                class_name = elem.get_attribute("class") or ""
                onclick = elem.get_attribute("onclick") or ""
                
                # 글쓰기 관련 키워드 체크
                keywords = ['글쓰기', 'write', 'post', 'Write', 'POST']
                
                for kw in keywords:
                    if (kw in text or kw.lower() in href.lower() or 
                        kw.lower() in src.lower() or kw in alt or 
                        kw.lower() in class_name.lower() or kw.lower() in onclick.lower()):
                        
                        print(f"\n발견! Tag: {elem.tag_name}")
                        print(f"  Text: {text}")
                        print(f"  href: {href}")
                        print(f"  src: {src}")
                        print(f"  alt: {alt}")
                        print(f"  class: {class_name}")
                        print(f"  onclick: {onclick}")
                        print(f"  displayed: {elem.is_displayed()}")
                        break
                        
            except Exception as e:
                continue
        
        print("\n[INFO] 분석 완료. 브라우저는 열려있습니다. Enter를 눌러 종료...")
        input()
        
    finally:
        driver_manager.close()

if __name__ == "__main__":
    analyze_blog_page()
