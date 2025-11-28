# Copilot Instructions - 네이버 블로그 자동 글쓰기

## 프로젝트 개요

네이버 블로그에 자동으로 로그인하고 글을 작성하는 Selenium 기반 자동화 프로그램입니다. 네이버의 자동화 탐지를 우회하기 위한 다양한 기법이 적용되어 있습니다.

## 아키텍처

```
main.py (진입점)
├── src/config.py        → 환경변수 기반 설정 (@dataclass)
├── src/driver.py        → WebDriver 생성 (Chrome/Edge/Firefox, WSL 지원)
├── src/naver_login.py   → 로그인 (클립보드 우회 방식)
├── src/blog_writer.py   → Selenium 직접 조작 방식
└── src/blog_writer_cdp.py → CDP 기반 조작 (권장, 1400+ lines)
```

## 핵심 패턴

### 1. 글쓰기 모드 선택 (CDP vs Selenium)
- **CDP 모드 (`blog_writer_cdp.py`)**: Chrome DevTools Protocol 사용, 더 안정적
- **Selenium 모드 (`blog_writer.py`)**: 기존 방식, 단순한 케이스에 사용
- `WRITER_MODE=cdp` 환경변수 또는 `--mode cdp` 옵션으로 선택

### 2. 자동화 탐지 우회 기법
```python
# 클립보드 방식 입력 (naver_login.py)
pyperclip.copy(self.config.naver_id)
pyautogui.hotkey('ctrl', 'v')

# CDP 직접 텍스트 입력 (blog_writer_cdp.py)
self._execute_cdp("Input.insertText", {"text": text})
```

### 3. 네이버 에디터 iframe 구조 처리
네이버 블로그는 중첩 iframe 구조를 사용합니다:
```python
# mainFrame으로 전환 후 작업
iframe = self.wait.until(EC.presence_of_element_located((By.ID, "mainFrame")))
self.driver.switch_to.frame(iframe)
# 작업 후 복귀
self.driver.switch_to.default_content()
```

### 4. CDP 명령 실행 패턴
```python
def _execute_cdp(self, cmd: str, params: dict = None):
    return self.driver.execute_cdp_cmd(cmd, params)

# JavaScript 평가
self._execute_cdp("Runtime.evaluate", {"expression": js_code, "returnByValue": True})

# 마우스 클릭
self._execute_cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y})
```

## 개발 워크플로우

### 실행
```bash
# 가상환경 활성화
source venv/bin/activate

# 대화형 모드
python main.py

# 명령줄 모드
python main.py --title "제목" --content "내용" --mode cdp
```

### 환경 설정
`.env` 파일 필수 설정:
```env
NAVER_ID=your_id
NAVER_PW=your_password
WRITER_MODE=cdp  # 권장
```

## 주의사항

1. **헤드리스 모드 제한**: `HEADLESS=True`는 클립보드 방식 불가, 탐지 확률 증가
2. **알림창 처리**: 모든 주요 작업 전후로 `_handle_alert()` 호출 필요
3. **재시도 로직**: `write_post()`는 `max_retries` 파라미터로 자동 재시도 지원
4. **발행 확인**: `_verify_post_published()`로 실제 발행 여부 검증

## 디버깅

- 분석용 HTML 저장 파일: `blog_page.html`, `editor_page.html`, `blog_iframe.html`
- 분석 스크립트: `analyze_blog.py`, `analyze_editor.py`, `analyze_iframe.py`
