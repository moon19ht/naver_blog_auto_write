#!/bin/bash
# 한글 글꼴 및 필수 의존성 설치 스크립트
# 지원 배포판: Debian/Ubuntu, Arch Linux, Fedora, openSUSE

echo "=========================================="
echo "한글 글꼴 및 필수 의존성 설치 스크립트"
echo "=========================================="

# 배포판 감지
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO_ID=$ID
        DISTRO_LIKE=$ID_LIKE
    elif [ -f /etc/arch-release ]; then
        DISTRO_ID="arch"
    elif [ -f /etc/debian_version ]; then
        DISTRO_ID="debian"
    elif [ -f /etc/fedora-release ]; then
        DISTRO_ID="fedora"
    else
        DISTRO_ID="unknown"
    fi
    echo "[INFO] 감지된 배포판: $DISTRO_ID"
}

# Arch Linux 계열 설치
install_arch() {
    echo "[INFO] Arch Linux 패키지 설치 중..."
    sudo pacman -Sy --noconfirm
    
    # 한글 글꼴
    sudo pacman -S --noconfirm --needed \
        noto-fonts-cjk \
        noto-fonts-emoji \
        ttf-nanum \
        ttf-baekmuk
    
    # tkinter (pyautogui 의존성)
    sudo pacman -S --noconfirm --needed tk
    
    # 로케일 설정 (필요한 경우)
    if ! locale -a | grep -q "ko_KR.utf8"; then
        echo "[INFO] 한글 로케일 생성 중..."
        sudo sed -i 's/#ko_KR.UTF-8/ko_KR.UTF-8/' /etc/locale.gen
        sudo locale-gen
    fi
}

# Debian/Ubuntu 계열 설치
install_debian() {
    echo "[INFO] Debian/Ubuntu 패키지 설치 중..."
    sudo apt-get update
    
    # 한글 글꼴
    sudo apt-get install -y \
        fonts-nanum fonts-nanum-coding fonts-nanum-extra \
        fonts-noto-cjk fonts-noto-cjk-extra \
        fonts-unfonts-core fonts-unfonts-extra \
        fonts-baekmuk
    
    # tkinter (pyautogui 의존성)
    sudo apt-get install -y python3-tk python3-dev
    
    # 한글 로케일 설정
    sudo apt-get install -y language-pack-ko
    sudo locale-gen ko_KR.UTF-8
}

# Fedora/RHEL 계열 설치
install_fedora() {
    echo "[INFO] Fedora/RHEL 패키지 설치 중..."
    sudo dnf check-update
    
    # 한글 글꼴
    sudo dnf install -y \
        google-noto-cjk-fonts \
        google-noto-sans-cjk-ttc-fonts \
        nhn-nanum-fonts-common \
        nhn-nanum-gothic-fonts \
        nhn-nanum-myeongjo-fonts
    
    # tkinter (pyautogui 의존성)
    sudo dnf install -y python3-tkinter
    
    # 한글 로케일 설정
    sudo dnf install -y glibc-langpack-ko
}

# openSUSE 계열 설치
install_suse() {
    echo "[INFO] openSUSE 패키지 설치 중..."
    sudo zypper refresh
    
    # 한글 글꼴
    sudo zypper install -y \
        noto-sans-cjk-fonts \
        noto-serif-cjk-fonts
    
    # tkinter (pyautogui 의존성)
    sudo zypper install -y python3-tk
}

# 메인 실행
detect_distro

case $DISTRO_ID in
    arch|manjaro|endeavouros|artix|garuda)
        install_arch
        ;;
    debian|ubuntu|linuxmint|pop)
        install_debian
        ;;
    fedora|rhel|centos|rocky|almalinux)
        install_fedora
        ;;
    opensuse*|suse)
        install_suse
        ;;
    *)
        # ID_LIKE 확인
        if [[ "$DISTRO_LIKE" == *"arch"* ]]; then
            install_arch
        elif [[ "$DISTRO_LIKE" == *"debian"* ]] || [[ "$DISTRO_LIKE" == *"ubuntu"* ]]; then
            install_debian
        elif [[ "$DISTRO_LIKE" == *"fedora"* ]] || [[ "$DISTRO_LIKE" == *"rhel"* ]]; then
            install_fedora
        else
            echo "[WARNING] 지원되지 않는 배포판입니다: $DISTRO_ID"
            echo "[INFO] 수동으로 한글 글꼴과 tkinter를 설치해주세요."
            exit 1
        fi
        ;;
esac

# 글꼴 캐시 갱신
echo "[INFO] 글꼴 캐시 갱신 중..."
sudo fc-cache -fv

echo ""
echo "=========================================="
echo "설치 완료!"
echo "설치된 한글 글꼴 목록:"
fc-list :lang=ko | head -20
echo "=========================================="
