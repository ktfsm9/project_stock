"""
네이버 증권 토론방 크롤러 (디버깅 버전)
HTML 구조를 확인하고 올바른 선택자 찾기
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

def test_crawler():
    """크롤러 테스트"""
    
    stock_code = '005930'
    base_url = f"https://finance.naver.com/item/board.naver?code={stock_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print("="*80)
    print("네이버 증권 토론방 크롤러 테스트")
    print("="*80)
    
    # 페이지 1 가져오기
    url = f"{base_url}&page=1"
    print(f"\n1. URL 요청: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print("   ❌ 요청 실패!")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. 테이블 찾기
        print("\n2. 테이블 찾기")
        table = soup.find('table', class_='type2')
        
        if not table:
            print("   ❌ 테이블을 찾을 수 없습니다!")
            print("\n   사용 가능한 테이블:")
            all_tables = soup.find_all('table')
            for i, t in enumerate(all_tables):
                print(f"   테이블 {i+1}: class={t.get('class')}")
            return
        
        print("   ✅ 테이블 발견!")
        
        # 3. 게시글 행 찾기
        print("\n3. 게시글 행 분석")
        rows = table.find_all('tr')
        print(f"   총 {len(rows)}개 행 발견")
        
        post_count = 0
        for idx, row in enumerate(rows[:5]):  # 처음 5개만 테스트
            # 제목 찾기
            title_tag = row.find('td', class_='title')
            if not title_tag:
                continue
            
            title_link = title_tag.find('a')
            if not title_link:
                continue
            
            post_count += 1
            print(f"\n   === 게시글 {post_count} ===")
            
            # 제목
            title = title_link.text.strip()
            print(f"   제목: {title[:50]}...")
            
            # 닉네임
            name_tag = row.find('td', class_='name')
            if name_tag:
                nickname = name_tag.text.strip()
                print(f"   닉네임: {nickname}")
            else:
                print("   닉네임: ❌ 찾을 수 없음")
                # 대안 찾기
                print(f"   행 내용: {row.text[:100]}")
            
            # 작성시간
            date_tag = row.find('td', class_='date')
            if date_tag:
                write_time = date_tag.text.strip()
                print(f"   작성시간: {write_time}")
            else:
                print("   작성시간: ❌ 찾을 수 없음")
            
            # 내용 링크
            href = title_link['href']
            print(f"   링크: {href[:50]}...")
            
            # 내용 가져오기
            try:
                content_url = f"https://finance.naver.com{href}"
                content_response = requests.get(content_url, headers=headers, timeout=10)
                
                if content_response.status_code == 200:
                    content_soup = BeautifulSoup(content_response.text, 'html.parser')
                    
                    # 내용 찾기 시도 1
                    content_tag = content_soup.find('td', class_='view_cnt')
                    if content_tag:
                        content = content_tag.text.strip()
                        print(f"   내용 (첫 100자): {content[:100]}...")
                    else:
                        # 내용 찾기 시도 2
                        content_tag = content_soup.find('div', class_='view_cnt')
                        if content_tag:
                            content = content_tag.text.strip()
                            print(f"   내용 (첫 100자): {content[:100]}...")
                        else:
                            print("   내용: ❌ 찾을 수 없음")
                            # 사용 가능한 클래스 출력
                            print("   사용 가능한 내용 영역:")
                            for tag in content_soup.find_all(['td', 'div'])[:5]:
                                if tag.get('class'):
                                    print(f"     {tag.name}.{tag.get('class')}")
                else:
                    print(f"   내용 요청 실패: {content_response.status_code}")
                
                time.sleep(1)  # 지연
                
            except Exception as e:
                print(f"   내용 가져오기 오류: {e}")
        
        print(f"\n총 {post_count}개 게시글 분석 완료")
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_crawler()
