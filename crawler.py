"""
네이버 주식 토론 피드 크롤러 - 1년 기간 제한
https://stock.naver.com/discussion/feed/all
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
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


class NaverStockDiscussionCrawler:
    """네이버 주식 토론 피드 크롤러 - 기간 제한"""
    
    def __init__(self):
        self.url = "https://stock.naver.com/discussion/feed/all"
        
        # Chrome 옵션
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 백그라운드 실행
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        logger.info("ChromeDriver 자동 설치 및 시작...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
        self.posts_collected = set()  # 중복 방지
        self.current_time = datetime.now()
    
    def _parse_relative_time(self, time_str):
        """
        상대 시간을 절대 시간으로 변환
        예: "방금 전" -> 현재 시간
             "5분 전" -> 현재 - 5분
             "2시간 전" -> 현재 - 2시간
             "3일 전" -> 현재 - 3일
             "1개월 전" -> 현재 - 30일
             "1년 전" -> 현재 - 365일
        """
        try:
            # "방금 전"
            if "방금" in time_str:
                return self.current_time
            
            # 숫자 추출
            numbers = re.findall(r'\d+', time_str)
            if not numbers:
                return self.current_time
            
            value = int(numbers[0])
            
            # 분 전
            if "분" in time_str:
                return self.current_time - timedelta(minutes=value)
            # 시간 전
            elif "시간" in time_str:
                return self.current_time - timedelta(hours=value)
            # 일 전
            elif "일" in time_str:
                return self.current_time - timedelta(days=value)
            # 개월 전
            elif "개월" in time_str or "달" in time_str:
                return self.current_time - timedelta(days=value * 30)
            # 년 전
            elif "년" in time_str or "해" in time_str:
                return self.current_time - timedelta(days=value * 365)
            else:
                return self.current_time
        except:
            return self.current_time
    
    def _is_within_period(self, time_str, days=365):
        """게시글이 목표 기간 내인지 확인"""
        post_time = self._parse_relative_time(time_str)
        target_date = self.current_time - timedelta(days=days)
        
        return post_time >= target_date
    
    def _get_element_text(self, xpath, default='N/A'):
        """XPath로 텍스트 가져오기"""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            text = element.text.strip()
            return text if text else default
        except:
            return default
    
    def scroll_down(self):
        """페이지 아래로 스크롤"""
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            return True
        except:
            return False
    
    def get_current_posts_count(self):
        """현재 로드된 게시글 개수"""
        try:
            elements = self.driver.find_elements(By.XPATH, '//*[@id="tabpanel-all"]/div[2]/ul/li')
            return len(elements)
        except:
            return 0
    
    def crawl_visible_posts(self, target_days):
        """현재 보이는 모든 게시글 크롤링"""
        posts = []
        old_posts_count = 0
        
        total_posts = self.get_current_posts_count()
        logger.info(f"  로드된 게시글: {total_posts}개")
        
        for i in range(1, total_posts + 1):
            try:
                base_xpath = f'//*[@id="tabpanel-all"]/div[2]/ul/li[{i}]'
                
                # 제목
                title_xpath = f'{base_xpath}/div[3]/div/a/strong'
                title = self._get_element_text(title_xpath)
                
                if title == 'N/A' or not title:
                    continue
                
                # 작성시간
                time_xpath = f'{base_xpath}/div[2]/div/button/ul/li/span[2]'
                write_time = self._get_element_text(time_xpath)
                
                # 기간 체크
                if not self._is_within_period(write_time, days=target_days):
                    old_posts_count += 1
                    logger.debug(f"  {target_days}일 이전 게시글: {write_time}")
                    continue
                
                # 중복 체크
                post_id = f"{title}_{write_time}"
                if post_id in self.posts_collected:
                    continue
                
                self.posts_collected.add(post_id)
                
                # 종목명
                stock_xpath = f'{base_xpath}/div[1]/a/span'
                stock_name = self._get_element_text(stock_xpath)
                
                # 닉네임
                nickname_xpath = f'{base_xpath}/div[2]/div/div/button/span'
                nickname = self._get_element_text(nickname_xpath)
                
                # 내용
                content_xpath = f'{base_xpath}/div[3]/div/a/div/p'
                content = self._get_element_text(content_xpath, default='내용 없음')
                
                post = {
                    '종목명': stock_name,
                    '닉네임': nickname,
                    '작성시간': write_time,
                    '제목': title,
                    '내용': content,
                    '크롤링일자': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                posts.append(post)
                
            except Exception as e:
                logger.debug(f"게시글 {i} 파싱 오류: {e}")
                continue
        
        return posts, old_posts_count
    
    def crawl_discussion_feed(self, target_days=365, max_scrolls=200):
        """
        토론 피드 크롤링 (기간 제한)
        
        Args:
            target_days: 목표 기간 (일, 기본 365일 = 1년)
            max_scrolls: 최대 스크롤 횟수 (기본 200)
        """
        all_posts = []
        target_date = self.current_time - timedelta(days=target_days)
        
        logger.info("="*80)
        logger.info("네이버 주식 토론 피드 크롤링 - 기간 제한")
        logger.info(f"URL: {self.url}")
        logger.info(f"수집 기간: {target_date.strftime('%Y-%m-%d')} ~ {self.current_time.strftime('%Y-%m-%d')}")
        logger.info(f"목표: 최근 {target_days}일 ({target_days/365:.1f}년)")
        logger.info(f"최대 스크롤: {max_scrolls}회")
        logger.info("="*80)
        
        try:
            # 페이지 로드
            logger.info("\n페이지 로딩...")
            self.driver.get(self.url)
            
            logger.info("초기 컨텐츠 로딩 대기...")
            time.sleep(5)
            
            # 게시글 리스트 대기
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="tabpanel-all"]/div[2]/ul'))
                )
                logger.info("✅ 게시글 리스트 로드 완료")
            except:
                logger.error("❌ 게시글 리스트를 찾을 수 없습니다!")
                return pd.DataFrame()
            
            scroll_count = 0
            consecutive_old_scrolls = 0  # 연속으로 오래된 게시글만 나온 횟수
            
            while scroll_count < max_scrolls:
                scroll_count += 1
                
                logger.info(f"\n[스크롤 {scroll_count}/{max_scrolls}]")
                
                # 현재 보이는 게시글 크롤링
                new_posts, old_posts_count = self.crawl_visible_posts(target_days)
                
                if new_posts:
                    all_posts.extend(new_posts)
                    consecutive_old_scrolls = 0
                    logger.info(f"  새 게시글: {len(new_posts)}개")
                    logger.info(f"  누적: {len(self.posts_collected)}개")
                    logger.info(f"  {target_days}일 이전: {old_posts_count}개")
                else:
                    if old_posts_count > 0:
                        # 오래된 게시글만 있음
                        consecutive_old_scrolls += 1
                        logger.info(f"  {target_days}일 이전 게시글만 발견: {old_posts_count}개")
                        logger.info(f"  연속 {consecutive_old_scrolls}회")
                    else:
                        logger.info("  새 게시글 없음")
                
                # 연속으로 5번 오래된 게시글만 나오면 종료
                if consecutive_old_scrolls >= 5:
                    logger.info(f"\n{target_days}일 이전 게시글이 연속 {consecutive_old_scrolls}회 발견")
                    logger.info("목표 기간 게시글 수집 완료!")
                    break
                
                # 스크롤 다운
                logger.info("  스크롤 중...")
                self.scroll_down()
            
            if scroll_count >= max_scrolls:
                logger.info(f"\n최대 스크롤 횟수 도달 ({max_scrolls}회)")
            
        except KeyboardInterrupt:
            logger.warning("\n사용자 중단 (Ctrl+C)")
        except Exception as e:
            logger.error(f"크롤링 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            logger.info("\n브라우저 종료...")
            self.driver.quit()
        
        logger.info(f"\n크롤링 완료: 총 {len(all_posts)}개 수집")
        return self._create_dataframe(all_posts)
    
    def _create_dataframe(self, posts):
        """DataFrame 생성 및 검증"""
        df = pd.DataFrame(posts)
        
        if len(df) > 0:
            df.insert(0, 'N', range(1, len(df) + 1))
            
            logger.info("\n=== 데이터 품질 체크 ===")
            logger.info(f"총 게시글: {len(df)}개")
            logger.info(f"종목명 'N/A': {(df['종목명'] == 'N/A').sum()}개 ({(df['종목명'] == 'N/A').sum()/len(df)*100:.1f}%)")
            logger.info(f"닉네임 'N/A': {(df['닉네임'] == 'N/A').sum()}개 ({(df['닉네임'] == 'N/A').sum()/len(df)*100:.1f}%)")
            logger.info(f"내용 '내용 없음': {(df['내용'] == '내용 없음').sum()}개 ({(df['내용'] == '내용 없음').sum()/len(df)*100:.1f}%)")
            
            # 완전한 게시글
            complete = df[
                (df['종목명'] != 'N/A') &
                (df['닉네임'] != 'N/A') &
                (df['내용'] != '내용 없음')
            ]
            logger.info(f"완전한 게시글: {len(complete)}개 ({len(complete)/len(df)*100:.1f}%)")
            
            # 종목별 통계
            if '종목명' in df.columns:
                logger.info("\n=== 종목별 게시글 Top 10 ===")
                stock_counts = df[df['종목명'] != 'N/A']['종목명'].value_counts().head(10)
                for stock, count in stock_counts.items():
                    logger.info(f"  {stock}: {count}개")
        
        return df


def main():
    """메인 실행"""
    
    os.makedirs('./data/raw', exist_ok=True)
    
    logger.info("="*80)
    logger.info("네이버 주식 토론 피드 크롤러 - 1년 기간 제한")
    logger.info("https://stock.naver.com/discussion/feed/all")
    logger.info("="*80)
    logger.info("\n[주의]")
    logger.info("- Chrome 브라우저가 자동으로 열립니다")
    logger.info("- 크롤링 중에는 창을 닫지 마세요")
    logger.info("- 목표 기간 이전 게시글이 나오면 자동 중단")
    logger.info("- Ctrl+C로 언제든지 중단 가능\n")
    
    # 사용자 설정
    print("수집 기간 설정:")
    print("1. 1년 (365일)")
    print("2. 6개월 (180일)")
    print("3. 3개월 (90일)")
    print("4. 직접 입력")
    
    choice = input("\n선택 (기본 1): ").strip()
    
    if choice == '2':
        target_days = 180
    elif choice == '3':
        target_days = 90
    elif choice == '4':
        days_input = input("일 수 입력: ").strip()
        target_days = int(days_input) if days_input else 365
    else:
        target_days = 365
    
    logger.info(f"\n선택: 최근 {target_days}일 ({target_days/365:.2f}년)")
    
    try:
        crawler = NaverStockDiscussionCrawler()
        df = crawler.crawl_discussion_feed(target_days=target_days, max_scrolls=200)
        
        if len(df) == 0:
            logger.error("\n크롤링 실패: 데이터 없음")
            return
        
        # 저장
        output_path = './data/raw/discussion_data.csv'
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"\n✅ 저장 완료: {output_path}")
        logger.info(f"총 {len(df):,}개 게시글 수집")
        
        # 샘플 출력
        logger.info(f"\n샘플 데이터 (최근 5개):")
        sample_cols = ['종목명', '닉네임', '작성시간', '제목']
        print("\n" + df.head(5)[sample_cols].to_string(index=False))
        
        logger.info("\n" + "="*80)
        logger.info("크롤링 성공! ✅")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"\n크롤링 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
