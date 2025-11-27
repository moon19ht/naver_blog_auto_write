# 네이버 블로그 자동 글쓰기 프로그램

네이버에 자동으로 로그인하고 블로그에 글을 자동으로 작성하는 Python 프로그램입니다.

## 기능

- 🔐 네이버 자동 로그인 (자동화 탐지 우회)
- ✍️ 블로그 글 자동 작성
- 📁 카테고리 설정
- 🏷️ 태그 추가
- 🔒 공개/비공개 설정
- 💻 명령줄 & 대화형 모드 지원

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

# 헤드리스 모드 (True/False)
HEADLESS=False

# 블로그 설정
BLOG_CATEGORY=일상
```

## 사용 방법

### 대화형 모드

```bash
python main.py
```

실행하면 제목, 내용, 카테고리, 태그, 공개 여부를 순차적으로 입력할 수 있습니다.

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

## 프로젝트 구조

```
naver_blog_auto_write/
├── main.py              # 메인 실행 파일
├── requirements.txt     # 의존성 패키지
├── .env.example         # 환경 변수 예시
├── .env                 # 환경 변수 (git 제외)
├── .gitignore
├── README.md
├── venv/                # 가상환경 (git 제외)
└── src/
    ├── __init__.py      # 패키지 초기화
    ├── config.py        # 설정 관리
    ├── driver.py        # 웹드라이버 관리
    ├── naver_login.py   # 네이버 로그인 모듈
    └── blog_writer.py   # 블로그 글 작성 모듈
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

- 네이버 에디터 UI가 변경되었을 수 있습니다.
- 로그인이 정상적으로 되었는지 확인하세요.

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 Issue를 통해 알려주세요.
