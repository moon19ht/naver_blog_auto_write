#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
네이버 블로그 자동 글쓰기 프로그램
메인 실행 파일

사용법:
    python main.py                          # 대화형 모드
    python main.py --title "제목" --content "내용"  # 명령줄 모드
"""
import argparse
import sys
import time

from src.config import get_config
from src.driver import WebDriverManager
from src.naver_login import NaverLogin
from src.blog_writer import NaverBlogWriter
from src.blog_writer_cdp import NaverBlogWriterCDP


def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='네이버 블로그 자동 글쓰기 프로그램',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
예시:
    python main.py --title "오늘의 일기" --content "오늘 하루도 즐거웠습니다."
    python main.py --title "제목" --content-file content.txt --tags "일상" "블로그"
    python main.py  # 대화형 모드
        '''
    )
    
    parser.add_argument(
        '--title', '-t',
        type=str,
        help='블로그 글 제목'
    )
    
    parser.add_argument(
        '--content', '-c',
        type=str,
        help='블로그 글 내용'
    )
    
    parser.add_argument(
        '--content-file', '-f',
        type=str,
        help='내용을 읽어올 파일 경로'
    )
    
    parser.add_argument(
        '--category',
        type=str,
        help='카테고리 이름'
    )
    
    parser.add_argument(
        '--tags',
        nargs='+',
        type=str,
        help='태그 목록'
    )
    
    parser.add_argument(
        '--private',
        action='store_true',
        help='비공개로 발행'
    )
    
    parser.add_argument(
        '--mode', '-m',
        type=str,
        choices=['selenium', 'cdp'],
        help='글쓰기 모드 선택 (selenium: 기존 방식, cdp: Chrome DevTools Protocol 방식)'
    )
    
    parser.add_argument(
        '--retries', '-r',
        type=int,
        default=2,
        help='발행 실패 시 최대 재시도 횟수 (기본값: 2)'
    )
    
    parser.add_argument(
        '--remote',
        action='store_true',
        help='SSH 원격 접속 모드 (자동으로 헤드리스 + CDP 모드 활성화)'
    )
    
    return parser.parse_args()


def get_publish_settings_interactive() -> dict:
    """대화형으로 발행 설정 옵션 입력받기"""
    print("\n" + "=" * 50)
    print("발행 설정 옵션")
    print("=" * 50)
    
    # 기본값 설정
    settings = {
        'visibility': 'public',           # 전체공개
        'allow_comment': True,            # 댓글 허용
        'allow_sympathy': True,           # 공감 허용
        'allow_search': True,             # 검색 허용
        'blog_cafe_share': 'link',        # 블로그/카페 공유 (링크 허용)
        'allow_external_share': True,     # 외부 공유 허용
        'is_notice': False                # 공지사항 등록
    }
    
    print("\n[공개 설정] (기본값: 1. 전체공개)")
    print("  1. 전체공개")
    print("  2. 이웃공개")
    print("  3. 서로이웃공개")
    print("  4. 비공개")
    visibility_input = input("선택 (1-4, Enter=기본값): ").strip()
    if visibility_input == '2':
        settings['visibility'] = 'neighbor'
    elif visibility_input == '3':
        settings['visibility'] = 'mutual'
    elif visibility_input == '4':
        settings['visibility'] = 'private'
    
    print("\n[발행 설정] 해제할 옵션 번호를 입력하세요 (쉼표로 구분, Enter=모두 유지)")
    print("  1. 댓글 허용 (기본: ON)")
    print("  2. 공감 허용 (기본: ON)")
    print("  3. 검색 허용 (기본: ON)")
    print("  4. 블로그/카페 공유 - 링크 허용 (기본: ON)")
    print("  5. 블로그/카페 공유 - 본문 허용으로 변경")
    print("  6. 외부 공유 허용 (기본: ON)")
    
    disable_input = input("해제할 옵션 (예: 1,3,6): ").strip()
    if disable_input:
        disable_options = [x.strip() for x in disable_input.split(',')]
        if '1' in disable_options:
            settings['allow_comment'] = False
        if '2' in disable_options:
            settings['allow_sympathy'] = False
        if '3' in disable_options:
            settings['allow_search'] = False
        if '4' in disable_options:
            settings['blog_cafe_share'] = 'none'
        if '5' in disable_options:
            settings['blog_cafe_share'] = 'content'
        if '6' in disable_options:
            settings['allow_external_share'] = False
    
    print("\n[공지사항]")
    print("  1. 공지사항으로 등록하지 않음 (기본)")
    print("  2. 공지사항으로 등록")
    notice_input = input("선택 (1-2, Enter=기본값): ").strip()
    if notice_input == '2':
        settings['is_notice'] = True
    
    return settings


def get_content_interactive() -> tuple:
    """대화형으로 제목과 내용 입력받기"""
    print("\n" + "=" * 50)
    print("네이버 블로그 자동 글쓰기")
    print("=" * 50 + "\n")
    
    # 제목 입력 (공백만 입력된 경우 재입력 요청)
    while True:
        title = input("제목을 입력하세요: ").strip()
        if title:
            break
        print("[WARNING] 제목이 비어있습니다. 다시 입력해주세요.")
    
    print("\n내용을 입력하세요 (입력 완료 시 빈 줄에서 'END' 입력):")
    print("-" * 30)
    
    # 내용 입력 (공백만 입력된 경우 재입력 요청)
    while True:
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
            except EOFError:
                break
        
        content = '\n'.join(lines).strip()
        
        if content:
            break
        print("[WARNING] 내용이 비어있습니다. 다시 입력해주세요.")
        print("-" * 30)
    
    # 카테고리 입력 (선택) - 공백만 있으면 None 처리
    category = input("\n카테고리를 입력하세요 (Enter로 건너뛰기): ").strip()
    category = category if category else None
    
    # 태그 입력 (띄어쓰기로 구분) - 공백만 있으면 None 처리
    tags_input = input("태그를 입력하세요 (띄어쓰기로 구분, Enter로 건너뛰기): ").strip()
    tags = [tag.strip() for tag in tags_input.split() if tag.strip()] if tags_input else None
    
    # 발행 설정 옵션
    publish_settings = get_publish_settings_interactive()
    
    return title, content, category, tags, publish_settings


def main():
    """메인 함수"""
    args = parse_arguments()
    
    # 내용 결정
    if args.title and (args.content or args.content_file):
        # 명령줄 모드
        title = args.title.strip() if args.title else ""
        
        if not title:
            print("[ERROR] 제목이 비어있습니다.")
            sys.exit(1)
        
        if args.content_file:
            try:
                with open(args.content_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
            except FileNotFoundError:
                print(f"[ERROR] 파일을 찾을 수 없습니다: {args.content_file}")
                sys.exit(1)
        else:
            content = args.content.strip() if args.content else ""
        
        if not content:
            print("[ERROR] 내용이 비어있습니다.")
            sys.exit(1)
        
        category = args.category.strip() if args.category else None
        category = category if category else None  # 공백만 있으면 None
        
        tags = [tag.strip() for tag in args.tags if tag.strip()] if args.tags else None
        tags = tags if tags else None  # 빈 리스트면 None
        # 명령줄 모드는 기본 설정 사용
        publish_settings = {
            'visibility': 'private' if args.private else 'public',
            'allow_comment': True,
            'allow_sympathy': True,
            'allow_search': True,
            'blog_cafe_share': 'link',
            'allow_external_share': True,
            'is_notice': False
        }
    else:
        # 대화형 모드
        title, content, category, tags, publish_settings = get_content_interactive()
    
    # 설정 로드
    try:
        config = get_config()
    except ValueError as e:
        print(f"[ERROR] 설정 오류: {e}")
        print("[INFO] .env.example 파일을 .env로 복사하고 설정을 입력해주세요.")
        sys.exit(1)
    
    # --remote 옵션 처리: SSH 원격 모드 강제 적용
    if args.remote:
        config.remote_mode = True
        config.headless = True
        config.writer_mode = 'cdp'
        print("[INFO] SSH 원격 모드 활성화 (헤드리스 + CDP 모드)")
    
    # 글쓰기 모드 결정 (명령줄 > 원격모드 > 환경변수)
    if args.mode:
        writer_mode = args.mode
    elif config.remote_mode:
        writer_mode = 'cdp'  # 원격 모드에서는 CDP 강제
    else:
        writer_mode = config.writer_mode
    
    print(f"\n[INFO] 브라우저: {config.browser_type}")
    print(f"[INFO] 헤드리스 모드: {config.headless}")
    print(f"[INFO] 원격 모드 (SSH): {config.remote_mode}")
    print(f"[INFO] 글쓰기 모드: {writer_mode.upper()}")
    
    # 웹드라이버 시작
    driver_manager = WebDriverManager(config)
    
    try:
        print("\n[INFO] 브라우저를 시작합니다...")
        driver = driver_manager.create_driver()
        
        # 네이버 로그인
        login = NaverLogin(driver, config)
        if not login.login():
            print("[ERROR] 로그인에 실패했습니다.")
            sys.exit(1)
        
        time.sleep(2)
        
        # 재시도 횟수
        max_retries = args.retries if hasattr(args, 'retries') else 2
        
        # 글쓰기 모드에 따라 Writer 선택
        if writer_mode == 'cdp':
            print("[INFO] Chrome DevTools Protocol(CDP) 모드로 글 작성...")
            print(f"[INFO] 최대 재시도 횟수: {max_retries}")
            writer = NaverBlogWriterCDP(driver, config)
            success = writer.write_post(
                title=title,
                content=content,
                category=category,
                tags=tags,
                publish_settings=publish_settings,
                max_retries=max_retries
            )
        else:
            print("[INFO] Selenium 모드로 글 작성...")
            writer = NaverBlogWriter(driver, config)
            is_public = publish_settings.get('visibility') == 'public'
            success = writer.write_post(
                title=title,
                content=content,
                category=category,
                tags=tags,
                is_public=is_public
            )
        
        if success:
            print("\n" + "=" * 50)
            print("블로그 글이 성공적으로 발행되었습니다!")
            print("=" * 50)
        else:
            print("\n[ERROR] 글 발행에 실패했습니다.")
            sys.exit(1)
        
        # 결과 확인을 위해 잠시 대기
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n[INFO] 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("\n[INFO] 브라우저를 종료합니다...")
        driver_manager.close()


if __name__ == "__main__":
    main()
