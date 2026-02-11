"""
간단한 백테스팅 엔진 (샘플 데이터용)
- Returns 컬럼 자동 생성
- 누락된 이동평균 자동 계산
- 5가지 전략 백테스팅
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
import os
import warnings

warnings.filterwarnings('ignore')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


class SimpleBacktesting:
    """간단한 백테스팅 엔진"""
    
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.commission = 0.00015  # 0.015%
        self.slippage = 0.0005     # 0.05%
        
    def prepare_data(self, df):
        """데이터 준비 - Returns 및 누락된 지표 계산"""
        df = df.copy()
        
        # Returns 계산
        df['Returns'] = df['Close'].pct_change()
        
        # MA_200 계산 (없으면)
        if 'MA_200' not in df.columns:
            df['MA_200'] = df['Close'].rolling(window=200).mean()
        
        logger.info(f"데이터 준비 완료: {len(df)}행, {len(df.columns)}컬럼")
        return df
    
    def calculate_performance(self, df, signals):
        """성과 지표 계산"""
        # 포지션 계산
        df['Position'] = signals
        df['Strategy_Returns'] = df['Position'].shift(1) * df['Returns']
        
        # 거래 비용 반영
        df['Trades'] = df['Position'].diff().abs()
        df['Strategy_Returns'] = df['Strategy_Returns'] - (df['Trades'] * (self.commission + self.slippage))
        
        # 누적 수익률
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        df['Buy_Hold_Returns'] = (1 + df['Returns']).cumprod()
        
        # 성과 지표
        total_return = df['Cumulative_Returns'].iloc[-1] - 1
        buy_hold_return = df['Buy_Hold_Returns'].iloc[-1] - 1
        
        # 연율화 (4년 데이터 가정)
        years = len(df) / 252
        annual_return = (1 + total_return) ** (1/years) - 1
        
        # 샤프 비율
        sharpe = df['Strategy_Returns'].mean() / df['Strategy_Returns'].std() * np.sqrt(252)
        
        # 최대 낙폭 (MDD)
        cummax = df['Cumulative_Returns'].cummax()
        drawdown = (df['Cumulative_Returns'] - cummax) / cummax
        mdd = drawdown.min()
        
        # 승률
        winning_trades = (df['Strategy_Returns'] > 0).sum()
        total_trades = df['Trades'].sum() / 2  # 매수+매도 = 1거래
        win_rate = winning_trades / len(df) if len(df) > 0 else 0
        
        return {
            'Total_Return': total_return * 100,
            'Annual_Return': annual_return * 100,
            'Buy_Hold_Return': buy_hold_return * 100,
            'Sharpe_Ratio': sharpe,
            'Max_Drawdown': mdd * 100,
            'Win_Rate': win_rate * 100,
            'Total_Trades': int(total_trades),
            'Final_Capital': self.initial_capital * (1 + total_return)
        }
    
    def strategy_ma_cross(self, df, short=5, long=20):
        """이동평균 크로스오버 전략"""
        signals = pd.Series(0, index=df.index)
        
        if f'MA_{short}' in df.columns and f'MA_{long}' in df.columns:
            signals[df[f'MA_{short}'] > df[f'MA_{long}']] = 1
        
        return signals
    
    def strategy_rsi(self, df, oversold=30, overbought=70):
        """RSI 전략"""
        signals = pd.Series(0, index=df.index)
        
        if 'RSI' in df.columns:
            signals[df['RSI'] < oversold] = 1
            signals[df['RSI'] > overbought] = -1
            signals = signals.replace(-1, 0)  # 공매도 제외
        
        return signals
    
    def strategy_macd(self, df):
        """MACD 전략"""
        signals = pd.Series(0, index=df.index)
        
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            signals[df['MACD'] > df['MACD_Signal']] = 1
        
        return signals
    
    def strategy_bollinger(self, df):
        """볼린저 밴드 평균 회귀 전략"""
        signals = pd.Series(0, index=df.index)
        
        if all(col in df.columns for col in ['Close', 'BB_Lower', 'BB_Upper', 'BB_Middle']):
            # 하단 돌파 시 매수
            signals[df['Close'] < df['BB_Lower']] = 1
            # 중간선 도달 시 매도 (일단 보유)
        
        return signals
    
    def strategy_multi_factor(self, df):
        """멀티 팩터 전략 (MA + RSI + MACD)"""
        signals = pd.Series(0, index=df.index)
        
        # 3가지 조건 모두 만족
        ma_cond = df['MA_5'] > df['MA_20'] if 'MA_5' in df.columns and 'MA_20' in df.columns else False
        rsi_cond = (df['RSI'] > 30) & (df['RSI'] < 70) if 'RSI' in df.columns else False
        macd_cond = df['MACD'] > df['MACD_Signal'] if 'MACD' in df.columns and 'MACD_Signal' in df.columns else False
        
        signals[ma_cond & rsi_cond & macd_cond] = 1
        
        return signals
    
    def run_all_strategies(self, df):
        """모든 전략 실행"""
        df = self.prepare_data(df)
        
        strategies = {
            'MA_Cross_5_20': lambda: self.strategy_ma_cross(df, 5, 20),
            'MA_Cross_10_60': lambda: self.strategy_ma_cross(df, 10, 60),
            'RSI_30_70': lambda: self.strategy_rsi(df, 30, 70),
            'MACD': lambda: self.strategy_macd(df),
            'Bollinger': lambda: self.strategy_bollinger(df),
            'Multi_Factor': lambda: self.strategy_multi_factor(df)
        }
        
        results = []
        
        for name, strategy_func in strategies.items():
            try:
                logger.info(f"{name} 전략 백테스팅 시작")
                
                signals = strategy_func()
                perf = self.calculate_performance(df.copy(), signals)
                perf['Strategy'] = name
                results.append(perf)
                
                logger.info(f"{name} 완료: 수익률 {perf['Total_Return']:.2f}%, 샤프 {perf['Sharpe_Ratio']:.2f}")
                
            except Exception as e:
                logger.error(f"{name} 실패: {e}")
        
        return pd.DataFrame(results)


def main():
    """메인 실행 함수"""
    
    try:
        # 디렉토리 생성
        os.makedirs('./data/backtest', exist_ok=True)
        
        logger.info("="*80)
        logger.info("간단한 백테스팅 시작")
        logger.info("="*80)
        
        # 데이터 로드
        data_path = './data/processed/kodex200_full_features.csv'
        df = pd.read_csv(data_path)
        logger.info(f"데이터 로드: {data_path} ({len(df)}행)")
        
        # 백테스팅 실행
        engine = SimpleBacktesting(initial_capital=1000000)
        results = engine.run_all_strategies(df)
        
        # 결과 저장
        output_path = './data/backtest/strategy_results.csv'
        results.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"\n결과 저장: {output_path}")
        
        # 결과 출력
        logger.info("\n" + "="*80)
        logger.info("백테스팅 결과 요약")
        logger.info("="*80)
        
        results_sorted = results.sort_values('Sharpe_Ratio', ascending=False)
        
        print("\n전략별 성과:")
        print(results_sorted[[
            'Strategy', 'Total_Return', 'Annual_Return', 
            'Sharpe_Ratio', 'Max_Drawdown', 'Win_Rate', 'Total_Trades'
        ]].to_string(index=False))
        
        # 최고 전략
        best = results_sorted.iloc[0]
        logger.info(f"\n최고 전략: {best['Strategy']}")
        logger.info(f"  총 수익률: {best['Total_Return']:.2f}%")
        logger.info(f"  연간 수익률: {best['Annual_Return']:.2f}%")
        logger.info(f"  샤프 비율: {best['Sharpe_Ratio']:.2f}")
        logger.info(f"  최대 낙폭: {best['Max_Drawdown']:.2f}%")
        logger.info(f"  승률: {best['Win_Rate']:.2f}%")
        logger.info(f"  최종 자본: {best['Final_Capital']:,.0f}원")
        
        # 시각화
        logger.info("\n차트 생성 중...")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 수익률 비교
        ax1 = axes[0, 0]
        results_sorted.plot(x='Strategy', y='Total_Return', kind='bar', ax=ax1, color='skyblue')
        ax1.set_title('전략별 총 수익률', fontsize=14, fontweight='bold')
        ax1.set_ylabel('수익률 (%)')
        ax1.set_xlabel('')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        # 2. 샤프 비율
        ax2 = axes[0, 1]
        results_sorted.plot(x='Strategy', y='Sharpe_Ratio', kind='bar', ax=ax2, color='lightgreen')
        ax2.set_title('전략별 샤프 비율', fontsize=14, fontweight='bold')
        ax2.set_ylabel('샤프 비율')
        ax2.set_xlabel('')
        ax2.grid(True, alpha=0.3)
        
        # 3. MDD
        ax3 = axes[1, 0]
        results_sorted.plot(x='Strategy', y='Max_Drawdown', kind='bar', ax=ax3, color='salmon')
        ax3.set_title('전략별 최대 낙폭 (MDD)', fontsize=14, fontweight='bold')
        ax3.set_ylabel('MDD (%)')
        ax3.set_xlabel('')
        ax3.grid(True, alpha=0.3)
        
        # 4. 승률
        ax4 = axes[1, 1]
        results_sorted.plot(x='Strategy', y='Win_Rate', kind='bar', ax=ax4, color='gold')
        ax4.set_title('전략별 승률', fontsize=14, fontweight='bold')
        ax4.set_ylabel('승률 (%)')
        ax4.set_xlabel('')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        chart_path = './data/backtest/strategy_comparison.png'
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        logger.info(f"차트 저장: {chart_path}")
        
        logger.info("\n" + "="*80)
        logger.info("백테스팅 완료!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"백테스팅 중 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
