# 네이버 블로그 자동 글쓰기 프로그램

네이버에 자동으로 로그인하고 블로그에 글을 자동으로 작성하는 Python 프로그램입니다.

## 기능

- 🔐 네이버 자동 로그인 (자동화 탐지 우회)
- ✍️ 블로그 글 자동 작성
- 📁 카테고리 설정
- 🏷️ 태그 추가
- 🔒 공개/이웃공개/서로이웃공개/비공개 설정
- 💬 댓글, 공감, 검색, 공유 옵션 설정
- 📌 공지사항 등록 지원
- 🔄 CDP (Chrome DevTools Protocol) 모드 지원 (권장)
- 💻 명령줄 & 대화형 모드 지원
- 🔁 발행 실패 시 자동 재시도

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/moon19ht/naver_blog_auto_write.git
cd naver_blog_auto_write
```

### 2. 가상환경 설정

```bash
# 가상환경 생성 (이미 생성되어 있다면 건너뛰기)
python3 -m venv venv

# 가상환경 활성화
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

```bash
# .env.example 파일을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일을 편집하여 네이버 계정 정보 입력
```

**.env 파일 내용:**
```env
# 네이버 로그인 정보
NAVER_ID=your_naver_id
NAVER_PW=your_naver_password

# 브라우저 설정 (chrome, edge, firefox)
BROWSER_TYPE=chrome

# 헤드리스 모드 (True/False) - 브라우저 창을 숨기려면 True
HEADLESS=False

# 블로그 설정
# 블로그 ID (네이버 아이디와 다를 경우 입력, 비워두면 NAVER_ID 사용)
BLOG_ID=
BLOG_CATEGORY=일상

# 글쓰기 모드 설정
# selenium: 기존 Selenium 방식
# cdp: Chrome DevTools Protocol 방식 (더 안정적, 권장)
WRITER_MODE=cdp
```

## 사용 방법

### 빠른 실행 (Linux/Mac)

```bash
./run.sh
```

### 대화형 모드

```bash
python main.py
```

실행하면 제목, 내용, 카테고리, 태그, 공개 여부 및 발행 옵션을 순차적으로 입력할 수 있습니다.

**대화형 모드 발행 설정 옵션:**
- 공개 설정: 전체공개 / 이웃공개 / 서로이웃공개 / 비공개
- 발행 설정: 댓글 허용, 공감 허용, 검색 허용, 블로그/카페 공유 (링크/본문), 외부 공유 허용
- 공지사항 등록

### 명령줄 모드

```bash
# 기본 사용
python main.py --title "글 제목" --content "글 내용"

# 파일에서 내용 읽기
python main.py --title "글 제목" --content-file content.txt

# 카테고리와 태그 추가
python main.py --title "글 제목" --content "글 내용" --category "일상" --tags "태그1" "태그2"

# 비공개로 발행
python main.py --title "글 제목" --content "글 내용" --private

# CDP 모드로 실행 (권장)
python main.py --title "글 제목" --content "글 내용" --mode cdp

# Selenium 모드로 실행
python main.py --title "글 제목" --content "글 내용" --mode selenium

# 재시도 횟수 설정
python main.py --title "글 제목" --content "글 내용" --retries 3

# SSH 원격 모드로 실행 (헤드리스 + CDP 자동 활성화)
python main.py --title "글 제목" --content "글 내용" --remote
```

### 명령줄 옵션

| 옵션 | 단축 | 설명 |
|------|------|------|
| `--title` | `-t` | 블로그 글 제목 |
| `--content` | `-c` | 블로그 글 내용 |
| `--content-file` | `-f` | 내용을 읽어올 파일 경로 |
| `--category` | | 카테고리 이름 |
| `--tags` | | 태그 목록 (공백으로 구분) |
| `--private` | | 비공개로 발행 |
| `--mode` | `-m` | 글쓰기 모드 (`selenium` 또는 `cdp`) |
| `--retries` | `-r` | 발행 실패 시 최대 재시도 횟수 (기본값: 2) |
| `--remote` | | SSH 원격 접속 모드 (자동으로 헤드리스 + CDP 모드) |

## 프로젝트 구조

```
naver_blog_auto_write/
├── main.py                  # 메인 실행 파일
├── requirements.txt         # 의존성 패키지
├── .env.example             # 환경 변수 예시
├── .env                     # 환경 변수 (git 제외)
├── .gitignore
├── README.md
├── run.sh                   # 실행 스크립트 (Linux/Mac)
├── install_korean_fonts.sh  # 한글 폰트 설치 스크립트
├── venv/                    # 가상환경 (git 제외)
├── drivers/                 # 웹드라이버 디렉토리
└── src/
    ├── __init__.py          # 패키지 초기화
    ├── config.py            # 설정 관리
    ├── driver.py            # 웹드라이버 관리
    ├── naver_login.py       # 네이버 로그인 모듈
    ├── blog_writer.py       # 블로그 글 작성 모듈 (Selenium 방식)
    └── blog_writer_cdp.py   # 블로그 글 작성 모듈 (CDP 방식, 권장)
```

## 글쓰기 모드

### CDP 모드 (권장)
- Chrome DevTools Protocol을 활용한 안정적인 페이지 조작
- 네이버 에디터의 iframe 구조를 더 효과적으로 처리
- `WRITER_MODE=cdp` 또는 `--mode cdp`로 사용

### Selenium 모드
- 기존 Selenium 방식의 글쓰기
- `WRITER_MODE=selenium` 또는 `--mode selenium`으로 사용

### SSH 원격 모드 (Remote Mode)
SSH로 서버에 원격 접속하여 사용할 때 권장하는 모드입니다.

**특징:**
- 자동으로 헤드리스 모드 활성화 (GUI 없는 환경)
- CDP 모드 강제 적용 (클립보드 방식 사용 불가하므로)
- 브라우저 창 크기 고정 (1920x1080)
- 원격 환경 최적화 옵션 자동 적용

**사용법:**
```bash
# 명령줄 옵션으로 사용
python main.py --title "제목" --content "내용" --remote

# 또는 .env 파일에서 설정
REMOTE_MODE=True
```

## 주의사항

1. **보안**: `.env` 파일에 네이버 계정 정보가 저장되므로, 절대로 외부에 공유하지 마세요.

2. **자동화 탐지**: 네이버는 자동화 탐지가 강력합니다. 프로그램이 캡차나 추가 인증을 요구할 수 있습니다. 이 경우 브라우저에서 직접 인증해주세요.

3. **헤드리스 모드**: `HEADLESS=True` 설정 시 브라우저 창이 표시되지 않습니다. 하지만 자동화 탐지에 걸릴 확률이 높아질 수 있습니다.

4. **클립보드 방식**: 자동화 탐지를 우회하기 위해 클립보드를 통한 붙여넣기 방식을 사용합니다. 헤드리스 모드에서는 작동하지 않을 수 있습니다.

5. **이용 약관**: 자동화 프로그램 사용은 네이버 이용 약관에 위반될 수 있습니다. 개인적인 용도로만 사용하시기 바랍니다.

## 문제 해결

### 로그인이 안 될 때

- 캡차가 표시되면 브라우저에서 직접 입력해주세요.
- 2단계 인증이 활성화된 경우 브라우저에서 직접 인증해주세요.
- `HEADLESS=False`로 설정하고 실행해보세요.

### 브라우저가 실행되지 않을 때

- Chrome/Edge/Firefox가 설치되어 있는지 확인하세요.
- webdriver-manager가 자동으로 드라이버를 다운로드합니다.

### 글 작성이 안 될 때

- CDP 모드(`--mode cdp`)를 사용해보세요.
- 네이버 에디터 UI가 변경되었을 수 있습니다.
- 로그인이 정상적으로 되었는지 확인하세요.
- `--retries` 옵션으로 재시도 횟수를 늘려보세요.

### 한글이 깨질 때 (Linux)

```bash
./install_korean_fonts.sh
```

## 의존성

- `selenium>=4.15.0` - 웹 브라우저 자동화
- `webdriver-manager>=4.0.1` - 웹드라이버 자동 관리
- `python-dotenv>=1.0.0` - 환경 변수 관리
- `pyperclip>=1.8.2` - 클립보드 조작
- `pyautogui>=0.9.54` - GUI 자동화

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 Issue를 통해 알려주세요.
