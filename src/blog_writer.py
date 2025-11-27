"""
네이버 블로그 자동 글쓰기 프로그램
블로그 글 작성 모듈
"""
import time
from typing import Optional, List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.common.action_chains import ActionChains

from src.config import Config


class NaverBlogWriter:
    """네이버 블로그 글 작성 클래스"""
    
    def __init__(self, driver, config: Config):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(driver, 20)
        self.blog_id = config.blog_id  # 별도 설정된 블로그 ID 사용
    
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
                   tags: Optional[List[str]] = None, is_public: bool = True) -> bool:
        """
        블로그 글 작성 및 발행
        
        Args:
            title: 글 제목
            content: 글 내용 (HTML 또는 텍스트)
            category: 카테고리 이름 (None이면 기본 카테고리)
            tags: 태그 리스트
            is_public: 공개 여부
            
        Returns:
            bool: 발행 성공 여부
        """
        print(f"[INFO] 블로그 글 작성 시작: {title}")
        
        try:
            # 글쓰기 페이지로 이동
            if not self._navigate_to_editor():
                return False
            
            # 제목 입력
            if not self._input_title(title):
                return False
            
            # 본문 내용 입력
            if not self._input_content(content):
                return False
            
            # 카테고리 설정
            if category:
                self._set_category(category)
            
            # 태그 추가
            if tags:
                self._add_tags(tags)
            
            # 공개 설정
            self._set_visibility(is_public)
            
            # 발행
            return self._publish()
            
        except UnexpectedAlertPresentException as e:
            self._handle_alert()
            print(f"[ERROR] 글 작성 중 알림창 오류: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] 글 작성 중 오류 발생: {e}")
            return False
    
    def _navigate_to_editor(self) -> bool:
        """글쓰기 에디터로 이동 - 블로그 메인에서 글쓰기 버튼 클릭"""
        try:
            # 알림창 처리
            self._handle_alert()
            
            # 블로그 메인 페이지로 이동
            blog_main_url = f"https://blog.naver.com/{self.blog_id}"
            print(f"[INFO] 블로그 메인 페이지로 이동: {blog_main_url}")
            self.driver.get(blog_main_url)
            time.sleep(4)
            self._handle_alert()
            
            # mainFrame iframe으로 전환 (네이버 블로그 구조)
            print("[INFO] mainFrame iframe으로 전환...")
            try:
                iframe = self.wait.until(
                    EC.presence_of_element_located((By.ID, "mainFrame"))
                )
                self.driver.switch_to.frame(iframe)
                print("[INFO] iframe 전환 성공!")
                time.sleep(2)
            except Exception as e:
                print(f"[WARNING] iframe 전환 실패: {e}")
            
            # 글쓰기 버튼 찾기 (iframe 내부)
            write_btn = None
            write_btn_selectors = [
                # 본문 영역의 이미지 글쓰기 버튼
                "img[alt='글쓰기']",
                "img[src*='img_write_btn']",
                # 사이드바의 텍스트 글쓰기 링크
                "a.col._checkBlock._rosRestrict",
                "a[href*='postwrite']",
                # 부모 a 태그 찾기
                "//img[@alt='글쓰기']/parent::a",
                "//img[contains(@src, 'img_write_btn')]/parent::a",
                # 텍스트로 찾기
                "//a[text()='글쓰기']",
                "//a[contains(text(), '글쓰기')]",
            ]
            
            for selector in write_btn_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for elem in elements:
                        if elem.is_displayed():
                            # img 태그인 경우 부모 a 태그 찾기
                            if elem.tag_name == 'img':
                                try:
                                    parent = elem.find_element(By.XPATH, "./..")
                                    if parent.tag_name == 'a':
                                        write_btn = parent
                                        print(f"[INFO] 글쓰기 이미지의 부모 링크 발견")
                                        break
                                except:
                                    pass
                            else:
                                write_btn = elem
                                print(f"[INFO] 글쓰기 버튼 발견: {selector}")
                                break
                    if write_btn:
                        break
                except Exception as e:
                    continue
            
            # default content로 복귀 (클릭 전)
            self.driver.switch_to.default_content()
            
            if write_btn:
                print("[INFO] 글쓰기 버튼 클릭...")
                # href 속성 가져와서 직접 이동 (iframe 내부 클릭 문제 방지)
                try:
                    href = write_btn.get_attribute("href")
                    if href:
                        print(f"[INFO] 글쓰기 URL로 이동: {href}")
                        self.driver.get(href)
                        time.sleep(3)
                        self._handle_alert()
                    else:
                        # href가 없으면 클릭 시도
                        self.driver.switch_to.frame(self.driver.find_element(By.ID, "mainFrame"))
                        self.driver.execute_script("arguments[0].click();", write_btn)
                        self.driver.switch_to.default_content()
                        time.sleep(3)
                        self._handle_alert()
                except Exception as e:
                    print(f"[WARNING] 클릭 실패, 직접 URL로 이동: {e}")
                    write_url = f"https://blog.naver.com/{self.blog_id}/postwrite"
                    self.driver.get(write_url)
                    time.sleep(3)
            else:
                # 글쓰기 버튼을 못 찾으면 직접 URL로 이동
                print("[WARNING] 글쓰기 버튼을 찾지 못했습니다. 직접 URL로 이동...")
                write_url = f"https://blog.naver.com/{self.blog_id}/postwrite"
                print(f"[INFO] 글쓰기 URL: {write_url}")
                self.driver.get(write_url)
                time.sleep(3)
                self._handle_alert()
            
            # 새 창/탭이 열렸는지 확인
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                time.sleep(2)
            
            # 에디터 로드 확인
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".se-title-text, .se-ff-system, .se-component, .se-content"))
                )
                print("[INFO] 에디터 로드 완료")
                return True
            except TimeoutException:
                print("[WARNING] 에디터 로드 대기 중...")
                time.sleep(3)
                return True
                
        except UnexpectedAlertPresentException:
            self._handle_alert()
            return self._navigate_to_editor()
        except Exception as e:
            print(f"[ERROR] 에디터 이동 실패: {e}")
            return False
    
    def _input_title(self, title: str) -> bool:
        """제목 입력"""
        try:
            print("[INFO] 제목 입력 중...")
            self._handle_alert()
            
            # 스마트에디터 ONE의 제목 입력 영역
            title_selectors = [
                ".se-title-text .se-text-paragraph span",
                ".se-title-text .se-text-paragraph",
                ".se-title-text",
                "span.se-ff-system.se-fs32",
                ".se-placeholder.__se_placeholder",
                "[contenteditable='true']"
            ]
            
            title_element = None
            for selector in title_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            title_element = elem
                            break
                    if title_element:
                        break
                except:
                    continue
            
            if not title_element:
                # placeholder 텍스트로 찾기
                try:
                    title_element = self.driver.find_element(
                        By.XPATH, "//*[contains(text(), '제목')]"
                    )
                except:
                    pass
            
            if title_element:
                # 클릭하여 포커스
                self.driver.execute_script("arguments[0].click();", title_element)
                time.sleep(0.5)
                
                # 제목 입력 - JavaScript로 직접 입력
                try:
                    self.driver.execute_script(
                        "arguments[0].textContent = arguments[1];", 
                        title_element, title
                    )
                except:
                    # ActionChains로 입력
                    actions = ActionChains(self.driver)
                    actions.send_keys(title)
                    actions.perform()
                
                print("[INFO] 제목 입력 완료")
                time.sleep(0.5)
                return True
            else:
                # 활성 요소에 직접 입력 시도
                print("[WARNING] 제목 영역을 찾지 못해 현재 포커스에 입력합니다.")
                actions = ActionChains(self.driver)
                actions.send_keys(title)
                actions.perform()
                return True
                
        except Exception as e:
            print(f"[ERROR] 제목 입력 실패: {e}")
            return False
    
    def _input_content(self, content: str) -> bool:
        """본문 내용 입력"""
        try:
            print("[INFO] 본문 입력 중...")
            self._handle_alert()
            
            # Tab을 눌러 본문 영역으로 이동
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.TAB)
            actions.perform()
            time.sleep(0.5)
            
            # 본문 영역 클릭 시도
            content_selectors = [
                ".se-component-content .se-text-paragraph",
                ".se-main-container .se-section-text .se-text-paragraph",
                ".se-section.se-section-text .se-text-paragraph",
                ".se-content .se-text-paragraph",
                ".se-text-paragraph"
            ]
            
            content_element = None
            for selector in content_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    # 본문 영역은 보통 두 번째 text-paragraph (첫번째는 제목)
                    if len(elements) > 1:
                        content_element = elements[1]
                    elif elements:
                        content_element = elements[0]
                    if content_element and content_element.is_displayed():
                        break
                except:
                    continue
            
            if content_element:
                try:
                    self.driver.execute_script("arguments[0].click();", content_element)
                    time.sleep(0.3)
                except:
                    pass
            
            # 내용을 줄 단위로 입력
            lines = content.split('\n')
            for i, line in enumerate(lines):
                actions = ActionChains(self.driver)
                actions.send_keys(line)
                if i < len(lines) - 1:
                    actions.send_keys(Keys.ENTER)
                actions.perform()
                time.sleep(0.1)
            
            print("[INFO] 본문 입력 완료")
            return True
            
        except Exception as e:
            print(f"[ERROR] 본문 입력 실패: {e}")
            return False
    
    def _set_category(self, category_name: str) -> bool:
        """카테고리 설정"""
        try:
            print(f"[INFO] 카테고리 설정: {category_name}")
            
            # 카테고리 선택 버튼 클릭
            category_btn_selectors = [
                ".se-category-btn",
                "button.category_btn",
                ".post_category"
            ]
            
            for selector in category_btn_selectors:
                try:
                    category_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    category_btn.click()
                    time.sleep(1)
                    break
                except:
                    continue
            
            # 카테고리 목록에서 선택
            try:
                categories = self.driver.find_elements(By.CSS_SELECTOR, ".se-category-item, .category_item")
                for cat in categories:
                    if category_name in cat.text:
                        cat.click()
                        print(f"[INFO] 카테고리 '{category_name}' 선택됨")
                        return True
            except:
                pass
            
            print(f"[WARNING] 카테고리 '{category_name}'를 찾을 수 없습니다.")
            return False
            
        except Exception as e:
            print(f"[WARNING] 카테고리 설정 실패: {e}")
            return False
    
    def _add_tags(self, tags: List[str]) -> bool:
        """태그 추가"""
        try:
            print(f"[INFO] 태그 추가: {tags}")
            
            # 태그 입력 영역 찾기
            tag_selectors = [
                ".se-tag-input input",
                "input.tag_input",
                "#post-tag-input"
            ]
            
            for selector in tag_selectors:
                try:
                    tag_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    for tag in tags:
                        tag_input.click()
                        tag_input.clear()
                        tag_input.send_keys(tag)
                        tag_input.send_keys(Keys.ENTER)
                        time.sleep(0.3)
                    
                    print("[INFO] 태그 추가 완료")
                    return True
                except:
                    continue
            
            print("[WARNING] 태그 입력 영역을 찾을 수 없습니다.")
            return False
            
        except Exception as e:
            print(f"[WARNING] 태그 추가 실패: {e}")
            return False
    
    def _set_visibility(self, is_public: bool) -> bool:
        """공개 설정"""
        try:
            visibility = "전체공개" if is_public else "비공개"
            print(f"[INFO] 공개 설정: {visibility}")
            
            # 공개 설정 버튼
            visibility_selectors = [
                ".se-publish-setting-btn",
                ".se-visibility-btn",
                "button.publish_setting"
            ]
            
            for selector in visibility_selectors:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    btn.click()
                    time.sleep(1)
                    
                    # 공개/비공개 옵션 선택
                    options = self.driver.find_elements(By.CSS_SELECTOR, ".se-popup-option, .publish_option")
                    for option in options:
                        if visibility in option.text:
                            option.click()
                            return True
                    break
                except:
                    continue
            
            return True  # 기본값 사용
            
        except Exception as e:
            print(f"[WARNING] 공개 설정 실패: {e}")
            return True
    
    def _publish(self) -> bool:
        """글 발행"""
        try:
            print("[INFO] 글 발행 중...")
            self._handle_alert()
            
            # 발행 버튼 찾기 - 다양한 선택자 시도
            publish_selectors = [
                # 스마트에디터 ONE 발행 버튼 (2024-2025 최신)
                "button.publish_btn__m9KHH",
                "button.publish_btn__W1ebR",
                "button.publish_btn__0bnz9",
                "button[class*='publish_btn__']",
                "button[class*='publish_btn']",
                # 발행 버튼 영역
                ".publish_btn_area__KjA2i button",
                "div[class*='publish_btn_area'] button",
                # 일반적인 발행 버튼
                ".se-publish-btn",
                "button.se-publish-btn",
                "button[class*='publish']",
                ".btn_publish",
                "#btn_publish",
                # 텍스트로 찾기
                "//button[contains(@class, 'publish')]",
                "//button[contains(text(), '발행')]",
                "//button[.//span[contains(text(), '발행')]]",
                "//span[text()='발행']/parent::button",
                "//div[text()='발행']/parent::button"
            ]
            
            publish_btn = None
            for selector in publish_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            publish_btn = elem
                            print(f"[DEBUG] 발행 버튼 발견: {selector}")
                            break
                    
                    if publish_btn:
                        break
                except:
                    continue
            
            if publish_btn:
                print("[INFO] 발행 버튼 발견, 클릭 중...")
                self.driver.execute_script("arguments[0].click();", publish_btn)
                time.sleep(3)
                
                # 발행 확인 팝업이 있다면 확인
                self._handle_alert()
                self._confirm_publish()
                
                # 발행 성공 확인 (URL 변경 또는 메시지 확인)
                time.sleep(2)
                current_url = self.driver.current_url
                if "postwrite" not in current_url.lower() or "logNo" in current_url:
                    print("[SUCCESS] 글 발행 완료!")
                    return True
                else:
                    print("[WARNING] 발행 후 페이지 변경 확인 필요")
                    return True
            else:
                print("[ERROR] 발행 버튼을 찾을 수 없습니다.")
                # 현재 페이지 스크린샷/HTML 저장 (디버깅용)
                print(f"[DEBUG] 현재 URL: {self.driver.current_url}")
                
                # 모든 버튼 출력 (디버깅)
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                print(f"[DEBUG] 페이지 내 버튼 수: {len(all_buttons)}")
                for btn in all_buttons[:10]:
                    try:
                        if btn.is_displayed():
                            print(f"  - Text: '{btn.text}', Class: {btn.get_attribute('class')[:50] if btn.get_attribute('class') else 'None'}")
                    except:
                        pass
                return False
                
        except UnexpectedAlertPresentException:
            self._handle_alert()
            return self._publish()
        except Exception as e:
            print(f"[ERROR] 글 발행 실패: {e}")
            return False
            
        except Exception as e:
            print(f"[ERROR] 글 발행 실패: {e}")
            return False
    
    def _confirm_publish(self):
        """발행 확인 팝업 처리"""
        try:
            time.sleep(2)
            
            # 발행 설정 팝업에서 "발행" 또는 "확인" 버튼 클릭
            confirm_selectors = [
                # 스마트에디터 ONE 발행 확인 팝업 버튼
                "button[class*='confirm_btn']",
                "button[class*='publish_layer'] button",
                ".publish_layer button[class*='confirm']",
                "div[class*='publish_popup'] button",
                "div[class*='layer'] button[class*='publish']",
                # 일반적인 확인 버튼
                ".se-popup-button-confirm",
                ".confirm_btn",
                "button.confirm",
                # 팝업 내 발행 버튼 (최종 발행)
                "//div[contains(@class, 'layer')]//button[contains(text(), '발행')]",
                "//div[contains(@class, 'popup')]//button[contains(text(), '발행')]",
                "//button[contains(text(), '확인')]",
                "//button[contains(text(), '발행')]",
            ]
            
            for selector in confirm_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            text = elem.text.strip()
                            if text in ['발행', '확인', '등록', 'Publish', 'OK']:
                                print(f"[INFO] 발행 확인 버튼 클릭: {text}")
                                self.driver.execute_script("arguments[0].click();", elem)
                                time.sleep(2)
                                return
                except:
                    continue
                    
        except Exception as e:
            print(f"[DEBUG] 발행 확인 팝업 처리: {e}")
            pass  # 팝업이 없을 수도 있음
