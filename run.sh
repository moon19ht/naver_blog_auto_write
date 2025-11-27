#!/bin/bash
# 네이버 블로그 자동 글쓰기 프로그램 실행 스크립트

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
source venv/bin/activate

# 프로그램 실행
python main.py "$@"
