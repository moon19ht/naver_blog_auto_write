#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
네이버 블로그 자동 글쓰기 프로그램
Chrome DevTools MCP 기반 블로그 글쓰기 모듈

Chrome DevTools Protocol을 활용하여 더 안정적인 페이지 조작
"""
import time
from typing import Optional, List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.config import Config


class NaverBlogWriterCDP:
    """Chrome DevTools Protocol 기반 네이버 블로그 글 작성 클래스"""
    
    def __init__(self, driver, config: Config):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(driver, 20)
        self.blog_id = config.blog_id
    
    def _execute_cdp(self, cmd: str, params: dict = None):
        """CDP 명령 실행"""
        if params is None:
            params = {}
        return self.driver.execute_cdp_cmd(cmd, params)
    
    def _evaluate_js(self, expression: str):
        """JavaScript 표현식 실행 (CDP Runtime.evaluate)"""
        try:
            result = self._execute_cdp("Runtime.evaluate", {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            })
            return result.get('result', {}).get('value')
        except Exception as e:
            print(f"[DEBUG] JS 실행 실패: {e}")
            return None
    
    def _cdp_click(self, x: float, y: float):
        """CDP를 통한 마우스 클릭"""
        try:
            self._execute_cdp("Input.dispatchMouseEvent", {
                "type": "mousePressed",
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1
            })
            time.sleep(0.05)
            self._execute_cdp("Input.dispatchMouseEvent", {
                "type": "mouseReleased",
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1
            })
            return True
        except Exception as e:
            print(f"[DEBUG] CDP 클릭 실패: {e}")
            return False
    
    def _cdp_type_text(self, text: str):
        """CDP를 통한 텍스트 입력"""
        try:
            self._execute_cdp("Input.insertText", {"text": text})
            return True
        except Exception as e:
            print(f"[DEBUG] CDP 텍스트 입력 실패: {e}")
            return False
    
    def _cdp_press_key(self, key: str, modifiers: int = 0):
        """CDP를 통한 키 입력"""
        try:
            # keyDown
            self._execute_cdp("Input.dispatchKeyEvent", {
                "type": "keyDown",
                "key": key,
                "modifiers": modifiers
            })
            # keyUp
            self._execute_cdp("Input.dispatchKeyEvent", {
                "type": "keyUp",
                "key": key,
                "modifiers": modifiers
            })
            return True
        except Exception as e:
            print(f"[DEBUG] CDP 키 입력 실패: {e}")
            return False
    
    def _get_element_center(self, selector: str) -> Optional[tuple]:
        """요소의 중심 좌표 가져오기"""
        result = self._evaluate_js(f'''
        (function() {{
            const el = document.querySelector('{selector}');
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            return {{
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
                visible: rect.width > 0 && rect.height > 0
            }};
        }})()
        ''')
        if result and result.get('visible'):
            return (result['x'], result['y'])
        return None
    
    def _click_element_by_selector(self, selector: str) -> bool:
        """선택자로 요소 클릭 (CDP 사용)"""
        coords = self._get_element_center(selector)
        if coords:
            return self._cdp_click(coords[0], coords[1])
        return False
    
    def _handle_alert(self):
        """알림창 처리"""
        try:
            alert = self.driver.switch_to.alert
            print(f"[WARNING] 알림창 감지: {alert.text}")
            alert.accept()
            time.sleep(1)
        except:
            pass
    
    def write_post(self, title: str, content: str, category: Optional[str] = None, 
                   tags: Optional[List[str]] = None, publish_settings: Optional[dict] = None,
                   max_retries: int = 2) -> bool:
        """
        블로그 글 작성 및 발행 (CDP 기반)
        
        흐름:
        1. 에디터로 이동
        2. 임시저장 글 팝업 처리 (있는 경우)
        3. 도움말 팝업 닫기 (있는 경우)
        4. 제목/본문 입력
        5. 발행 버튼 클릭 (1차) → 발행 설정 팝업 열림
        6. 팝업에서 카테고리/태그/공개설정 후 최종 발행 버튼 클릭
        7. 블로그로 이동하여 발행 확인
        8. 실패 시 재시도
        
        Args:
            title: 글 제목
            content: 글 내용
            category: 카테고리 이름
            tags: 태그 리스트
            publish_settings: 발행 설정 딕셔너리
            max_retries: 최대 재시도 횟수
        """
        # 기본 발행 설정
        if publish_settings is None:
            publish_settings = {
                'visibility': 'public',
                'allow_comment': True,
                'allow_sympathy': True,
                'allow_search': True,
                'blog_cafe_share': 'link',
                'allow_external_share': True,
                'is_notice': False
            }
        
        print(f"[INFO] [CDP] 블로그 글 작성 시작: {title}")
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                print(f"\n[INFO] [CDP] 재시도 {attempt}/{max_retries}...")
            
            try:
                # 글쓰기 에디터로 이동
                if not self._navigate_to_editor():
                    continue
                
                # 임시저장 글 팝업 처리 (작성 취소)
                self._handle_draft_popup()
                
                # 도움말 팝업 닫기 (우측에 나오는 팝업)
                self._close_help_popup()
                
                # 제목 입력
                if not self._input_title(title):
                    continue
                
                # 본문 내용 입력
                if not self._input_content(content):
                    continue
                
                # 발행 (카테고리, 태그, 공개설정 포함)
                publish_result = self._publish(title=title, category=category, tags=tags, publish_settings=publish_settings)
                
                if publish_result:
                    # 발행 성공 확인 (블로그 글목록에서 확인)
                    if self._verify_post_published(title):
                        print("[SUCCESS] [CDP] 발행 확인 완료!")
                        return True
                    else:
                        print("[WARNING] [CDP] 발행 확인 실패, 재시도...")
                        continue
                else:
                    continue
                    
            except Exception as e:
                print(f"[ERROR] 글 작성 중 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"[ERROR] [CDP] {max_retries + 1}번 시도 후 발행 실패")
        return False
    
    def _handle_draft_popup(self) -> bool:
        """임시저장 글 팝업 처리 - '작성 취소' 버튼 클릭"""
        try:
            print("[INFO] [CDP] 임시저장 글 팝업 확인 중...")
            time.sleep(2)
            
            result = self._evaluate_js('''
            (function() {
                // 임시저장 관련 팝업/모달 찾기 - 더 구체적인 텍스트
                const popupTexts = ['작성 중인 글이 있습니다', '임시저장된 글', '작성하던 글이 있습니다', '이어서 작성하시겠습니까'];
                
                // 팝업/모달 컨테이너 찾기
                const modalContainers = document.querySelectorAll('[class*="modal"], [class*="layer"], [class*="popup"], [class*="dialog"], [role="dialog"]');
                
                for (const container of modalContainers) {
                    if (container.offsetParent === null) continue;
                    
                    const containerText = container.innerText;
                    let hasPopup = false;
                    
                    for (const txt of popupTexts) {
                        if (containerText.includes(txt)) {
                            hasPopup = true;
                            break;
                        }
                    }
                    
                    if (!hasPopup) continue;
                    
                    // 이 컨테이너 내에서 취소/새로작성 버튼 찾기
                    const buttons = container.querySelectorAll('button');
                    for (const btn of buttons) {
                        const btnText = btn.textContent.trim();
                        // 정확히 매칭되는 텍스트
                        if (btnText === '작성 취소' || btnText === '취소' || 
                            btnText === '새로 작성' || btnText === '아니요' ||
                            btnText === '새글 작성') {
                            const rect = btn.getBoundingClientRect();
                            btn.click();
                            return { 
                                found: true, 
                                clicked: btnText,
                                container: container.className.substring(0, 50)
                            };
                        }
                    }
                }
                
                return { found: false };
            })()
            ''')
            
            if result and result.get('found'):
                print(f"[INFO] [CDP] 임시저장 팝업 - '{result.get('clicked')}' 버튼 클릭 (container: {result.get('container')})")
                time.sleep(2)
            else:
                print("[INFO] [CDP] 임시저장 팝업 없음")
            
            return True
            
        except Exception as e:
            print(f"[DEBUG] [CDP] 임시저장 팝업 처리 오류: {e}")
            return True
    
    def _close_help_popup(self) -> bool:
        """도움말 팝업 닫기 (글쓰기 페이지 우측 팝업)"""
        try:
            print("[INFO] [CDP] 도움말 팝업 확인 중...")
            time.sleep(1)
            
            # 도움말/가이드 팝업 닫기 버튼 찾기
            close_result = self._evaluate_js('''
            (function() {
                // 닫기 버튼 선택자들 (다양한 패턴)
                const closeSelectors = [
                    // 일반적인 닫기 버튼
                    '[class*="help"] [class*="close"]',
                    '[class*="guide"] [class*="close"]',
                    '[class*="tooltip"] [class*="close"]',
                    '[class*="popup"] [class*="close"]',
                    '[class*="layer"] [class*="close"]',
                    '[class*="modal"] [class*="close"]',
                    // 버튼 타입 닫기
                    'button[class*="close"]',
                    'button[aria-label*="닫기"]',
                    'button[aria-label*="close"]',
                    // X 아이콘 버튼
                    '[class*="btn_close"]',
                    '[class*="closeBtn"]',
                    '[class*="close_btn"]',
                    // 도움말 관련
                    '[class*="help_close"]',
                    '[class*="tip_close"]',
                    '[class*="guide_close"]',
                    // 우측 패널/사이드바
                    '[class*="side"] [class*="close"]',
                    '[class*="panel"] [class*="close"]',
                    '[class*="aside"] [class*="close"]',
                    // 네이버 에디터 특정
                    '.se-help-panel-close',
                    '.se-popup-close',
                    '[class*="help_panel"] button',
                    '[class*="helpPanel"] button'
                ];
                
                const closedButtons = [];
                
                for (const sel of closeSelectors) {
                    const elements = document.querySelectorAll(sel);
                    for (const el of elements) {
                        if (el.offsetParent !== null && el.offsetWidth > 0) {
                            const rect = el.getBoundingClientRect();
                            // 우측에 있는 요소만 (화면 중앙 이후)
                            if (rect.left > window.innerWidth / 2) {
                                el.click();
                                closedButtons.push({
                                    selector: sel,
                                    x: rect.left,
                                    y: rect.top
                                });
                            }
                        }
                    }
                }
                
                // "다시 보지 않기" 또는 "닫기" 텍스트가 있는 버튼/링크
                const allClickables = document.querySelectorAll('button, a, span, div');
                for (const el of allClickables) {
                    const text = el.textContent.trim();
                    if ((text === '닫기' || text === '✕' || text === '×' || text === 'X' || 
                         text.includes('다시 보지 않기') || text === '확인') && 
                        el.offsetParent !== null) {
                        const rect = el.getBoundingClientRect();
                        // 우측에 있는 요소
                        if (rect.left > window.innerWidth / 2 || rect.top < 200) {
                            el.click();
                            closedButtons.push({
                                text: text,
                                x: rect.left,
                                y: rect.top
                            });
                        }
                    }
                }
                
                return { closed: closedButtons.length, buttons: closedButtons };
            })()
            ''')
            
            if close_result and close_result.get('closed', 0) > 0:
                print(f"[INFO] [CDP] 팝업 닫기 버튼 {close_result.get('closed')}개 클릭")
                time.sleep(1)
            else:
                print("[INFO] [CDP] 닫을 팝업 없음")
            
            # ESC 키로 팝업 닫기 시도
            self._cdp_press_key("Escape")
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"[DEBUG] [CDP] 도움말 팝업 닫기 중 오류: {e}")
            return True  # 에러가 나도 계속 진행
    
    def _navigate_to_editor(self) -> bool:
        """글쓰기 에디터로 이동 (CDP 활용)"""
        try:
            self._handle_alert()
            
            # 블로그 메인 페이지로 이동
            blog_main_url = f"https://blog.naver.com/{self.blog_id}"
            print(f"[INFO] [CDP] 블로그 메인 페이지로 이동: {blog_main_url}")
            self.driver.get(blog_main_url)
            time.sleep(4)
            self._handle_alert()
            
            # JavaScript로 iframe 내부의 글쓰기 버튼 찾아서 href 가져오기
            print("[INFO] [CDP] iframe 내부에서 글쓰기 버튼 검색...")
            
            write_url = self._evaluate_js('''
            (function() {
                const mainFrame = document.getElementById('mainFrame');
                if (mainFrame && mainFrame.contentDocument) {
                    const frameDoc = mainFrame.contentDocument;
                    
                    // 글쓰기 이미지 버튼의 부모 링크
                    const writeImg = frameDoc.querySelector('img[src*="img_write_btn"]');
                    if (writeImg && writeImg.parentElement && writeImg.parentElement.href) {
                        return writeImg.parentElement.href;
                    }
                    
                    // 글쓰기 텍스트 링크
                    const links = frameDoc.querySelectorAll('a');
                    for (const link of links) {
                        if (link.textContent.trim() === '글쓰기' && link.href) {
                            return link.href;
                        }
                        if (link.href && link.href.includes('postwrite')) {
                            return link.href;
                        }
                    }
                }
                return null;
            })()
            ''')
            
            if write_url:
                print(f"[INFO] [CDP] 글쓰기 URL 발견: {write_url}")
                self.driver.get(write_url)
            else:
                # 직접 URL로 이동
                print("[INFO] [CDP] 글쓰기 버튼을 찾지 못해 직접 URL로 이동...")
                write_url = f"https://blog.naver.com/{self.blog_id}/postwrite"
                self.driver.get(write_url)
            
            time.sleep(4)
            self._handle_alert()
            
            # 에디터 로드 확인
            print("[INFO] [CDP] 에디터 로드 대기...")
            editor_loaded = self._wait_for_editor()
            
            if editor_loaded:
                print("[INFO] [CDP] 에디터 로드 완료")
                return True
            else:
                print("[WARNING] [CDP] 에디터 로드 확인 실패, 계속 진행...")
                return True
                
        except Exception as e:
            print(f"[ERROR] [CDP] 에디터 이동 실패: {e}")
            return False
    
    def _wait_for_editor(self, timeout: int = 15) -> bool:
        """에디터 로드 대기"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 에디터 요소 확인
            result = self._evaluate_js('''
            (function() {
                // 스마트에디터 ONE 확인
                const seBody = document.querySelector('.se-body, .__se-body');
                const seContent = document.querySelector('.se-content');
                const titleInput = document.querySelector('.se-title-input, [contenteditable="true"]');
                
                return {
                    seBody: !!seBody,
                    seContent: !!seContent,
                    titleInput: !!titleInput,
                    url: window.location.href
                };
            })()
            ''')
            
            if result and (result.get('seBody') or result.get('seContent') or result.get('titleInput')):
                return True
            
            time.sleep(0.5)
        
        return False
    
    def _input_title(self, title: str) -> bool:
        """제목 입력 (CDP 클릭 + Input.insertText 방식)"""
        try:
            print("[INFO] [CDP] 제목 입력 중...")
            print(f"[DEBUG] [CDP] 입력할 제목: {title}")
            
            # 제목 영역 좌표 얻기
            title_pos = self._evaluate_js('''
            (function() {
                // 제목 영역 찾기 - placeholder가 "제목"인 영역
                const allParagraphs = document.querySelectorAll('.se-text-paragraph');
                for (const el of allParagraphs) {
                    const placeholder = el.querySelector('.se-placeholder');
                    if (placeholder && placeholder.textContent.includes('제목')) {
                        const rect = el.getBoundingClientRect();
                        return {
                            found: true,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            selector: 'placeholder-title'
                        };
                    }
                }
                
                // se-title-text 클래스로 찾기
                const titleEl = document.querySelector('.se-title-text .se-text-paragraph');
                if (titleEl) {
                    const rect = titleEl.getBoundingClientRect();
                    return {
                        found: true,
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2,
                        selector: '.se-title-text .se-text-paragraph'
                    };
                }
                
                return { found: false };
            })()
            ''')
            
            if title_pos and title_pos.get('found'):
                print(f"[DEBUG] [CDP] 제목 영역 발견: {title_pos.get('selector')}, 좌표: ({title_pos.get('x')}, {title_pos.get('y')})")
                
                # CDP로 제목 영역 클릭
                self._cdp_click(title_pos['x'], title_pos['y'])
                time.sleep(0.3)
                
                # 한 번 더 클릭 (확실하게)
                self._cdp_click(title_pos['x'], title_pos['y'])
                time.sleep(0.3)
                
                # CDP Input.insertText로 제목 입력
                success = self._cdp_type_text(title)
                
                if success:
                    print("[INFO] [CDP] 제목 입력 완료")
                    time.sleep(0.3)
                    return True
            
            print("[ERROR] [CDP] 제목 영역을 찾지 못함")
            return False
                
        except Exception as e:
            print(f"[ERROR] [CDP] 제목 입력 실패: {e}")
            return False
    
    def _input_content(self, content: str) -> bool:
        """본문 내용 입력 (CDP 클릭 + Input.insertText 방식)"""
        try:
            print("[INFO] [CDP] 본문 입력 중...")
            print(f"[DEBUG] [CDP] 입력할 내용: {content[:50]}..." if len(content) > 50 else f"[DEBUG] [CDP] 입력할 내용: {content}")
            
            # 본문 영역 좌표 얻기 (제목이 아닌 영역)
            content_pos = self._evaluate_js('''
            (function() {
                // 모든 se-text-paragraph 중 제목이 아닌 것 찾기
                const allParagraphs = document.querySelectorAll('.se-text-paragraph');
                for (const el of allParagraphs) {
                    // 제목 영역이 아닌지 확인
                    const isTitle = el.closest('.se-title-text') || 
                                   el.closest('.se-documentTitle') ||
                                   el.querySelector('.se-placeholder')?.textContent?.includes('제목');
                    
                    if (!isTitle) {
                        const rect = el.getBoundingClientRect();
                        return {
                            found: true,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            selector: 'non-title paragraph'
                        };
                    }
                }
                
                // se-component.se-text 내의 본문 영역 찾기
                const contentEl = document.querySelector('.se-component.se-text .se-text-paragraph');
                if (contentEl) {
                    const rect = contentEl.getBoundingClientRect();
                    return {
                        found: true,
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2,
                        selector: '.se-component.se-text .se-text-paragraph'
                    };
                }
                
                return { found: false };
            })()
            ''')
            
            if content_pos and content_pos.get('found'):
                print(f"[DEBUG] [CDP] 본문 영역 발견: {content_pos.get('selector')}, 좌표: ({content_pos.get('x')}, {content_pos.get('y')})")
                
                # CDP로 본문 영역 클릭
                self._cdp_click(content_pos['x'], content_pos['y'])
                time.sleep(0.3)
                
                # 한 번 더 클릭 (확실하게)
                self._cdp_click(content_pos['x'], content_pos['y'])
                time.sleep(0.3)
            else:
                print("[WARNING] [CDP] 본문 영역을 찾지 못함")
            
            # CDP Input.insertText로 본문 입력
            success = self._cdp_type_text(content)
            
            if success:
                print("[INFO] [CDP] 본문 입력 완료")
                time.sleep(0.3)
                return True
            else:
                print("[ERROR] [CDP] 본문 입력 실패")
                return False
            
        except Exception as e:
            print(f"[ERROR] [CDP] 본문 입력 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _publish(self, title: str = "", category: Optional[str] = None, 
                 tags: Optional[List[str]] = None, publish_settings: Optional[dict] = None) -> bool:
        """
        글 발행 (CDP 활용)
        
        단계:
        1. 도움말 팝업이 있으면 닫기
        2. 우측 상단 발행 버튼 클릭 (1차)
        3. 발행 설정 팝업에서 카테고리/태그/공개설정/발행옵션
        4. 팝업 내 발행 버튼 클릭 (최종)
        """
        # 기본 발행 설정
        if publish_settings is None:
            publish_settings = {
                'visibility': 'public',
                'allow_comment': True,
                'allow_sympathy': True,
                'allow_search': True,
                'blog_cafe_share': 'link',
                'allow_external_share': True,
                'is_notice': False
            }
        
        try:
            print("[INFO] [CDP] 글 발행 프로세스 시작...")
            self._handle_alert()
            
            # 1. 도움말 팝업 다시 확인하고 닫기
            self._close_help_popup()
            time.sleep(1)
            
            # 2. 우측 상단 발행 버튼 찾기 (1차 발행 버튼)
            print("[INFO] [CDP] 1차 발행 버튼 검색...")
            
            first_publish_result = self._evaluate_js('''
            (function() {
                // 헤더 영역의 발행 버튼 (우측 상단)
                const headerSelectors = [
                    'header button[class*="publish"]',
                    '.header button[class*="publish"]',
                    '[class*="header"] button[class*="publish"]',
                    'button[class*="publish_btn__"]',
                    'button.publish_btn__m9KHH',
                    '.publish_btn_area__KjA2i button',
                    '[class*="publish_btn_area"] button'
                ];
                
                for (const sel of headerSelectors) {
                    const btn = document.querySelector(sel);
                    if (btn && btn.offsetParent !== null) {
                        const rect = btn.getBoundingClientRect();
                        // 상단에 있는 버튼 (y < 100)
                        if (rect.top < 100) {
                            return {
                                found: true,
                                x: rect.left + rect.width / 2,
                                y: rect.top + rect.height / 2,
                                text: btn.textContent.trim(),
                                type: 'header'
                            };
                        }
                    }
                }
                
                // 모든 버튼에서 "발행" 텍스트 찾기 (상단)
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.textContent.trim() === '발행' && btn.offsetParent !== null) {
                        const rect = btn.getBoundingClientRect();
                        if (rect.top < 100) {  // 상단 영역
                            return {
                                found: true,
                                x: rect.left + rect.width / 2,
                                y: rect.top + rect.height / 2,
                                text: '발행',
                                type: 'text'
                            };
                        }
                    }
                }
                
                return { found: false };
            })()
            ''')
            
            if not first_publish_result or not first_publish_result.get('found'):
                print("[ERROR] [CDP] 1차 발행 버튼을 찾을 수 없습니다.")
                # 디버깅: 현재 버튼 목록 출력
                self._debug_buttons()
                return False
            
            print(f"[INFO] [CDP] 1차 발행 버튼 발견 (type: {first_publish_result.get('type')})")
            
            # 1차 발행 버튼 클릭
            self._cdp_click(first_publish_result['x'], first_publish_result['y'])
            print("[INFO] [CDP] 1차 발행 버튼 클릭 완료")
            time.sleep(2)
            
            # 3. 발행 설정 팝업 대기
            print("[INFO] [CDP] 발행 설정 팝업 대기...")
            popup_ready = self._wait_for_publish_popup()
            
            if not popup_ready:
                print("[WARNING] [CDP] 발행 팝업을 찾지 못함, 재시도...")
                time.sleep(1)
            
            # 4. 팝업에서 카테고리 설정
            if category:
                self._set_category_in_popup(category)
            
            # 5. 팝업에서 태그 설정
            if tags:
                self._set_tags_in_popup(tags)
            
            # 6. 팝업에서 공개 설정 (라디오 버튼)
            self._set_visibility_in_popup(publish_settings.get('visibility', 'public'))
            
            # 7. 발행 설정 옵션 (체크박스들)
            self._set_publish_options_in_popup(publish_settings)
            
            time.sleep(1)
            
            # 8. 팝업 내 최종 발행 버튼 클릭
            print("[INFO] [CDP] 최종 발행 버튼 검색...")
            
            final_publish_result = self._evaluate_js('''
            (function() {
                // 1순위: data-testid로 정확히 찾기
                const seOnePublishBtn = document.querySelector('[data-testid="seOnePublishBtn"]');
                if (seOnePublishBtn && seOnePublishBtn.offsetParent !== null) {
                    const rect = seOnePublishBtn.getBoundingClientRect();
                    seOnePublishBtn.click();
                    return {
                        found: true,
                        clicked: true,
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2,
                        container: 'data-testid=seOnePublishBtn'
                    };
                }
                
                // 2순위: confirm_btn 클래스로 찾기
                const confirmBtn = document.querySelector('button.confirm_btn__WEaBq');
                if (confirmBtn && confirmBtn.offsetParent !== null) {
                    const rect = confirmBtn.getBoundingClientRect();
                    confirmBtn.click();
                    return {
                        found: true,
                        clicked: true,
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2,
                        container: 'confirm_btn__WEaBq'
                    };
                }
                
                // 3순위: confirm_btn 패턴으로 찾기
                const confirmBtnPattern = document.querySelector('button[class*="confirm_btn"]');
                if (confirmBtnPattern && confirmBtnPattern.offsetParent !== null) {
                    const rect = confirmBtnPattern.getBoundingClientRect();
                    confirmBtnPattern.click();
                    return {
                        found: true,
                        clicked: true,
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2,
                        container: 'confirm_btn pattern'
                    };
                }
                
                // 4순위: 모든 '발행' 버튼 중 y좌표가 큰 것 (팝업 내부)
                const publishButtons = [];
                document.querySelectorAll('button').forEach(btn => {
                    const text = btn.textContent.trim();
                    if (text === '발행' && btn.offsetParent !== null) {
                        const rect = btn.getBoundingClientRect();
                        publishButtons.push({
                            element: btn,
                            rect: rect,
                            y: rect.top
                        });
                    }
                });
                
                if (publishButtons.length >= 2) {
                    publishButtons.sort((a, b) => b.y - a.y);
                    const btn = publishButtons[0];
                    btn.element.click();
                    return {
                        found: true,
                        clicked: true,
                        x: btn.rect.left + btn.rect.width / 2,
                        y: btn.rect.top + btn.rect.height / 2,
                        container: 'popup (lower button)',
                        buttonCount: publishButtons.length
                    };
                }
                
                return { found: false, buttonCount: publishButtons.length };
            })()
            ''')
            
            if not final_publish_result or not final_publish_result.get('found'):
                print("[ERROR] [CDP] 최종 발행 버튼을 찾을 수 없습니다.")
                self._debug_buttons()
                return False
            
            print(f"[INFO] [CDP] 최종 발행 버튼 발견 (container: {final_publish_result.get('container')})")
            
            # JavaScript에서 이미 클릭했으면 추가 클릭 불필요
            if final_publish_result.get('clicked'):
                print("[INFO] [CDP] 최종 발행 버튼 클릭 완료 (JS)")
            else:
                # CDP로 클릭
                self._cdp_click(final_publish_result['x'], final_publish_result['y'])
                print("[INFO] [CDP] 최종 발행 버튼 클릭 완료 (CDP)")
            
            time.sleep(3)
            self._handle_alert()
            
            # 발행 성공 확인
            current_url = self.driver.current_url
            print(f"[DEBUG] [CDP] 현재 URL: {current_url}")
            
            if "postwrite" not in current_url.lower() or "logNo" in current_url:
                print("[SUCCESS] [CDP] 글 발행 완료!")
                return True
            else:
                # 추가 확인
                time.sleep(2)
                current_url = self.driver.current_url
                if "postwrite" not in current_url.lower():
                    print("[SUCCESS] [CDP] 글 발행 완료!")
                    return True
                print("[WARNING] [CDP] 발행 상태 확인 필요")
                return True
                
        except Exception as e:
            print(f"[ERROR] [CDP] 글 발행 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _wait_for_publish_popup(self, timeout: int = 10) -> bool:
        """발행 설정 팝업이 나타날 때까지 대기"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self._evaluate_js('''
            (function() {
                // 발행 설정 팝업 확인
                const popupIndicators = [
                    '[class*="publish_layer"]',
                    '[class*="publishLayer"]',
                    '[class*="publish_setting"]',
                    '[class*="publish_popup"]',
                    // 팝업 내 특정 요소
                    '[class*="category"]',
                    '[class*="tag_input"]',
                    '[class*="공개"]'
                ];
                
                for (const sel of popupIndicators) {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) {
                        return { found: true, selector: sel };
                    }
                }
                
                // 버튼이 2개 이상인 발행 버튼 확인 (팝업 열림)
                let publishBtnCount = 0;
                document.querySelectorAll('button').forEach(btn => {
                    if (btn.textContent.trim() === '발행' && btn.offsetParent !== null) {
                        publishBtnCount++;
                    }
                });
                
                if (publishBtnCount >= 2) {
                    return { found: true, selector: 'multiple_publish_buttons' };
                }
                
                return { found: false };
            })()
            ''')
            
            if result and result.get('found'):
                print(f"[INFO] [CDP] 발행 팝업 감지: {result.get('selector')}")
                return True
            
            time.sleep(0.5)
        
        return False
    
    def _set_category_in_popup(self, category_name: str) -> bool:
        """발행 팝업 내에서 카테고리 설정"""
        try:
            print(f"[INFO] [CDP] 카테고리 설정: {category_name}")
            
            result = self._evaluate_js(f'''
            (function() {{
                // 카테고리 선택 드롭다운/버튼 찾기
                const categorySelectors = [
                    '[class*="category"] select',
                    '[class*="category"] button',
                    'select[class*="category"]',
                    '[class*="categorySelect"]'
                ];
                
                for (const sel of categorySelectors) {{
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) {{
                        el.click();
                        return {{ clicked: true, selector: sel }};
                    }}
                }}
                return {{ clicked: false }};
            }})()
            ''')
            
            if result and result.get('clicked'):
                time.sleep(0.5)
                
                # 카테고리 항목 선택
                self._evaluate_js(f'''
                (function() {{
                    const items = document.querySelectorAll('[class*="category"] li, [class*="category"] option, [role="option"]');
                    for (const item of items) {{
                        if (item.textContent.includes('{category_name}')) {{
                            item.click();
                            return true;
                        }}
                    }}
                    return false;
                }})()
                ''')
                time.sleep(0.3)
            
            return True
            
        except Exception as e:
            print(f"[WARNING] [CDP] 카테고리 설정 실패: {e}")
            return False
    
    def _set_tags_in_popup(self, tags: List[str]) -> bool:
        """발행 팝업 내에서 태그 설정 (띄어쓰기로 구분)"""
        try:
            # 태그를 띄어쓰기로 구분된 문자열로 변환
            tags_text = ' '.join(tags)
            print(f"[INFO] [CDP] 태그 설정: {tags_text}")
            
            # 태그 입력 필드 좌표 얻기
            tag_pos = self._evaluate_js('''
            (function() {
                const tagSelectors = [
                    'input[class*="tag_input"]',
                    'input[placeholder*="태그"]',
                    '[class*="tag"] input',
                    '.tag_input__rvUB5'
                ];
                
                for (const sel of tagSelectors) {
                    const input = document.querySelector(sel);
                    if (input && input.offsetParent !== null) {
                        const rect = input.getBoundingClientRect();
                        return { 
                            found: true, 
                            selector: sel,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2
                        };
                    }
                }
                return { found: false };
            })()
            ''')
            
            if tag_pos and tag_pos.get('found'):
                print(f"[DEBUG] [CDP] 태그 입력 영역 발견: {tag_pos.get('selector')}")
                
                # CDP로 태그 입력 영역 클릭
                self._cdp_click(tag_pos['x'], tag_pos['y'])
                time.sleep(0.3)
                
                # 태그를 하나씩 입력 (띄어쓰기가 구분자)
                for tag in tags:
                    time.sleep(0.2)
                    self._cdp_type_text(tag)
                    time.sleep(0.2)
                    # 스페이스로 태그 구분 (Enter 대신)
                    self._cdp_press_key("Space")
                
                print("[INFO] [CDP] 태그 입력 완료")
            else:
                print("[WARNING] [CDP] 태그 입력 영역을 찾지 못함")
            
            return True
            
        except Exception as e:
            print(f"[WARNING] [CDP] 태그 설정 실패: {e}")
            return False
    
    def _set_visibility_in_popup(self, visibility: str) -> bool:
        """발행 팝업 내에서 공개 설정 (라디오 버튼 클릭)"""
        try:
            # visibility: 'public', 'neighbor', 'mutual', 'private'
            visibility_map = {
                'public': '전체공개',
                'neighbor': '이웃공개',
                'mutual': '서로이웃공개',
                'private': '비공개'
            }
            visibility_text = visibility_map.get(visibility, '전체공개')
            print(f"[INFO] [CDP] 공개 설정 적용: {visibility_text}")
            
            # 공개 설정 라디오 버튼 좌표 얻기
            visibility_pos = self._evaluate_js(f'''
            (function() {{
                const targetText = '{visibility_text}';
                
                // 라디오 버튼 레이블 찾기
                const labels = document.querySelectorAll('label');
                for (const label of labels) {{
                    if (label.textContent.includes(targetText) && label.offsetParent !== null) {{
                        const rect = label.getBoundingClientRect();
                        return {{
                            found: true,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            element: 'label'
                        }};
                    }}
                }}
                
                // input[type="radio"] 찾기
                const radios = document.querySelectorAll('input[type="radio"]');
                for (const radio of radios) {{
                    const parent = radio.closest('label, div, span');
                    if (parent && parent.textContent.includes(targetText) && radio.offsetParent !== null) {{
                        const rect = radio.getBoundingClientRect();
                        return {{
                            found: true,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            element: 'radio'
                        }};
                    }}
                }}
                
                // span/div 텍스트로 찾기
                const elements = document.querySelectorAll('span, div');
                for (const el of elements) {{
                    if (el.textContent.trim() === targetText && el.offsetParent !== null) {{
                        const rect = el.getBoundingClientRect();
                        return {{
                            found: true,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            element: 'span/div'
                        }};
                    }}
                }}
                
                return {{ found: false }};
            }})()
            ''')
            
            if visibility_pos and visibility_pos.get('found'):
                print(f"[DEBUG] [CDP] 공개 설정 영역 발견: {visibility_pos.get('element')}")
                self._cdp_click(visibility_pos['x'], visibility_pos['y'])
                time.sleep(0.3)
                print(f"[INFO] [CDP] 공개 설정 클릭 완료: {visibility_text}")
            else:
                print(f"[WARNING] [CDP] 공개 설정 '{visibility_text}'을 찾지 못함, 기본값 유지")
            
            return True
            
        except Exception as e:
            print(f"[WARNING] [CDP] 공개 설정 실패: {e}")
            return True
    
    def _set_publish_options_in_popup(self, publish_settings: dict) -> bool:
        """발행 팝업 내에서 발행 설정 옵션들 설정 (체크박스 클릭)"""
        try:
            print("[INFO] [CDP] 발행 설정 옵션 적용 중...")
            
            # 체크박스 옵션 매핑 (네이버 블로그 기본값은 모두 체크되어 있음)
            # 기본값에서 해제하려면 클릭해야 함
            checkbox_options = [
                ('allow_comment', '댓글', '댓글허용', '댓글 허용'),
                ('allow_sympathy', '공감', '공감허용', '공감 허용'),
                ('allow_search', '검색', '검색허용', '검색 허용'),
                ('allow_external_share', '외부', '외부 공유', '외부공유', '외부 공유 허용'),
            ]
            
            for setting_key, *search_texts in checkbox_options:
                setting_value = publish_settings.get(setting_key, True)
                
                # 기본값(True)에서 False로 변경하려면 클릭하여 해제
                if not setting_value:
                    self._toggle_checkbox(search_texts, uncheck=True)
            
            # 블로그/카페 공유 설정 (드롭다운)
            blog_cafe_share = publish_settings.get('blog_cafe_share', 'link')
            if blog_cafe_share == 'content':
                # 본문 허용으로 변경
                self._set_blog_cafe_share_option('본문')
            elif blog_cafe_share == 'none':
                # 블로그/카페 공유 체크박스 해제
                self._toggle_checkbox(['블로그', '카페', '공유'], uncheck=True)
            
            # 공지사항 체크박스
            is_notice = publish_settings.get('is_notice', False)
            if is_notice:
                self._toggle_checkbox(['공지사항', '공지 사항', '공지'], check=True)
            
            print("[INFO] [CDP] 발행 설정 옵션 적용 완료")
            return True
            
        except Exception as e:
            print(f"[WARNING] [CDP] 발행 설정 옵션 적용 실패: {e}")
            return True
    
    def _toggle_checkbox(self, search_texts: list, check: bool = False, uncheck: bool = False) -> bool:
        """체크박스 토글 (check=True면 체크, uncheck=True면 해제)"""
        try:
            search_texts_js = str(search_texts)
            action = 'check' if check else 'uncheck' if uncheck else 'toggle'
            
            result = self._evaluate_js(f'''
            (function() {{
                const searchTexts = {search_texts_js};
                const action = '{action}';
                
                // 체크박스 또는 레이블 찾기
                const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                for (const cb of checkboxes) {{
                    const parent = cb.closest('label, div, li');
                    if (!parent) continue;
                    
                    const parentText = parent.textContent;
                    let matched = false;
                    
                    for (const text of searchTexts) {{
                        if (parentText.includes(text)) {{
                            matched = true;
                            break;
                        }}
                    }}
                    
                    if (matched && cb.offsetParent !== null) {{
                        // 현재 상태 확인
                        const isChecked = cb.checked;
                        
                        // 원하는 상태와 다르면 클릭
                        if ((action === 'check' && !isChecked) || 
                            (action === 'uncheck' && isChecked) ||
                            action === 'toggle') {{
                            const rect = cb.getBoundingClientRect();
                            return {{
                                found: true,
                                x: rect.left + rect.width / 2,
                                y: rect.top + rect.height / 2,
                                wasChecked: isChecked
                            }};
                        }}
                        return {{ found: true, noChange: true, isChecked: isChecked }};
                    }}
                }}
                
                // 레이블로 찾기
                const labels = document.querySelectorAll('label');
                for (const label of labels) {{
                    const labelText = label.textContent;
                    let matched = false;
                    
                    for (const text of searchTexts) {{
                        if (labelText.includes(text)) {{
                            matched = true;
                            break;
                        }}
                    }}
                    
                    if (matched && label.offsetParent !== null) {{
                        const rect = label.getBoundingClientRect();
                        return {{
                            found: true,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            element: 'label'
                        }};
                    }}
                }}
                
                return {{ found: false }};
            }})()
            ''')
            
            if result and result.get('found') and not result.get('noChange'):
                self._cdp_click(result['x'], result['y'])
                time.sleep(0.2)
                print(f"[DEBUG] [CDP] 체크박스 토글: {search_texts[0]}")
                return True
            
            return True
            
        except Exception as e:
            print(f"[WARNING] [CDP] 체크박스 토글 실패: {e}")
            return False
    
    def _set_blog_cafe_share_option(self, option_text: str) -> bool:
        """블로그/카페 공유 드롭다운 옵션 선택"""
        try:
            # 드롭다운 버튼 클릭
            dropdown_result = self._evaluate_js('''
            (function() {
                // 링크 허용/본문 허용 드롭다운 버튼 찾기
                const buttons = document.querySelectorAll('button, [class*="dropdown"], [class*="select"]');
                for (const btn of buttons) {
                    const text = btn.textContent;
                    if ((text.includes('링크') || text.includes('본문')) && 
                        text.includes('허용') && btn.offsetParent !== null) {
                        const rect = btn.getBoundingClientRect();
                        return {
                            found: true,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2
                        };
                    }
                }
                return { found: false };
            })()
            ''')
            
            if dropdown_result and dropdown_result.get('found'):
                self._cdp_click(dropdown_result['x'], dropdown_result['y'])
                time.sleep(0.3)
                
                # 옵션 선택
                option_result = self._evaluate_js(f'''
                (function() {{
                    const targetText = '{option_text}';
                    const options = document.querySelectorAll('li, option, [role="option"], [class*="item"]');
                    for (const opt of options) {{
                        if (opt.textContent.includes(targetText) && opt.offsetParent !== null) {{
                            const rect = opt.getBoundingClientRect();
                            return {{
                                found: true,
                                x: rect.left + rect.width / 2,
                                y: rect.top + rect.height / 2
                            }};
                        }}
                    }}
                    return {{ found: false }};
                }})()
                ''')
                
                if option_result and option_result.get('found'):
                    self._cdp_click(option_result['x'], option_result['y'])
                    time.sleep(0.2)
                    print(f"[DEBUG] [CDP] 블로그/카페 공유 옵션 선택: {option_text}")
            
            return True
            
        except Exception as e:
            print(f"[WARNING] [CDP] 블로그/카페 공유 옵션 설정 실패: {e}")
            return False
    
    def _verify_post_published(self, title: str) -> bool:
        """
        블로그 글목록에서 발행된 글 확인
        
        Args:
            title: 확인할 글 제목
            
        Returns:
            bool: 글이 발행되었으면 True
        """
        try:
            print(f"[INFO] [CDP] 발행 확인 중: '{title}'")
            time.sleep(3)
            
            # 1. 먼저 블로그 전체글 보기 페이지로 이동
            post_list_url = f"https://blog.naver.com/PostList.naver?blogId={self.blog_id}&from=postList&categoryNo=0"
            print(f"[INFO] [CDP] 글목록으로 이동: {post_list_url}")
            self.driver.get(post_list_url)
            time.sleep(4)
            
            # iframe 내부에서 제목 검색
            result = self._evaluate_js(f'''
            (function() {{
                const searchTitle = '{title}';
                
                // mainFrame iframe 접근
                const mainFrame = document.getElementById('mainFrame');
                if (mainFrame && mainFrame.contentDocument) {{
                    const frameDoc = mainFrame.contentDocument;
                    const frameText = frameDoc.body.innerText;
                    
                    // 제목이 포함되어 있는지 확인
                    if (frameText.includes(searchTitle)) {{
                        return {{ found: true, location: 'mainFrame', source: 'text' }};
                    }}
                    
                    // 글 목록 링크들에서 검색
                    const links = frameDoc.querySelectorAll('a');
                    for (const link of links) {{
                        const text = link.textContent.trim();
                        if (text.includes(searchTitle)) {{
                            return {{ found: true, location: 'mainFrame', source: 'link', title: text }};
                        }}
                    }}
                }}
                
                // 메인 문서에서도 검색
                if (document.body.innerText.includes(searchTitle)) {{
                    return {{ found: true, location: 'main', source: 'text' }};
                }}
                
                return {{ found: false }};
            }})()
            ''')
            
            if result and result.get('found'):
                print(f"[SUCCESS] [CDP] 글 발행 확인됨 - 위치: {result.get('location')}, 소스: {result.get('source')}")
                return True
            
            # 2. 블로그 메인 페이지에서 추가 확인
            blog_main_url = f"https://blog.naver.com/{self.blog_id}"
            print(f"[INFO] [CDP] 블로그 메인에서 재확인: {blog_main_url}")
            self.driver.get(blog_main_url)
            time.sleep(4)
            
            # 페이지 소스에서 직접 검색
            page_source = self.driver.page_source
            if title in page_source:
                print(f"[SUCCESS] [CDP] 블로그 메인에서 발견됨")
                return True
            
            # 3. iframe 내부에서 다시 확인
            result2 = self._evaluate_js(f'''
            (function() {{
                const searchTitle = '{title}';
                const mainFrame = document.getElementById('mainFrame');
                if (mainFrame && mainFrame.contentDocument) {{
                    const frameSource = mainFrame.contentDocument.body.innerHTML;
                    if (frameSource.includes(searchTitle)) {{
                        return {{ found: true }};
                    }}
                }}
                return {{ found: false }};
            }})()
            ''')
            
            if result2 and result2.get('found'):
                print(f"[SUCCESS] [CDP] iframe HTML에서 발견됨")
                return True
                
            print("[WARNING] [CDP] 글목록에서 해당 글을 찾을 수 없음")
            return False
                
        except Exception as e:
            print(f"[ERROR] [CDP] 발행 확인 실패: {e}")
            return False
    
    def _debug_buttons(self):
        """현재 페이지의 버튼 목록 출력 (디버깅용)"""
        result = self._evaluate_js('''
        (function() {
            const buttons = [];
            document.querySelectorAll('button').forEach(btn => {
                if (btn.offsetParent !== null) {
                    const rect = btn.getBoundingClientRect();
                    buttons.push({
                        text: btn.textContent.trim().substring(0, 30),
                        class: (btn.className || '').substring(0, 50),
                        x: Math.round(rect.left),
                        y: Math.round(rect.top)
                    });
                }
            });
            return buttons;
        })()
        ''')
        
        if result:
            print("[DEBUG] 현재 페이지 버튼 목록:")
            for btn in result[:15]:  # 최대 15개만 출력
                print(f"  - '{btn.get('text')}' | class: {btn.get('class')} | pos: ({btn.get('x')}, {btn.get('y')})")
    
    def analyze_page(self) -> dict:
        """페이지 분석 (디버깅용)"""
        return self._evaluate_js('''
        (function() {
            const result = {
                url: window.location.href,
                title: document.title,
                buttons: [],
                inputs: [],
                frames: []
            };
            
            // 버튼 정보
            document.querySelectorAll('button').forEach(btn => {
                if (btn.offsetParent !== null) {
                    result.buttons.push({
                        text: btn.textContent.trim().substring(0, 50),
                        class: btn.className.substring(0, 100)
                    });
                }
            });
            
            // 입력 필드
            document.querySelectorAll('input, [contenteditable="true"]').forEach(input => {
                if (input.offsetParent !== null) {
                    result.inputs.push({
                        tag: input.tagName,
                        type: input.type || 'contenteditable',
                        class: input.className.substring(0, 100)
                    });
                }
            });
            
            // iframe
            document.querySelectorAll('iframe').forEach(frame => {
                result.frames.push({
                    id: frame.id,
                    name: frame.name,
                    src: (frame.src || '').substring(0, 100)
                });
            });
            
            return result;
        })()
        ''')
