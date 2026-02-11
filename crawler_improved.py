"""
네이버 증권 토론방 크롤러 (강화 버전)
- 여러 선택자 시도
- 더 나은 에러 처리
- 디버깅 정보 포함
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImprovedStockDiscussionCrawler:
    """개선된 네이버 증권 토론방 크롤러"""
    
    def __init__(self, stock_code='005930'):
        self.stock_code = stock_code
        self.base_url = f"https://finance.naver.com/item/board.naver?code={stock_code}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
    def _get_nickname(self, row):
        """닉네임 추출 (여러 방법 시도)"""
        # 방법 1: td.name
        name_tag = row.find('td', class_='name')
        if name_tag:
            nickname = name_tag.text.strip()
            if nickname:
                return nickname
        
        # 방법 2: td.p11 (대안)
        name_tag = row.find('td', class_='p11')
        if name_tag:
            nickname = name_tag.text.strip()
            if nickname:
                return nickname
        
        # 방법 3: span.p11
        name_span = row.find('span', class_='p11')
        if name_span:
            nickname = name_span.text.strip()
            if nickname:
                return nickname
        
        return 'N/A'
    
    def _get_write_time(self, row):
        """작성시간 추출 (여러 방법 시도)"""
        # 방법 1: td.date
        date_tag = row.find('td', class_='date')
        if date_tag:
            write_time = date_tag.text.strip()
            if write_time:
                return write_time
        
        # 방법 2: span.date (대안)
        date_span = row.find('span', class_='date')
        if date_span:
            write_time = date_span.text.strip()
            if write_time:
                return write_time
        
        # 방법 3: td.p11 중 날짜 형식
        all_tds = row.find_all('td')
        for td in all_tds:
            text = td.text.strip()
            if '.' in text or ':' in text:
                # 날짜 형식일 가능성
                if len(text) < 20:  # 너무 길지 않음
                    return text
        
        return 'N/A'
    
    def _get_content(self, href):
        """게시글 내용 가져오기 (여러 방법 시도)"""
        try:
            url = f"https://finance.naver.com{href}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return "내용 없음"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 방법 1: td.view_cnt
            content_tag = soup.find('td', class_='view_cnt')
            if content_tag:
                content = content_tag.text.strip()
                content = ' '.join(content.split())
                if len(content) > 5:
                    return content
            
            # 방법 2: div.view_cnt
            content_div = soup.find('div', class_='view_cnt')
            if content_div:
                content = content_div.text.strip()
                content = ' '.join(content.split())
                if len(content) > 5:
                    return content
            
            # 방법 3: div.view_content
            content_div = soup.find('div', class_='view_content')
            if content_div:
                content = content_div.text.strip()
                content = ' '.join(content.split())
                if len(content) > 5:
                    return content
            
            # 방법 4: div.sub_ct (대안)
            content_div = soup.find('div', class_='sub_ct')
            if content_div:
                content = content_div.text.strip()
                content = ' '.join(content.split())
                if len(content) > 5:
                    return content
            
            # 방법 5: table.view_tb 안의 모든 텍스트
            view_table = soup.find('table', class_='view_tb')
            if view_table:
                content = view_table.text.strip()
                content = ' '.join(content.split())
                if len(content) > 20:
                    return content
            
            logger.warning(f"내용을 찾을 수 없음: {href}")
            return "내용 없음"
            
        except Exception as e:
            logger.error(f"내용 크롤링 오류: {e}")
            return "내용 없음"
    
    def _is_older_than_target(self, date_str, target_date):
        """목표 날짜 이전인지 확인"""
        try:
            if '.' in date_str and date_str.count('.') == 2:
                post_date = datetime.strptime(date_str, '%Y.%m.%d')
                return post_date < target_date
            elif date_str.count('.') == 1:
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
        
        Args:
            max_pages: 최대 페이지 수 (기본 100, 1년치는 보통 100페이지 이내)
            delay: 요청 간 지연 시간 (초) - 2초로 증가
            target_days: 목표 수집 일수 (기본 365일)
        """
        all_posts = []
        current_date = datetime.now()
        target_date = current_date - timedelta(days=target_days)
        
        logger.info(f"크롤링 시작: 종목코드 {self.stock_code}")
        logger.info(f"목표 기간: {target_date.date()} ~ {current_date.date()} ({target_days}일)")
        logger.info(f"지연 시간: {delay}초 (서버 부담 최소화)")
        
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
                    logger.warning(f"페이지 {page}: 게시글 없음")
                    break
                
                rows = table.find_all('tr')
                page_has_posts = False
                
                for row in rows:
                    try:
                        # 제목 찾기
                        title_tag = row.find('td', class_='title')
                        if not title_tag:
                            continue
                        
                        title_link = title_tag.find('a')
                        if not title_link:
                            continue
                        
                        title = title_link.text.strip()
                        
                        # 닉네임 (개선된 방법)
                        nickname = self._get_nickname(row)
                        
                        # 작성시간 (개선된 방법)
                        write_time = self._get_write_time(row)
                        
                        # 목표 기간 초과 확인
                        if self._is_older_than_target(write_time, target_date):
                            logger.info(f"목표 기간 초과: {write_time}")
                            return self._create_dataframe(all_posts, current_date)
                        
                        # 내용 (개선된 방법)
                        content = self._get_content(title_link['href'])
                        
                        post = {
                            '닉네임': nickname,
                            '작성시간': write_time,
                            '제목': title,
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
                
                time.sleep(delay)  # 2초 지연
                
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
            has_real_content = df[(df['내용'] != '내용 없음') & (df['내용'].str.len() > 10)]
            logger.info(f"실제 내용이 있는 게시글: {len(has_real_content)}개 ({len(has_real_content)/len(df)*100:.1f}%)")
        
        return df


def main():
    """메인 실행"""
    os.makedirs('./data/raw', exist_ok=True)
    
    logger.info("="*80)
    logger.info("네이버 증권 토론방 크롤러 - 강화 버전")
    logger.info("="*80)
    
    crawler = ImprovedStockDiscussionCrawler(stock_code='005930')
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
