#!/bin/bash
# 네이버 블로그 자동 글쓰기 프로그램 실행 스크립트

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# 디스플레이 환경 설정 (GUI 브라우저 실행에 필요)
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo "[INFO] Wayland 세션 감지됨"
    # Wayland 환경에서 필요한 설정
    export MOZ_ENABLE_WAYLAND=1
elif [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
    echo "[INFO] DISPLAY 환경 변수를 :0으로 설정했습니다."
fi

# 가상환경 활성화
source venv/bin/activate

# 프로그램 실행
python main.py "$@"
