"""
네이버 증권 토론방 크롤러 (XPath 기반 Selenium)
ChromeDriver 자동 설치 버전
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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


class NpayStockCrawler:
    """Npay 증권 크롤러 (XPath 기반)"""
    
    def __init__(self, stock_code='005930'):
        self.stock_code = stock_code
        self.base_url = f"https://finance.naver.com/item/board.naver?code={stock_code}"
        
        # Chrome 옵션
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 백그라운드 실행
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        logger.info("ChromeDriver 자동 설치 및 Chrome 시작...")
        # ChromeDriver 자동 설치
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
    
    def _get_element_text(self, xpath, default='N/A'):
        """XPath로 요소 텍스트 가져오기"""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            text = element.text.strip()
            return text if text else default
        except:
            return default
    
    def crawl_page(self, page=1):
        """페이지 크롤링"""
        url = f"{self.base_url}&page={page}"
        logger.info(f"페이지 {page} 로딩...")
        
        try:
            self.driver.get(url)
            time.sleep(3)  # 페이지 로딩 대기
            
            # 게시글 리스트 대기
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="tabpanel-all"]/div[2]/ul'))
            )
            
            posts = []
            
            # 게시글 순회 (최대 24개)
            for i in range(1, 25):
                try:
                    base_xpath = f'//*[@id="tabpanel-all"]/div[2]/ul/li[{i}]'
                    
                    # 제목 (필수)
                    title = self._get_element_text(f'{base_xpath}/div[3]/div/a/strong')
                    if title == 'N/A':
                        break  # 더 이상 게시글 없음
                    
                    # 닉네임
                    nickname = self._get_element_text(f'{base_xpath}/div[2]/div/div/button/span')
                    
                    # 작성시간
                    write_time = self._get_element_text(f'{base_xpath}/div[2]/div/button/ul/li/span[2]')
                    
                    # 내용
                    content = self._get_element_text(f'{base_xpath}/div[3]/div/a/div/p', default='내용 없음')
                    
                    posts.append({
                        '닉네임': nickname,
                        '작성시간': write_time,
                        '제목': title,
                        '내용': content,
                        '크롤링일자': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                except:
                    continue
            
            logger.info(f"  수집: {len(posts)}개")
            return posts
            
        except Exception as e:
            logger.error(f"페이지 {page} 오류: {e}")
            return []
    
    def crawl_discussion_board(self, max_pages=50, delay=3):
        """토론방 크롤링"""
        all_posts = []
        
        logger.info("="*80)
        logger.info(f"크롤링 시작: {self.stock_code}")
        logger.info(f"최대 페이지: {max_pages}, 지연: {delay}초")
        logger.info("="*80)
        
        try:
            for page in range(1, max_pages + 1):
                posts = self.crawl_page(page)
                
                if not posts:
                    logger.warning(f"페이지 {page}: 게시글 없음 - 종료")
                    break
                
                all_posts.extend(posts)
                
                if page % 5 == 0:
                    logger.info(f"진행: {page}/{max_pages} 페이지, 총 {len(all_posts)}개")
                
                time.sleep(delay)
            
        except KeyboardInterrupt:
            logger.warning("사용자 중단")
        finally:
            self.driver.quit()
        
        logger.info(f"\n완료: 총 {len(all_posts)}개")
        return self._create_dataframe(all_posts)
    
    def _create_dataframe(self, posts):
        """DataFrame 생성"""
        df = pd.DataFrame(posts)
        
        if len(df) > 0:
            df.insert(0, 'N', range(1, len(df) + 1))
            
            logger.info("\n=== 데이터 품질 ===")
            logger.info(f"총: {len(df)}개")
            logger.info(f"닉네임 N/A: {(df['닉네임'] == 'N/A').sum()}개 ({(df['닉네임'] == 'N/A').sum()/len(df)*100:.1f}%)")
            logger.info(f"내용 없음: {(df['내용'] == '내용 없음').sum()}개 ({(df['내용'] == '내용 없음').sum()/len(df)*100:.1f}%)")
            
            complete = df[(df['닉네임'] != 'N/A') & (df['내용'] != '내용 없음')]
            logger.info(f"완전: {len(complete)}개 ({len(complete)/len(df)*100:.1f}%)")
        
        return df


def main():
    """메인"""
    os.makedirs('./data/raw', exist_ok=True)
    
    logger.info("="*80)
    logger.info("네이버 증권 크롤러 - XPath + Selenium (자동 설치)")
    logger.info("="*80)
    
    try:
        crawler = NpayStockCrawler(stock_code='005930')
        df = crawler.crawl_discussion_board(max_pages=50, delay=3)
        
        if len(df) == 0:
            logger.error("크롤링 실패")
            return
        
        # 저장
        output_path = './data/raw/discussion_data.csv'
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"\n저장: {output_path}")
        
        # 샘플
        logger.info(f"\n샘플 (5개):")
        print(df.head(5)[['닉네임', '작성시간', '제목']].to_string(index=False))
        
        logger.info("\n크롤링 성공! ✅")
        
    except Exception as e:
        logger.error(f"실패: {e}")
        logger.error("\n해결: pip install selenium webdriver-manager")


if __name__ == "__main__":
    main()
