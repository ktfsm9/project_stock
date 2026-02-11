"""
네이버 증권 토론방 크롤러 (패턴 기반 - 최종 완성 버전)
HTML 클래스 대신 패턴으로 데이터 추출
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
import os
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerfectStockDiscussionCrawler:
    """완벽한 네이버 증권 토론방 크롤러"""
    
    def __init__(self, stock_code='005930'):
        self.stock_code = stock_code
        self.base_url = f"https://finance.naver.com/item/board.naver?code={stock_code}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
    def _extract_from_row(self, row):
        """행에서 모든 정보 추출 (패턴 기반)"""
        # 모든 td 태그 가져오기
        all_tds = row.find_all('td')
        
        # 제목과 링크 찾기
        title = None
        href = None
        for td in all_tds:
            link = td.find('a')
            if link and 'board_read.naver' in link.get('href', ''):
                title = link.text.strip()
                href = link['href']
                break
        
        if not title:
            return None
        
        # 행의 모든 텍스트 추출
        row_text = row.get_text(separator='|', strip=True)
        parts = [p.strip() for p in row_text.split('|') if p.strip()]
        
        # 작성시간 찾기 (YYYY.MM.DD HH:MM 또는 MM.DD 형식)
        write_time = None
        for part in parts:
            # 패턴 1: 2026.02.11 11:42
            if re.match(r'\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}', part):
                write_time = part
                break
            # 패턴 2: 02.11
            elif re.match(r'\d{2}\.\d{2}$', part):
                write_time = part
                break
        
        if not write_time:
            write_time = 'N/A'
        
        # 닉네임 찾기 (제목 다음에 나오는 한글 텍스트)
        nickname = None
        found_title = False
        for part in parts:
            if title in part:
                found_title = True
                continue
            if found_title and len(part) > 1 and re.search(r'[가-힣]', part):
                # 숫자만 있는 것 제외
                if not part.isdigit() and not re.match(r'^\d+$', part):
                    nickname = part
                    break
        
        if not nickname:
            nickname = 'N/A'
        
        return {
            'title': title,
            'href': href,
            'write_time': write_time,
            'nickname': nickname
        }
    
    def _get_content(self, href):
        """게시글 내용 가져오기"""
        try:
            url = f"https://finance.naver.com{href}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return "내용 없음"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 방법 1: td.view_cnt
            content_tag = soup.find('td', class_='view_cnt')
            if content_tag:
                content = content_tag.get_text(separator=' ', strip=True)
                if len(content) > 10:
                    return content
            
            # 방법 2: 모든 td에서 가장 긴 텍스트 찾기
            all_tds = soup.find_all('td')
            longest_text = ""
            for td in all_tds:
                text = td.get_text(separator=' ', strip=True)
                if len(text) > len(longest_text):
                    longest_text = text
            
            if len(longest_text) > 20:
                return longest_text
            
            return "내용 없음"
            
        except Exception as e:
            logger.error(f"내용 크롤링 오류: {e}")
            return "내용 없음"
    
    def _is_older_than_target(self, date_str, target_date):
        """목표 날짜 이전인지 확인"""
        try:
            # 2026.02.11 11:42 형식
            if re.match(r'\d{4}\.\d{2}\.\d{2}', date_str):
                date_part = date_str.split()[0]
                post_date = datetime.strptime(date_part, '%Y.%m.%d')
                return post_date < target_date
            # 02.11 형식
            elif re.match(r'\d{2}\.\d{2}$', date_str):
                month, day = date_str.split('.')
                current_year = datetime.now().year
                post_date = datetime(current_year, int(month), int(day))
                return post_date < target_date
            return False
        except:
            return False
    
    def crawl_discussion_board(self, max_pages=100, delay=2, target_days=365):
        """
        토론방 게시글 크롤링
        """
        all_posts = []
        current_date = datetime.now()
        target_date = current_date - timedelta(days=target_days)
        
        logger.info(f"크롤링 시작: 종목코드 {self.stock_code}")
        logger.info(f"목표 기간: {target_date.date()} ~ {current_date.date()} ({target_days}일)")
        logger.info(f"지연 시간: {delay}초")
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.base_url}&page={page}"
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code != 200:
                    logger.warning(f"페이지 {page} 요청 실패: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table', class_='type2')
                
                if not table:
                    logger.warning(f"페이지 {page}: 테이블 없음")
                    break
                
                rows = table.find_all('tr')
                page_has_posts = False
                
                for row in rows:
                    try:
                        # 패턴 기반 추출
                        post_info = self._extract_from_row(row)
                        
                        if not post_info:
                            continue
                        
                        # 목표 기간 초과 확인
                        if self._is_older_than_target(post_info['write_time'], target_date):
                            logger.info(f"목표 기간 초과: {post_info['write_time']}")
                            return self._create_dataframe(all_posts, current_date)
                        
                        # 내용 가져오기
                        content = self._get_content(post_info['href'])
                        
                        post = {
                            '닉네임': post_info['nickname'],
                            '작성시간': post_info['write_time'],
                            '제목': post_info['title'],
                            '내용': content,
                            '크롤링일자': current_date.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        all_posts.append(post)
                        page_has_posts = True
                        
                    except Exception as e:
                        logger.error(f"게시글 파싱 오류: {e}")
                        continue
                
                if not page_has_posts:
                    break
                
                if page % 10 == 0:
                    logger.info(f"진행: {page}/{max_pages} 페이지, {len(all_posts)}개 수집")
                
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"페이지 {page} 크롤링 오류: {e}")
                continue
        
        logger.info(f"크롤링 완료: 총 {len(all_posts)}개 게시글")
        return self._create_dataframe(all_posts, current_date)
    
    def _create_dataframe(self, posts, current_date):
        """DataFrame 생성 및 검증"""
        df = pd.DataFrame(posts)
        
        if len(df) > 0:
            df.insert(0, 'N', range(1, len(df) + 1))
            
            # 데이터 품질 체크
            logger.info("\n=== 데이터 품질 체크 ===")
            logger.info(f"총 게시글: {len(df)}개")
            logger.info(f"닉네임 'N/A': {(df['닉네임'] == 'N/A').sum()}개 ({(df['닉네임'] == 'N/A').sum()/len(df)*100:.1f}%)")
            logger.info(f"작성시간 'N/A': {(df['작성시간'] == 'N/A').sum()}개 ({(df['작성시간'] == 'N/A').sum()/len(df)*100:.1f}%)")
            logger.info(f"내용 '내용 없음': {(df['내용'] == '내용 없음').sum()}개 ({(df['내용'] == '내용 없음').sum()/len(df)*100:.1f}%)")
            
            # 실제 내용이 있는 게시글
            has_real_content = df[
                (df['닉네임'] != 'N/A') & 
                (df['작성시간'] != 'N/A') & 
                (df['내용'] != '내용 없음') & 
                (df['내용'].str.len() > 10)
            ]
            logger.info(f"완전한 게시글: {len(has_real_content)}개 ({len(has_real_content)/len(df)*100:.1f}%)")
        
        return df


def main():
    """메인 실행"""
    os.makedirs('./data/raw', exist_ok=True)
    
    logger.info("="*80)
    logger.info("네이버 증권 토론방 크롤러 - 패턴 기반 완성 버전")
    logger.info("="*80)
    
    crawler = PerfectStockDiscussionCrawler(stock_code='005930')
    df = crawler.crawl_discussion_board(max_pages=100, delay=2, target_days=365)
    
    output_path = './data/raw/discussion_data.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    logger.info(f"\n저장 완료: {output_path}")
    logger.info(f"총 {len(df):,}개 게시글 수집")
    
    if len(df) > 0:
        logger.info(f"\n샘플 데이터 (최근 5개):")
        print(df.head(5)[['닉네임', '작성시간', '제목']].to_string(index=False))
        
        # 내용 샘플
        has_content = df[df['내용'] != '내용 없음'].head(3)
        if len(has_content) > 0:
            logger.info(f"\n내용 샘플 (3개):")
            for idx, row in has_content.iterrows():
                logger.info(f"\n[{idx+1}] 제목: {row['제목']}")
                logger.info(f"닉네임: {row['닉네임']}, 작성시간: {row['작성시간']}")
                logger.info(f"내용: {str(row['내용'])[:150]}...")


if __name__ == "__main__":
    main()
