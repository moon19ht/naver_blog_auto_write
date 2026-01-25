# 네이버 블로그 자동 포스팅 아키텍처

## 1. 개요

### 1.1 프로젝트 목적
네이버 블로그에 자동으로 글을 작성하고 발행하는 Python 기반 자동화 도구입니다. 네이버의 자동화 탐지를 우회하기 위해 Chrome DevTools Protocol(CDP)을 활용합니다.

### 1.2 기술 스택
| 기술 | 용도 |
|------|------|
| Python 3.x | 메인 언어 |
| Selenium | WebDriver 제어 |
| Chrome DevTools Protocol (CDP) | 자동화 탐지 우회 |
| webdriver-manager | 드라이버 자동 관리 |
| python-dotenv | 환경변수 관리 |

### 1.3 핵심 기능
- CDP 기반 텍스트 입력 (자동화 탐지 우회)
- 발행 설정 (카테고리, 태그, 공개범위)
- 재시도 로직 내장
- Headless 모드 지원 (SSH 환경)

---

## 2. 시스템 아키텍처

### 2.1 디렉토리 구조
```
naver_blog_auto_write/
├── main.py                    # 진입점, CLI 파싱
├── requirements.txt           # 의존성
├── .env.example               # 환경변수 템플릿
├── run.sh                     # Bash 래퍼 (display 환경 처리)
│
├── src/
│   ├── __init__.py
│   ├── config.py              # 설정 데이터클래스 (62줄)
│   ├── driver.py              # WebDriver 팩토리 (223줄)
│   ├── naver_login.py         # 로그인 처리 (340줄)
│   ├── blog_writer.py         # Selenium 포스팅 - 레거시 (595줄)
│   └── blog_writer_cdp.py     # CDP 포스팅 - 권장 (1453줄)
│
└── docs/
    └── ARCHITECTURE.md        # 본 문서
```

### 2.2 모듈 의존성
```
main.py
   │
   ├─→ src/config.py        (설정 로드)
   │
   ├─→ src/driver.py        (WebDriver 생성)
   │
   ├─→ src/naver_login.py   (로그인 - 본 문서 범위 외)
   │
   └─→ src/blog_writer_cdp.py  (자동 포스팅 - 핵심)
       또는
       src/blog_writer.py      (자동 포스팅 - 레거시)
```

---

## 3. 자동 포스팅 흐름

### 3.1 전체 흐름도
```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                               │
│  1. CLI 인자 파싱 (--title, --content, --mode)              │
│  2. Config 로드 (.env)                                       │
│  3. WebDriver 생성                                           │
│  4. 로그인 (본 문서 범위 외)                                 │
│  5. Writer 모드 결정 (CDP 또는 Selenium)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               NaverBlogWriterCDP.write_post()               │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 재시도 루프 (max_retries)                           │    │
│  │                                                      │    │
│  │  1. _navigate_to_editor()    에디터 페이지 이동     │    │
│  │           ↓                                          │    │
│  │  2. _handle_draft_popup()    임시저장 팝업 처리     │    │
│  │           ↓                                          │    │
│  │  3. _close_help_popup()      도움말 팝업 닫기       │    │
│  │           ↓                                          │    │
│  │  4. _input_title(title)      제목 입력 (CDP)        │    │
│  │           ↓                                          │    │
│  │  5. _input_content(content)  본문 입력 (CDP)        │    │
│  │           ↓                                          │    │
│  │  6. _publish()               발행 처리               │    │
│  │           ↓                                          │    │
│  │  7. _verify_post_published() 발행 검증              │    │
│  │                                                      │    │
│  │  성공 → return True                                  │    │
│  │  실패 → 재시도 또는 return False                    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 단계별 상세 설명

#### 3.2.1 에디터 네비게이션
**메서드**: `_navigate_to_editor()` (blog_writer_cdp.py:385-452)

```python
# 흐름
1. 블로그 메인 페이지 이동
   → https://blog.naver.com/{blog_id}

2. 글쓰기 버튼 URL 추출 (mainFrame iframe 내부)
   → JavaScript로 iframe contentDocument 접근
   → img[src*="img_write_btn"] 또는 "글쓰기" 링크 탐색

3. 에디터 페이지 이동
   → https://blog.naver.com/{blog_id}/postwrite

4. 에디터 로드 대기
   → SmartEditor ONE 컨테이너 (.se-body) 확인
   → 편집 가능 요소 ([contenteditable="true"]) 확인
```

#### 3.2.2 팝업 처리
**임시저장 팝업**: `_handle_draft_popup()` (blog_writer_cdp.py:220-282)
```python
# "작성 중인 글이 있습니다" 모달 처리
→ "작성 취소" 또는 "새로 작성" 버튼 클릭
```

**도움말 팝업**: `_close_help_popup()` (blog_writer_cdp.py:284-383)
```python
# 우측 도움말 패널 닫기
→ 닫기 버튼 탐색 (class*="close", aria-label*="닫기")
→ ESC 키 전송
```

#### 3.2.3 제목 입력
**메서드**: `_input_title()` (blog_writer_cdp.py:482-546)

```python
# 흐름
1. 제목 영역 탐색
   → .se-text-paragraph[placeholder="제목"]
   → JavaScript로 좌표 추출

2. CDP 클릭
   → Input.dispatchMouseEvent (좌표 기반)

3. CDP 텍스트 입력
   → Input.insertText (자동화 탐지 우회)
```

#### 3.2.4 본문 입력
**메서드**: `_input_content()` (blog_writer_cdp.py:548-620)

```python
# 흐름
1. 본문 영역 탐색
   → 제목이 아닌 .se-text-paragraph 요소
   → JavaScript로 좌표 추출

2. CDP 클릭 (더블클릭으로 포커스 확보)

3. CDP 텍스트 입력
   → Input.insertText
   → 멀티라인 지원
```

#### 3.2.5 발행 처리
**메서드**: `_publish()` (blog_writer_cdp.py:622-862)

```python
# 2단계 버튼 클릭 구조

┌────────────────────────────────────────────┐
│ 1단계: 헤더 발행 버튼                       │
│                                             │
│  위치: 상단 헤더 영역 (y < 100)             │
│  셀렉터: .publish_btn_area__KjA2i button   │
│  텍스트: "발행"                             │
│                                             │
│  클릭 → 발행 설정 팝업 열림                 │
└─────────────────┬──────────────────────────┘
                  ↓
┌────────────────────────────────────────────┐
│ 발행 설정 팝업                              │
│                                             │
│  _set_category_in_popup()   카테고리 선택  │
│  _set_tags_in_popup()       태그 입력      │
│  _set_visibility_in_popup() 공개범위 설정  │
│  _set_publish_options_in_popup() 기타 옵션 │
└─────────────────┬──────────────────────────┘
                  ↓
┌────────────────────────────────────────────┐
│ 2단계: 팝업 내 확인 버튼                    │
│                                             │
│  셀렉터: [data-testid="seOnePublishBtn"]   │
│  또는: button.confirm_btn__WEaBq           │
│                                             │
│  클릭 → 최종 발행 실행                      │
└────────────────────────────────────────────┘
```

#### 3.2.6 발행 검증
**메서드**: `_verify_post_published()` (blog_writer_cdp.py:1287-1382)

```python
# 다단계 검증 전략

Stage 1: 게시글 목록 페이지
  → blog.naver.com/PostList.naver?blogId={id}
  → mainFrame iframe 내 제목 검색

Stage 2: 블로그 메인 페이지
  → blog.naver.com/{blog_id}
  → page_source에서 제목 문자열 검색

Stage 3: iframe HTML 재검사
  → contentDocument.innerText/innerHTML 검색

어느 단계에서든 제목 발견 → return True
모든 단계 실패 → return False (재시도 트리거)
```

---

## 4. CDP 핵심 메서드

### 4.1 CDP 명령 실행 구조
```python
class NaverBlogWriterCDP:
    def _execute_cdp(self, cmd: str, params: dict = None):
        """CDP 명령 실행 래퍼"""
        return self.driver.execute_cdp_cmd(cmd, params or {})
```

### 4.2 주요 CDP 메서드

| 메서드 | 위치 | CDP 명령 | 용도 |
|--------|------|----------|------|
| `_execute_cdp()` | :30-34 | - | CDP 명령 래퍼 |
| `_evaluate_js()` | :36-47 | `Runtime.evaluate` | JavaScript 실행 |
| `_cdp_click()` | :49-70 | `Input.dispatchMouseEvent` | 좌표 기반 클릭 |
| `_cdp_type_text()` | :72-79 | `Input.insertText` | 텍스트 입력 |
| `_cdp_press_key()` | :81-99 | `Input.dispatchKeyEvent` | 키 입력 |
| `_get_element_center()` | :101-117 | `Runtime.evaluate` | 요소 좌표 추출 |

### 4.3 CDP 클릭 vs Selenium 클릭
```python
# CDP 클릭 (권장)
def _cdp_click(self, x: int, y: int) -> bool:
    self._execute_cdp("Input.dispatchMouseEvent", {
        "type": "mousePressed",
        "x": x, "y": y,
        "button": "left",
        "clickCount": 1
    })
    time.sleep(0.05)
    self._execute_cdp("Input.dispatchMouseEvent", {
        "type": "mouseReleased",
        "x": x, "y": y,
        "button": "left"
    })

# Selenium 클릭 (레거시)
element.click()  # 자동화 탐지에 취약
```

### 4.4 CDP 텍스트 입력 vs Selenium send_keys
```python
# CDP 텍스트 입력 (권장) - 자동화 탐지 우회
def _cdp_type_text(self, text: str) -> bool:
    self._execute_cdp("Input.insertText", {"text": text})

# Selenium send_keys (레거시) - 탐지 가능
element.send_keys(text)
```

---

## 5. CDP vs Selenium 모드 비교

### 5.1 기능 비교표
| 항목 | Selenium 모드 | CDP 모드 |
|------|---------------|----------|
| **파일** | blog_writer.py | blog_writer_cdp.py |
| **코드량** | 595줄 | 1453줄 |
| **텍스트 입력** | `send_keys()` | `Input.insertText` |
| **클릭 방식** | `element.click()` | `Input.dispatchMouseEvent` |
| **Headless** | 미지원 (클립보드 필요) | 완전 지원 |
| **자동화 탐지** | 취약 | 강함 |
| **재시도 로직** | 없음 | 내장 (`max_retries`) |
| **발행 설정** | 공개범위만 | 전체 옵션 |
| **SSH/원격** | 미지원 | 권장 |
| **안정성** | 중 | 높음 |

### 5.2 모드 선택 로직
```python
# main.py에서의 모드 결정
if config.remote_mode:
    writer_mode = 'cdp'  # SSH 환경에서 자동 CDP
elif args.mode:
    writer_mode = args.mode  # CLI 인자 우선
else:
    writer_mode = config.writer_mode  # .env 설정

# Headless 모드면 CDP 강제
if config.headless:
    writer_mode = 'cdp'  # 클립보드 사용 불가
```

### 5.3 권장 사용 시나리오
| 시나리오 | 권장 모드 |
|----------|-----------|
| SSH/원격 서버 | CDP |
| Headless 실행 | CDP |
| GUI 환경 + 안정성 필요 | CDP |
| 간단한 테스트 | Selenium |
| 레거시 호환성 | Selenium |

---

## 6. 설정 시스템

### 6.1 Config 데이터클래스
```python
# src/config.py
@dataclass
class Config:
    naver_id: str           # 필수: 네이버 ID
    naver_pw: str           # 필수: 네이버 비밀번호
    browser_type: str       # 'chrome', 'edge', 'firefox'
    headless: bool          # Headless 모드
    blog_id: str            # 블로그 ID (기본: naver_id)
    blog_category: str      # 기본 카테고리 (기본: '일상')
    writer_mode: str        # 'cdp' 또는 'selenium'
    remote_mode: bool       # SSH 모드 (자동 headless+CDP)
```

### 6.2 환경변수 (.env)
```bash
# 필수
NAVER_ID=your_id
NAVER_PW=your_password

# 선택 (기본값 있음)
BROWSER_TYPE=chrome      # chrome, edge, firefox
HEADLESS=False           # True/False
WRITER_MODE=cdp          # cdp, selenium
REMOTE_MODE=False        # True/False
BLOG_ID=                 # 비워두면 NAVER_ID 사용
BLOG_CATEGORY=일상       # 기본 카테고리
```

### 6.3 설정 우선순위
```
CLI 인자 > REMOTE_MODE 설정 > .env 파일 > 기본값
```

---

## 7. 발행 설정 옵션

### 7.1 publish_settings 구조
```python
publish_settings = {
    'visibility': 'public',      # 공개범위
    'allow_comment': True,       # 댓글 허용
    'allow_sympathy': True,      # 공감 허용
    'allow_search': True,        # 검색 허용
    'blog_cafe_share': 'link',   # 블로그/카페 공유
    'allow_external_share': True, # 외부 공유 허용
    'is_notice': False           # 공지사항 지정
}
```

### 7.2 공개범위 옵션
| 값 | 한글 | 설명 |
|-----|------|------|
| `public` | 전체공개 | 모든 사용자 |
| `neighbor` | 이웃공개 | 이웃만 |
| `mutual` | 서로이웃공개 | 서로이웃만 |
| `private` | 비공개 | 본인만 |

### 7.3 블로그/카페 공유 옵션
| 값 | 설명 |
|-----|------|
| `link` | 링크만 공유 |
| `content` | 본문 포함 공유 |
| `none` | 공유 안함 |

---

## 8. 주요 설계 패턴

### 8.1 재시도 패턴
```python
def write_post(self, ..., max_retries: int = 2) -> bool:
    for attempt in range(max_retries + 1):
        try:
            if not self._navigate_to_editor():
                continue  # 재시도
            if not self._input_title(title):
                continue  # 재시도
            # ... 각 단계 실패 시 재시도
            return True  # 성공
        except Exception:
            if attempt < max_retries:
                continue  # 재시도
            return False
    return False
```

### 8.2 다중 셀렉터 폴백
```python
# 여러 셀렉터 시도로 UI 변경에 대응
selectors = [
    '[data-testid="seOnePublishBtn"]',
    'button.confirm_btn__WEaBq',
    'button[class*="confirm_btn"]'
]
for selector in selectors:
    element = self._find_element(selector)
    if element:
        break
```

### 8.3 JavaScript 기반 요소 탐지
```python
# Runtime.evaluate로 동적 DOM 탐색
js_code = """
    const elements = document.querySelectorAll('.se-text-paragraph');
    for (const el of elements) {
        if (el.getAttribute('placeholder') === '제목') {
            const rect = el.getBoundingClientRect();
            return {x: rect.left + rect.width/2, y: rect.top + rect.height/2};
        }
    }
    return null;
"""
result = self._evaluate_js(js_code)
```

### 8.4 iframe 격리 처리
```python
# 네이버 블로그의 중첩 iframe 구조 처리

# 방법 1: Selenium switch_to
iframe = driver.find_element(By.ID, "mainFrame")
driver.switch_to.frame(iframe)
# ... 작업 ...
driver.switch_to.default_content()

# 방법 2: JavaScript 직접 접근
js_code = """
    const iframe = document.getElementById('mainFrame');
    return iframe.contentDocument.body.innerHTML;
"""
self._evaluate_js(js_code)
```

---

## 9. 에러 처리

### 9.1 Alert 핸들링
```python
def _handle_alert(self):
    """예상치 못한 alert 처리"""
    try:
        alert = self.driver.switch_to.alert
        alert.accept()
        return True
    except NoAlertPresentException:
        return False
```

### 9.2 재시도 가능한 오류
| 오류 상황 | 처리 방법 |
|-----------|-----------|
| 에디터 로드 실패 | 재시도 |
| 요소 찾기 실패 | 대체 셀렉터 시도 → 재시도 |
| 클릭 실패 | 좌표 재계산 → 재시도 |
| 발행 버튼 미발견 | 페이지 새로고침 → 재시도 |
| 검증 실패 | 재발행 시도 |

### 9.3 치명적 오류
| 오류 상황 | 처리 방법 |
|-----------|-----------|
| 로그인 실패 | 프로그램 종료 |
| WebDriver 생성 실패 | 프로그램 종료 |
| 최대 재시도 초과 | return False |

---

## 10. 참고 자료

### 10.1 관련 파일
| 파일 | 설명 |
|------|------|
| [main.py](../main.py) | 진입점, CLI 처리 |
| [src/config.py](../src/config.py) | 설정 관리 |
| [src/driver.py](../src/driver.py) | WebDriver 팩토리 |
| [src/blog_writer_cdp.py](../src/blog_writer_cdp.py) | CDP 포스팅 (핵심) |
| [src/blog_writer.py](../src/blog_writer.py) | Selenium 포스팅 |

### 10.2 외부 문서
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [Selenium Python Documentation](https://selenium-python.readthedocs.io/)
- [네이버 SmartEditor ONE](https://smarteditor.naver.com/)
