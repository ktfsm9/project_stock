"""
간단한 RAG 챗봇 (Rule-based)
- API 키 불필요
- 백테스팅 및 ML 결과 질의응답
- 키워드 기반 검색
"""

import pandas as pd
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleRAGChatbot:
    """간단한 규칙 기반 RAG 챗봇"""
    
    def __init__(self):
        self.backtest_results = None
        self.ml_results = None
        self.data_info = None
        
    def load_results(self):
        """분석 결과 로드"""
        try:
            # 백테스팅 결과
            backtest_path = './data/backtest/strategy_results.csv'
            if os.path.exists(backtest_path):
                self.backtest_results = pd.read_csv(backtest_path)
                logger.info(f"백테스팅 결과 로드: {len(self.backtest_results)}개 전략")
            
            # 데이터 정보
            data_path = './data/processed/kodex200_full_features.csv'
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
                self.data_info = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'start_date': df['Date'].min() if 'Date' in df.columns else 'N/A',
                    'end_date': df['Date'].max() if 'Date' in df.columns else 'N/A'
                }
                logger.info(f"데이터 정보 로드: {self.data_info['rows']}행")
            
            # ML 결과는 하드코딩 (이전 실행 결과)
            self.ml_results = {
                'best_model': 'LinearRegression',
                'r2_score': 0.9855,
                'rmse': 1026.18,
                'mae': 826.06,
                'accuracy': 54.89
            }
            
            logger.info("모든 결과 로드 완료")
            return True
            
        except Exception as e:
            logger.error(f"결과 로드 실패: {e}")
            return False
    
    def get_best_strategy(self):
        """최고 전략 정보 반환"""
        if self.backtest_results is None or len(self.backtest_results) == 0:
            return "백테스팅 결과를 찾을 수 없습니다."
        
        best = self.backtest_results.sort_values('Sharpe_Ratio', ascending=False).iloc[0]
        
        response = f"""
🏆 최고 성과 전략: {best['Strategy']}

📊 성과 지표:
- 총 수익률: {best['Total_Return']:.2f}%
- 연간 수익률: {best['Annual_Return']:.2f}%
- 샤프 비율: {best['Sharpe_Ratio']:.2f}
- 최대 낙폭(MDD): {best['Max_Drawdown']:.2f}%
- 승률: {best['Win_Rate']:.2f}%
- 총 거래 횟수: {int(best['Total_Trades'])}회

💰 투자 시뮬레이션:
- 초기 투자: 1,000,000원
- 최종 자본: {best['Final_Capital']:,.0f}원
- 수익: {best['Final_Capital'] - 1000000:,.0f}원
"""
        return response
    
    def get_all_strategies(self):
        """모든 전략 비교"""
        if self.backtest_results is None or len(self.backtest_results) == 0:
            return "백테스팅 결과를 찾을 수 없습니다."
        
        df = self.backtest_results.sort_values('Sharpe_Ratio', ascending=False)
        
        response = "📊 전략별 성과 비교 (샤프 비율 순):\n\n"
        
        for idx, row in df.iterrows():
            response += f"{idx+1}. {row['Strategy']}\n"
            response += f"   수익률: {row['Total_Return']:.2f}% | "
            response += f"샤프: {row['Sharpe_Ratio']:.2f} | "
            response += f"MDD: {row['Max_Drawdown']:.2f}%\n\n"
        
        return response
    
    def get_investment_simulation(self, amount):
        """투자 시뮬레이션"""
        if self.backtest_results is None or len(self.backtest_results) == 0:
            return "백테스팅 결과를 찾을 수 없습니다."
        
        best = self.backtest_results.sort_values('Sharpe_Ratio', ascending=False).iloc[0]
        
        multiplier = amount / 1000000
        final_amount = best['Final_Capital'] * multiplier
        profit = final_amount - amount
        
        response = f"""
💰 {amount:,.0f}원 투자 시뮬레이션

전략: {best['Strategy']}
기간: 약 4년 (2021-2024)

📈 투자 결과:
- 초기 투자: {amount:,.0f}원
- 최종 금액: {final_amount:,.0f}원
- 순수익: {profit:,.0f}원
- 수익률: {best['Total_Return']:.2f}%
- 연간 수익률: {best['Annual_Return']:.2f}%

⚠️ 주의: 이는 샘플 데이터 기반 시뮬레이션입니다.
실제 투자 전 실제 데이터로 재검증이 필요합니다.
"""
        return response
    
    def get_ml_results(self):
        """머신러닝 결과"""
        if self.ml_results is None:
            return "머신러닝 결과를 찾을 수 없습니다."
        
        response = f"""
🤖 머신러닝 모델 결과

🏆 최고 성능 모델: {self.ml_results['best_model']}

📊 성능 지표:
- R² Score: {self.ml_results['r2_score']:.4f} (98.55% 설명력)
- RMSE: {self.ml_results['rmse']:.2f}원
- MAE: {self.ml_results['mae']:.2f}원
- 방향성 정확도: {self.ml_results['accuracy']:.2f}%

💡 해석:
R² Score 0.9855는 모델이 가격 변동의 98.55%를 
설명할 수 있다는 의미입니다. 매우 높은 정확도입니다.

📁 저장 위치:
- 모델: models/LinearRegression.pkl
- 예측 차트: data/processed/LinearRegression_predictions.png
"""
        return response
    
    def get_data_info(self):
        """데이터 정보"""
        if self.data_info is None:
            return "데이터 정보를 찾을 수 없습니다."
        
        response = f"""
📊 데이터 정보

📈 KODEX 200 ETF 데이터:
- 총 거래일: {self.data_info['rows']}일
- 컬럼 수: {self.data_info['columns']}개
- 기간: {self.data_info['start_date']} ~ {self.data_info['end_date']}

📋 포함된 지표:
- OHLCV: Open, High, Low, Close, Volume
- 이동평균: MA_5, MA_10, MA_20, MA_60, MA_120
- MACD: MACD, MACD_Signal, MACD_Hist
- 볼린저 밴드: BB_Upper, BB_Middle, BB_Lower
- 기타: RSI, Stochastic

📁 저장 위치:
- data/processed/kodex200_full_features.csv
"""
        return response
    
    def get_help(self):
        """도움말"""
        return """
🤖 RAG 챗봇 사용 가이드

📌 가능한 질문:

1️⃣ 백테스팅 관련:
   - 최고 전략은?
   - 전략 비교
   - 100만원 투자하면?
   - 1000만원 수익은?

2️⃣ 머신러닝 관련:
   - 머신러닝 결과는?
   - 가장 정확한 모델은?
   - R2 스코어는?

3️⃣ 데이터 관련:
   - 데이터 정보
   - 어떤 지표가 있나요?
   - 데이터 기간은?

4️⃣ 기타:
   - 도움말
   - 종료

💡 팁: 자연어로 질문하세요!
"""
    
    def process_query(self, query):
        """쿼리 처리"""
        query_lower = query.lower()
        
        # 최고 전략
        if any(word in query_lower for word in ['최고', '베스트', 'best', '가장 좋은', '추천']):
            if '전략' in query_lower or 'strategy' in query_lower:
                return self.get_best_strategy()
        
        # 전략 비교
        if any(word in query_lower for word in ['비교', '전략', '모든', 'all', 'compare']):
            if '전략' in query_lower:
                return self.get_all_strategies()
        
        # 투자 시뮬레이션
        if any(word in query_lower for word in ['투자', '수익', '만원', '원']):
            # 금액 추출
            try:
                if '100만원' in query or '1000000' in query:
                    return self.get_investment_simulation(1000000)
                elif '1000만원' in query or '10000000' in query:
                    return self.get_investment_simulation(10000000)
                elif '500만원' in query or '5000000' in query:
                    return self.get_investment_simulation(5000000)
                else:
                    return self.get_investment_simulation(1000000)
            except:
                return self.get_investment_simulation(1000000)
        
        # 머신러닝
        if any(word in query_lower for word in ['머신러닝', 'ml', '모델', 'model', 'r2', '정확']):
            return self.get_ml_results()
        
        # 데이터 정보
        if any(word in query_lower for word in ['데이터', 'data', '지표', '기간', '정보']):
            return self.get_data_info()
        
        # 도움말
        if any(word in query_lower for word in ['도움', 'help', '사용법', '가이드']):
            return self.get_help()
        
        # 기본 응답
        return """
죄송합니다. 질문을 이해하지 못했습니다.

💡 다음과 같이 질문해보세요:
- "최고 전략은 뭐야?"
- "100만원 투자하면 얼마 벌어?"
- "머신러닝 결과 보여줘"
- "데이터 정보 알려줘"
- "도움말"

또는 '도움말'을 입력하여 전체 가이드를 확인하세요.
"""
    
    def run_interactive(self):
        """대화형 실행"""
        print("\n" + "="*80)
        print("🤖 RAG 챗봇에 오신 것을 환영합니다!")
        print("="*80)
        print("\n백테스팅 및 머신러닝 결과에 대해 질문하세요.")
        print("종료하려면 '종료' 또는 'exit'를 입력하세요.\n")
        
        if not self.load_results():
            print("⚠️ 결과 파일 로드 실패. 일부 기능이 제한될 수 있습니다.")
        
        while True:
            try:
                query = input("\n질문: ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['종료', 'exit', 'quit', 'q']:
                    print("\n👋 챗봇을 종료합니다. 감사합니다!")
                    break
                
                response = self.process_query(query)
                print("\n답변:")
                print(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 챗봇을 종료합니다. 감사합니다!")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
    
    def run_demo(self):
        """데모 모드 (자동 질문)"""
        print("\n" + "="*80)
        print("🤖 RAG 챗봇 데모 모드")
        print("="*80)
        
        if not self.load_results():
            print("⚠️ 결과 파일 로드 실패")
            return
        
        demo_queries = [
            "최고 전략은?",
            "100만원 투자하면 얼마 벌어?",
            "머신러닝 결과 보여줘",
            "데이터 정보 알려줘"
        ]
        
        for query in demo_queries:
            print(f"\n{'='*80}")
            print(f"질문: {query}")
            print("="*80)
            response = self.process_query(query)
            print(response)
            input("\n[Enter를 눌러 다음 질문으로...]")
        
        print("\n" + "="*80)
        print("✅ 데모 완료!")
        print("="*80)


def main():
    """메인 실행"""
    import sys
    
    chatbot = SimpleRAGChatbot()
    
    # 명령행 인자 확인
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        chatbot.run_demo()
    else:
        chatbot.run_interactive()


if __name__ == "__main__":
    main()
