#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
블로그 페이지 iframe 내부 HTML 분석 스크립트
"""
import time
from selenium.webdriver.common.by import By
from src.config import get_config
from src.driver import WebDriverManager
from src.naver_login import NaverLogin

def analyze_iframe():
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
        
        # mainFrame iframe으로 전환
        print("[INFO] mainFrame iframe으로 전환...")
        try:
            iframe = driver.find_element(By.ID, "mainFrame")
            driver.switch_to.frame(iframe)
            print("[INFO] iframe 전환 성공!")
        except Exception as e:
            print(f"[ERROR] iframe 전환 실패: {e}")
            return
        
        time.sleep(2)
        
        # iframe 내부 HTML 가져오기
        html = driver.page_source
        
        # HTML 파일로 저장
        with open("blog_iframe.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("[INFO] iframe HTML 저장됨: blog_iframe.html")
        
        # 글쓰기 관련 요소 찾기
        print("\n" + "="*50)
        print("iframe 내 글쓰기 관련 요소")
        print("="*50)
        
        # 모든 링크, 버튼, 이미지 검사
        elements = driver.find_elements(By.CSS_SELECTOR, "a, button, img, div, span")
        
        for elem in elements:
            try:
                text = elem.text.strip()
                href = elem.get_attribute("href") or ""
                src = elem.get_attribute("src") or ""
                alt = elem.get_attribute("alt") or ""
                class_name = elem.get_attribute("class") or ""
                onclick = elem.get_attribute("onclick") or ""
                tag = elem.tag_name
                
                # 글쓰기 관련 키워드 체크
                keywords = ['글쓰기', 'write', 'Write', 'WRITE', 'post', 'Post', 'btn_write', 'write_btn']
                
                found = False
                for kw in keywords:
                    if (kw in text or kw.lower() in href.lower() or 
                        kw.lower() in src.lower() or kw in alt or 
                        kw.lower() in class_name.lower() or kw.lower() in onclick.lower()):
                        found = True
                        break
                
                if found:
                    print(f"\n★ 발견! Tag: {tag}")
                    print(f"  Text: '{text[:50]}'" if text else "  Text: (없음)")
                    print(f"  href: {href[:100]}" if href else "  href: (없음)")
                    print(f"  src: {src[:100]}" if src else "  src: (없음)")
                    print(f"  alt: {alt}" if alt else "  alt: (없음)")
                    print(f"  class: {class_name}" if class_name else "  class: (없음)")
                    print(f"  onclick: {onclick[:100]}" if onclick else "  onclick: (없음)")
                    print(f"  displayed: {elem.is_displayed()}")
                    print(f"  enabled: {elem.is_enabled()}")
                        
            except Exception as e:
                continue
        
        # default content로 복귀
        driver.switch_to.default_content()
        
        print("\n[INFO] 분석 완료!")
        
    finally:
        driver_manager.close()

if __name__ == "__main__":
    analyze_iframe()
