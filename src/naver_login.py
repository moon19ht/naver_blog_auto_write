"""
네이버 블로그 자동 글쓰기 프로그램
네이버 로그인 모듈

네이버는 자동화 탐지가 강력하므로, 여러 방법을 사용하여 로그인합니다:
1. 일반 로그인 시도
2. pyperclip + pyautogui를 이용한 클립보드 방식 로그인
"""
import time
import platform
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.config import Config

# 플랫폼에 따른 모듈 임포트 (지연 로딩)
CLIPBOARD_AVAILABLE = False
pyperclip = None
pyautogui = None

def _get_tkinter_install_hint() -> str:
    """OS별 tkinter 설치 힌트 반환"""
    import distro
    try:
        distro_id = distro.id().lower()
    except:
        distro_id = ""
    
    if distro_id in ['arch', 'manjaro', 'endeavouros', 'artix', 'garuda']:
        return "sudo pacman -S tk"
    elif distro_id in ['fedora', 'rhel', 'centos', 'rocky', 'almalinux']:
        return "sudo dnf install python3-tkinter"
    elif distro_id in ['opensuse', 'suse']:
        return "sudo zypper install python3-tk"
    else:
        # Debian/Ubuntu 계열 기본값
        return "sudo apt-get install python3-tk python3-dev"

def _load_clipboard_modules():
    """클립보드 관련 모듈을 지연 로딩"""
    global CLIPBOARD_AVAILABLE, pyperclip, pyautogui
    if pyperclip is not None:
        return CLIPBOARD_AVAILABLE
    
    try:
        import pyperclip as _pyperclip
        # pyautogui 임포트 전에 DISPLAY 환경변수 확인 (headless 환경 감지)
        import os
        display = os.environ.get('DISPLAY')
        wayland = os.environ.get('WAYLAND_DISPLAY')
        
        # tkinter 의존성 확인을 위해 먼저 테스트
        try:
            import tkinter
        except ImportError as tk_err:
            install_hint = _get_tkinter_install_hint()
            print(f"[WARNING] tkinter가 설치되지 않았습니다.")
            print(f"[INFO] 설치 명령어: {install_hint}")
            # tkinter 없이도 pyautogui 일부 기능은 사용 가능
        
        import pyautogui as _pyautogui
        pyperclip = _pyperclip
        pyautogui = _pyautogui
        CLIPBOARD_AVAILABLE = True
        
    except ImportError as e:
        print(f"[WARNING] 클립보드 모듈 로드 실패: {e}")
        CLIPBOARD_AVAILABLE = False
    except Exception as e:
        # pyautogui가 headless 환경에서 실패하는 경우 처리
        if "MouseInfo" in str(e) or "tkinter" in str(e).lower():
            install_hint = _get_tkinter_install_hint()
            print(f"[WARNING] pyautogui 초기화 실패 (tkinter 필요)")
            print(f"[INFO] 설치 명령어: {install_hint}")
        else:
            print(f"[WARNING] 클립보드 모듈 초기화 실패: {e}")
        CLIPBOARD_AVAILABLE = False
    
    return CLIPBOARD_AVAILABLE


class NaverLogin:
    """네이버 로그인 클래스"""
    
    NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"
    NAVER_MAIN_URL = "https://www.naver.com"
    
    def __init__(self, driver, config: Config):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(driver, 20)
        
        # 로그인 페이지 요소 선택자 (여러 버전 지원)
        self.selectors = {
            'id_input': ['#id', 'input[name="id"]', 'input[placeholder*="아이디"]', 'input[placeholder*="ID"]'],
            'pw_input': ['#pw', 'input[name="pw"]', 'input[type="password"]'],
            'login_btn': ['#log\\.login', '.btn_login', 'button[type="submit"]', '.btn_global']
        }
    
    def _find_element_by_selectors(self, selector_list: list, timeout: int = 10):
        """여러 선택자 중 첫 번째로 찾은 요소 반환"""
        for selector in selector_list:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if element:
                    return element
            except:
                continue
        return None
    
    def login(self) -> bool:
        """
        네이버 로그인 실행
        
        Returns:
            bool: 로그인 성공 여부
        """
        print("[INFO] 네이버 로그인을 시작합니다...")
        
        try:
            # 로그인 페이지로 이동
            self.driver.get(self.NAVER_LOGIN_URL)
            time.sleep(2)
            
            # 클립보드 모듈 로드 시도
            clipboard_available = _load_clipboard_modules()
            
            # 클립보드 방식 로그인 시도 (자동화 탐지 우회)
            if clipboard_available and not self.config.headless:
                success = self._login_with_clipboard()
            else:
                # 일반 방식 로그인 시도
                success = self._login_direct()
            
            if success:
                print("[SUCCESS] 네이버 로그인 성공!")
                return True
            else:
                print("[WARNING] 로그인 확인이 필요합니다. 수동으로 로그인해주세요.")
                return self._wait_for_manual_login()
                
        except Exception as e:
            print(f"[ERROR] 로그인 중 오류 발생: {e}")
            return False
    
    def _login_with_clipboard(self) -> bool:
        """
        클립보드를 이용한 로그인 (자동화 탐지 우회)
        pyperclip과 pyautogui를 사용하여 클립보드 복사/붙여넣기로 입력
        """
        try:
            print("[INFO] 클립보드 방식으로 로그인 시도...")
            
            # 아이디 입력 필드 찾기 (여러 선택자 시도)
            id_input = self._find_element_by_selectors(self.selectors['id_input'])
            if not id_input:
                print("[WARNING] 아이디 입력 필드를 찾을 수 없습니다.")
                return False
            
            id_input.click()
            time.sleep(0.5)
            
            # 클립보드에 아이디 복사 후 붙여넣기
            pyperclip.copy(self.config.naver_id)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            
            # 비밀번호 입력 필드 찾기
            pw_input = self._find_element_by_selectors(self.selectors['pw_input'])
            if not pw_input:
                print("[WARNING] 비밀번호 입력 필드를 찾을 수 없습니다.")
                return False
            
            pw_input.click()
            time.sleep(0.5)
            
            # 클립보드에 비밀번호 복사 후 붙여넣기
            pyperclip.copy(self.config.naver_pw)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            
            # 클립보드 초기화 (보안)
            pyperclip.copy('')
            
            # 로그인 버튼 찾기 및 클릭
            login_btn = self._find_element_by_selectors(self.selectors['login_btn'])
            if login_btn:
                login_btn.click()
            else:
                # Enter 키로 로그인 시도
                pyautogui.press('enter')
            
            time.sleep(3)
            
            return self._check_login_success()
            
        except Exception as e:
            print(f"[WARNING] 클립보드 방식 로그인 실패: {e}")
            return False
    
    def _login_direct(self) -> bool:
        """
        직접 입력 방식 로그인 (CDP + JavaScript 사용)
        여러 선택자를 시도하고 CDP로 텍스트 입력
        """
        try:
            print("[INFO] 직접 입력 방식으로 로그인 시도...")
            
            # 아이디 입력 필드 찾기 (여러 선택자 시도)
            id_input = self._find_element_by_selectors(self.selectors['id_input'])
            if not id_input:
                print("[ERROR] 아이디 입력 필드를 찾을 수 없습니다.")
                return False
            
            # 아이디 입력 - CDP 방식
            id_input.click()
            time.sleep(0.3)
            self._input_text_cdp(self.config.naver_id)
            time.sleep(0.5)
            
            # 비밀번호 입력 필드 찾기
            pw_input = self._find_element_by_selectors(self.selectors['pw_input'])
            if not pw_input:
                print("[ERROR] 비밀번호 입력 필드를 찾을 수 없습니다.")
                return False
            
            # 비밀번호 입력 - CDP 방식
            pw_input.click()
            time.sleep(0.3)
            self._input_text_cdp(self.config.naver_pw)
            time.sleep(0.5)
            
            # 로그인 버튼 찾기 및 클릭
            login_btn = self._find_element_by_selectors(self.selectors['login_btn'])
            if not login_btn:
                # Enter 키로 로그인 시도
                print("[INFO] 로그인 버튼을 찾을 수 없어 Enter 키로 시도합니다.")
                pw_input.send_keys(Keys.RETURN)
            else:
                login_btn.click()
            
            time.sleep(3)
            
            return self._check_login_success()
            
        except Exception as e:
            print(f"[WARNING] 직접 입력 방식 로그인 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _input_text_cdp(self, text: str):
        """CDP를 사용하여 텍스트 입력 (자동화 탐지 우회)"""
        try:
            # Chrome DevTools Protocol의 Input.insertText 사용
            self.driver.execute_cdp_cmd("Input.insertText", {"text": text})
        except Exception as e:
            # CDP 실패 시 JavaScript로 대체
            print(f"[WARNING] CDP 입력 실패, JavaScript로 대체: {e}")
            active_element = self.driver.switch_to.active_element
            # 현재 활성화된 요소에 값 입력
            self.driver.execute_script(
                "arguments[0].value = arguments[1]; "
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true})); "
                "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                active_element, text
            )
    
    def _check_login_success(self) -> bool:
        """로그인 성공 여부 확인"""
        try:
            # URL 확인 - 로그인 페이지를 벗어났는지
            current_url = self.driver.current_url
            
            # 캡차나 추가 인증이 필요한 경우
            if "captcha" in current_url.lower() or "protect" in current_url.lower():
                print("[WARNING] 캡차 또는 추가 인증이 필요합니다.")
                return False
            
            # 로그인 성공 시 리다이렉트되는 페이지 확인
            if "nidlogin" not in current_url:
                return True
            
            # 에러 메시지 확인
            try:
                error_msg = self.driver.find_element(By.CLASS_NAME, "error_message")
                if error_msg.is_displayed():
                    print(f"[ERROR] 로그인 실패: {error_msg.text}")
                    return False
            except NoSuchElementException:
                pass
            
            return False
            
        except Exception as e:
            print(f"[WARNING] 로그인 확인 중 오류: {e}")
            return False
    
    def _wait_for_manual_login(self, timeout: int = 300) -> bool:
        """
        수동 로그인 대기
        사용자가 직접 로그인할 때까지 대기
        """
        print(f"[INFO] {timeout}초 동안 수동 로그인을 기다립니다...")
        print("[INFO] 브라우저에서 직접 로그인해주세요.")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if "nidlogin" not in self.driver.current_url:
                print("[SUCCESS] 수동 로그인 감지!")
                return True
            time.sleep(2)
        
        print("[ERROR] 로그인 시간 초과")
        return False
    
    def is_logged_in(self) -> bool:
        """현재 로그인 상태 확인"""
        try:
            self.driver.get(self.NAVER_MAIN_URL)
            time.sleep(2)
            
            # 로그인 버튼이 보이면 로그아웃 상태
            try:
                login_btn = self.driver.find_element(By.CLASS_NAME, "MyView-module__link_login___HpHMW")
                return False
            except NoSuchElementException:
                return True
                
        except Exception:
            return False
