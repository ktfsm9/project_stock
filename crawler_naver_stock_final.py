"""
네이버 주식 토론 피드 크롤러
https://stock.naver.com/discussion/feed/all
무한 스크롤 지원
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime
import time
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NaverStockDiscussionCrawler:
    """네이버 주식 토론 피드 크롤러"""
    
    def __init__(self):
        self.url = "https://stock.naver.com/discussion/feed/all"
        
        # Chrome 옵션
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 디버깅 시 주석
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        logger.info("ChromeDriver 자동 설치 및 시작...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
        self.posts_collected = set()  # 중복 방지
    
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
            # 페이지 끝까지 스크롤
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # 로딩 대기
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
    
    def crawl_visible_posts(self):
        """현재 보이는 모든 게시글 크롤링"""
        posts = []
        
        # 현재 로드된 게시글 개수
        total_posts = self.get_current_posts_count()
        logger.info(f"  로드된 게시글: {total_posts}개")
        
        # 모든 게시글 순회
        for i in range(1, total_posts + 1):
            try:
                base_xpath = f'//*[@id="tabpanel-all"]/div[2]/ul/li[{i}]'
                
                # 제목 (필수 - 고유 ID로 사용)
                title_xpath = f'{base_xpath}/div[3]/div/a/strong'
                title = self._get_element_text(title_xpath)
                
                if title == 'N/A' or not title:
                    continue
                
                # 중복 체크 (제목 + 시간)
                time_xpath = f'{base_xpath}/div[2]/div/button/ul/li/span[2]'
                write_time = self._get_element_text(time_xpath)
                
                post_id = f"{title}_{write_time}"
                if post_id in self.posts_collected:
                    continue  # 이미 수집한 게시글
                
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
        
        return posts
    
    def crawl_discussion_feed(self, target_count=500, max_scrolls=50):
        """
        토론 피드 크롤링
        
        Args:
            target_count: 목표 게시글 수 (기본 500개)
            max_scrolls: 최대 스크롤 횟수 (기본 50)
        """
        all_posts = []
        
        logger.info("="*80)
        logger.info("네이버 주식 토론 피드 크롤링")
        logger.info(f"URL: {self.url}")
        logger.info(f"목표: {target_count}개, 최대 스크롤: {max_scrolls}회")
        logger.info("="*80)
        
        try:
            # 페이지 로드
            logger.info("\n페이지 로딩...")
            self.driver.get(self.url)
            
            # 초기 로딩 대기
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
            no_new_posts_count = 0
            
            while scroll_count < max_scrolls and len(self.posts_collected) < target_count:
                scroll_count += 1
                
                logger.info(f"\n[스크롤 {scroll_count}/{max_scrolls}]")
                
                # 현재 보이는 게시글 크롤링
                new_posts = self.crawl_visible_posts()
                
                if new_posts:
                    all_posts.extend(new_posts)
                    no_new_posts_count = 0
                    logger.info(f"  새 게시글: {len(new_posts)}개")
                    logger.info(f"  누적: {len(self.posts_collected)}개 (목표: {target_count}개)")
                else:
                    no_new_posts_count += 1
                    logger.info("  새 게시글 없음")
                
                # 연속으로 새 게시글이 없으면 종료
                if no_new_posts_count >= 3:
                    logger.info("더 이상 새 게시글이 없습니다.")
                    break
                
                # 목표 달성
                if len(self.posts_collected) >= target_count:
                    logger.info(f"목표 달성! ({len(self.posts_collected)}개)")
                    break
                
                # 스크롤 다운
                logger.info("  스크롤 중...")
                self.scroll_down()
            
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
            logger.info(f"작성시간 'N/A': {(df['작성시간'] == 'N/A').sum()}개 ({(df['작성시간'] == 'N/A').sum()/len(df)*100:.1f}%)")
            logger.info(f"내용 '내용 없음': {(df['내용'] == '내용 없음').sum()}개 ({(df['내용'] == '내용 없음').sum()/len(df)*100:.1f}%)")
            
            # 완전한 게시글
            complete = df[
                (df['종목명'] != 'N/A') &
                (df['닉네임'] != 'N/A') & 
                (df['작성시간'] != 'N/A') &
                (df['내용'] != '내용 없음') &
                (df['내용'].str.len() > 10)
            ]
            logger.info(f"완전한 게시글: {len(complete)}개 ({len(complete)/len(df)*100:.1f}%)")
            
            # 종목별 통계
            if '종목명' in df.columns:
                logger.info("\n=== 종목별 게시글 ===")
                stock_counts = df[df['종목명'] != 'N/A']['종목명'].value_counts().head(10)
                for stock, count in stock_counts.items():
                    logger.info(f"  {stock}: {count}개")
        
        return df


def main():
    """메인 실행"""
    
    os.makedirs('./data/raw', exist_ok=True)
    
    logger.info("="*80)
    logger.info("네이버 주식 토론 피드 크롤러")
    logger.info("https://stock.naver.com/discussion/feed/all")
    logger.info("="*80)
    logger.info("\n[주의]")
    logger.info("- Chrome 브라우저가 자동으로 열립니다")
    logger.info("- 크롤링 중에는 창을 닫지 마세요")
    logger.info("- 무한 스크롤로 게시글을 로드합니다")
    logger.info("- Ctrl+C로 언제든지 중단 가능\n")
    
    # 사용자 설정
    target_count = input("목표 게시글 수 (기본 500개, Enter): ").strip()
    target_count = int(target_count) if target_count else 500
    
    try:
        crawler = NaverStockDiscussionCrawler()
        df = crawler.crawl_discussion_feed(target_count=target_count, max_scrolls=100)
        
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
        
        # 내용 샘플
        has_content = df[df['내용'] != '내용 없음'].head(3)
        if len(has_content) > 0:
            logger.info(f"\n내용 샘플 (3개):")
            for idx, row in has_content.iterrows():
                logger.info(f"\n[{idx+1}] 종목: {row['종목명']}, 제목: {row['제목']}")
                logger.info(f"닉네임: {row['닉네임']}, 작성시간: {row['작성시간']}")
                logger.info(f"내용: {str(row['내용'])[:150]}...")
        
        logger.info("\n" + "="*80)
        logger.info("크롤링 성공! ✅")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"\n크롤링 실패: {e}")
        logger.error("\n해결 방법:")
        logger.error("1. pip install selenium webdriver-manager")
        logger.error("2. Chrome 브라우저 최신 버전 확인")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
