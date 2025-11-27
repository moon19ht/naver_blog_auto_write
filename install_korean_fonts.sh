#!/bin/bash
# WSL에서 한글 글꼴 설치 스크립트

echo "=========================================="
echo "한글 글꼴 설치 스크립트"
echo "=========================================="

# 패키지 업데이트
echo "[INFO] 패키지 목록 업데이트 중..."
sudo apt-get update

# 한글 글꼴 패키지 설치
echo "[INFO] 한글 글꼴 설치 중..."
sudo apt-get install -y fonts-nanum fonts-nanum-coding fonts-nanum-extra
sudo apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra
sudo apt-get install -y fonts-unfonts-core fonts-unfonts-extra
sudo apt-get install -y fonts-baekmuk

# 한글 로케일 설정
echo "[INFO] 한글 로케일 설정 중..."
sudo apt-get install -y language-pack-ko
sudo locale-gen ko_KR.UTF-8

# 글꼴 캐시 갱신
echo "[INFO] 글꼴 캐시 갱신 중..."
sudo fc-cache -fv

echo ""
echo "=========================================="
echo "한글 글꼴 설치 완료!"
echo "설치된 한글 글꼴 목록:"
fc-list :lang=ko | head -20
echo "=========================================="
