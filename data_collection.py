"""
데이터 수집 및 기술적 지표 계산 (MultiIndex 수정 버전)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCollector:
    """데이터 수집 및 지표 계산"""
    
    def __init__(self, start_date='2021-01-01', end_date='2024-12-31'):
        self.start_date = start_date
        self.end_date = end_date
        
    def get_etf_data_yfinance(self, ticker, name):
        """
        yfinance로 ETF 데이터 수집 (MultiIndex 수정)
        """
        logger.info(f"{name} 데이터 수집: {ticker}")
        
        ticker_symbol = f"{ticker}.KS"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"다운로드 시도 {attempt+1}/{max_retries}: {ticker_symbol}")
                
                # yfinance 다운로드
                df = yf.download(
                    ticker_symbol,
                    start=self.start_date,
                    end=self.end_date,
                    progress=False
                )
                
                if df.empty:
                    logger.warning(f"데이터 없음: {ticker_symbol}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return None
                
                logger.info(f"다운로드 성공: {ticker_symbol}")
                
                # MultiIndex 처리 (핵심 수정!)
                if isinstance(df.columns, pd.MultiIndex):
                    # MultiIndex인 경우 첫 번째 레벨만 사용
                    df.columns = df.columns.get_level_values(0)
                
                # 컬럼명 정리
                df.columns = [str(col).strip() for col in df.columns]
                
                # 인덱스를 Date 컬럼으로
                df.reset_index(inplace=True)
                
                # 필요한 컬럼만 선택
                required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                available_cols = [col for col in required_cols if col in df.columns]
                
                if 'Close' not in available_cols:
                    logger.error(f"Close 컬럼 없음: {available_cols}")
                    return None
                
                df = df[available_cols].copy()
                
                # 기술적 지표 계산
                df = self.calculate_technical_indicators(df)
                
                # Returns 컬럼 추가
                if 'Returns' not in df.columns:
                    df['Returns'] = df['Close'].pct_change()
                
                # NaN 제거
                df = df.dropna()
                
                logger.info(f"데이터 처리 완료: {len(df)}행, {len(df.columns)}컬럼")
                return df
                
            except Exception as e:
                logger.error(f"다운로드 실패 (시도 {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    logger.error("최대 재시도 횟수 초과")
                    return None
        
        return None
    
    def calculate_technical_indicators(self, df):
        """기술적 지표 계산"""
        
        # 이동평균 (MA)
        df['MA_5'] = df['Close'].rolling(window=5).mean()
        df['MA_10'] = df['Close'].rolling(window=10).mean()
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['MA_60'] = df['Close'].rolling(window=60).mean()
        df['MA_120'] = df['Close'].rolling(window=120).mean()
        
        # MACD
        ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # 볼린저 밴드
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Stochastic
        low_14 = df['Low'].rolling(window=14).min()
        high_14 = df['High'].rolling(window=14).max()
        df['Stochastic'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
        
        return df
    
    def create_sample_data(self, ticker, name):
        """샘플 데이터 생성 (yfinance 실패 시)"""
        logger.warning(f"{name} 샘플 데이터 생성")
        
        # 날짜 범위
        date_range = pd.date_range(start=self.start_date, end=self.end_date, freq='B')
        
        # Random Walk 시뮬레이션
        np.random.seed(42)
        initial_price = 40000
        returns = np.random.normal(0.0005, 0.015, len(date_range))
        prices = initial_price * (1 + returns).cumprod()
        
        # OHLCV 생성
        df = pd.DataFrame({
            'Date': date_range,
            'Open': prices * (1 + np.random.uniform(-0.01, 0.01, len(date_range))),
            'High': prices * (1 + np.random.uniform(0, 0.02, len(date_range))),
            'Low': prices * (1 + np.random.uniform(-0.02, 0, len(date_range))),
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, len(date_range))
        })
        
        # 기술적 지표
        df = self.calculate_technical_indicators(df)
        
        # Returns
        df['Returns'] = df['Close'].pct_change()
        
        # NaN 제거
        df = df.dropna()
        
        logger.info(f"샘플 데이터 생성 완료: {len(df)}행")
        return df


def main():
    """메인 실행"""
    
    os.makedirs('./data/processed', exist_ok=True)
    
    logger.info(f"데이터 수집 기간: 2021-01-01 ~ 2024-12-31")
    logger.info("\n" + "="*80)
    logger.info("데이터 수집 시작 (Rate Limit 대응 모드)")
    logger.info("="*80)
    
    collector = DataCollector(start_date='2021-01-01', end_date='2024-12-31')
    
    # KODEX 200
    logger.info("\n[1/2] KODEX 200 (069500)")
    kodex200_df = collector.get_etf_data_yfinance('069500', 'KODEX 200')
    
    if kodex200_df is None:
        logger.warning("KODEX 200 다운로드 실패 - 샘플 데이터 사용")
        kodex200_df = collector.create_sample_data('069500', 'KODEX 200')
    
    # 저장
    output_path = './data/processed/kodex200_full_features.csv'
    kodex200_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"저장 완료: {output_path}")
    
    # KODEX KOSDAQ 150
    logger.info("\n[2/2] KODEX KOSDAQ 150 (229200)")
    kosdaq150_df = collector.get_etf_data_yfinance('229200', 'KODEX KOSDAQ 150')
    
    if kosdaq150_df is None:
        logger.warning("KODEX KOSDAQ 150 다운로드 실패 - 샘플 데이터 사용")
        kosdaq150_df = collector.create_sample_data('229200', 'KODEX KOSDAQ 150')
    
    # 저장
    output_path2 = './data/processed/kodex_kosdaq150_full_features.csv'
    kosdaq150_df.to_csv(output_path2, index=False, encoding='utf-8-sig')
    logger.info(f"저장 완료: {output_path2}")
    
    # 통계
    logger.info("\n" + "="*80)
    logger.info("데이터 수집 완료")
    logger.info("="*80)
    logger.info(f"KODEX 200: {len(kodex200_df)}행, {len(kodex200_df.columns)}컬럼")
    logger.info(f"KODEX KOSDAQ 150: {len(kosdaq150_df)}행, {len(kosdaq150_df.columns)}컬럼")
    
    logger.info("\n컬럼:")
    logger.info(f"  {', '.join(kodex200_df.columns.tolist())}")


if __name__ == "__main__":
    main()
