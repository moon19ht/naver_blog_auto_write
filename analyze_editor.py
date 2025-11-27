#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
블로그 에디터 페이지 분석 스크립트
"""
import time
from selenium.webdriver.common.by import By
from src.config import get_config
from src.driver import WebDriverManager
from src.naver_login import NaverLogin

def analyze_editor():
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
        
        # 글쓰기 페이지로 이동
        write_url = f"https://blog.naver.com/{config.blog_id}/postwrite"
        print(f"[INFO] 글쓰기 페이지로 이동: {write_url}")
        driver.get(write_url)
        time.sleep(5)
        
        print(f"[INFO] 현재 URL: {driver.current_url}")
        print(f"[INFO] 페이지 타이틀: {driver.title}")
        
        # HTML 저장
        html = driver.page_source
        with open("editor_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("[INFO] HTML 저장됨: editor_page.html")
        
        # 모든 iframe 확인
        print("\n" + "="*50)
        print("페이지 내 iframe 목록")
        print("="*50)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for i, iframe in enumerate(iframes):
            print(f"  [{i}] id={iframe.get_attribute('id')}, name={iframe.get_attribute('name')}, src={iframe.get_attribute('src')[:100] if iframe.get_attribute('src') else 'None'}")
        
        # 발행 관련 요소 찾기
        print("\n" + "="*50)
        print("발행/등록 관련 버튼 요소")
        print("="*50)
        
        elements = driver.find_elements(By.CSS_SELECTOR, "button, a, span, div, input[type='button'], input[type='submit']")
        
        keywords = ['발행', '등록', '저장', 'publish', 'submit', 'save', 'post', '완료', '확인']
        
        for elem in elements:
            try:
                text = elem.text.strip()
                class_name = elem.get_attribute("class") or ""
                id_attr = elem.get_attribute("id") or ""
                onclick = elem.get_attribute("onclick") or ""
                tag = elem.tag_name
                
                found = False
                for kw in keywords:
                    if (kw in text.lower() or kw in class_name.lower() or 
                        kw in id_attr.lower() or kw in onclick.lower()):
                        found = True
                        break
                
                if found and elem.is_displayed():
                    print(f"\n★ 발견! Tag: {tag}")
                    print(f"  Text: '{text[:50]}'" if text else "  Text: (없음)")
                    print(f"  id: {id_attr}" if id_attr else "  id: (없음)")
                    print(f"  class: {class_name[:100]}" if class_name else "  class: (없음)")
                    print(f"  onclick: {onclick[:100]}" if onclick else "  onclick: (없음)")
                    print(f"  displayed: {elem.is_displayed()}, enabled: {elem.is_enabled()}")
                    
            except Exception as e:
                continue
        
        # 제목/본문 입력 필드 찾기
        print("\n" + "="*50)
        print("제목/본문 입력 필드")
        print("="*50)
        
        title_selectors = [
            "input[placeholder*='제목']",
            "textarea[placeholder*='제목']",
            ".se-title-text",
            "[class*='title']",
            "input[type='text']"
        ]
        
        for sel in title_selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for elem in elems:
                    if elem.is_displayed():
                        print(f"  제목 필드 후보: {sel}")
                        print(f"    tag: {elem.tag_name}, class: {elem.get_attribute('class')[:80] if elem.get_attribute('class') else 'None'}")
            except:
                pass
        
        # 에디터 영역 찾기
        content_selectors = [
            ".se-content",
            ".se-component-content",
            "[contenteditable='true']",
            ".ProseMirror",
            "[class*='editor']"
        ]
        
        for sel in content_selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for elem in elems:
                    if elem.is_displayed():
                        print(f"  본문 영역 후보: {sel}")
                        print(f"    tag: {elem.tag_name}, class: {elem.get_attribute('class')[:80] if elem.get_attribute('class') else 'None'}")
            except:
                pass
        
        print("\n[INFO] 분석 완료! 30초 후 종료...")
        time.sleep(30)
        
    finally:
        driver_manager.close()

if __name__ == "__main__":
    analyze_editor()
