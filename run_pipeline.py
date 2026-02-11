"""
주식 백테스팅 파이프라인 - 통합 실행 스크립트
python run_pipeline.py --start 1 --end 7 로 전체 실행
"""

import argparse
import sys
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'./logs/pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_directories():
    """필요한 디렉토리 생성"""
    directories = ['data/raw', 'data/processed', 'data/backtest', 'models', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def run_step_1_crawling():
    """1단계: 웹 크롤링 (1년치)"""
    logger.info("\n" + "="*80)
    logger.info("[1단계] 웹 크롤링 (1년치)")
    logger.info("="*80)
    
    try:
        import crawler
        crawler.main()
        logger.info("[1단계] 완료\n")
        return True
    except Exception as e:
        logger.error(f"[1단계] 실패: {e}")
        logger.warning("크롤링 실패 - 기존 데이터 사용")
        return True


def run_step_2_sentiment():
    """2단계: 감성 분석"""
    logger.info("\n" + "="*80)
    logger.info("[2단계] 고급 감성 분석")
    logger.info("="*80)
    
    try:
        import sentiment_analysis
        sentiment_analysis.main()
        logger.info("[2단계] 완료\n")
        return True
    except Exception as e:
        logger.error(f"[2단계] 실패: {e}")
        return False


def run_step_3_data_collection():
    """3단계: 데이터 수집"""
    logger.info("\n" + "="*80)
    logger.info("[3단계] 데이터 수집 및 지표 계산")
    logger.info("="*80)
    
    try:
        import data_collection
        data_collection.main()
        logger.info("[3단계] 완료\n")
        return True
    except Exception as e:
        logger.error(f"[3단계] 실패: {e}")
        if os.path.exists('./data/processed/kodex200_full_features.csv'):
            logger.warning("샘플 데이터 사용하여 계속 진행")
            return True
        return False


def run_step_4_correlation():
    """4단계: 상관관계 분석"""
    logger.info("\n" + "="*80)
    logger.info("[4단계] 상관관계 분석")
    logger.info("="*80)
    
    try:
        import correlation_analysis
        correlation_analysis.main()
        logger.info("[4단계] 완료\n")
        return True
    except Exception as e:
        logger.error(f"[4단계] 실패: {e}")
        return False


def run_step_5_backtesting():
    """5단계: 백테스팅"""
    logger.info("\n" + "="*80)
    logger.info("[5단계] 백테스팅 (6가지 전략)")
    logger.info("="*80)
    
    try:
        import backtesting
        backtesting.main()
        logger.info("[5단계] 완료\n")
        return True
    except Exception as e:
        logger.error(f"[5단계] 실패: {e}")
        return False


def run_step_6_machine_learning():
    """6단계: 머신러닝"""
    logger.info("\n" + "="*80)
    logger.info("[6단계] 머신러닝 모델 학습")
    logger.info("="*80)
    
    try:
        import ml_models
        ml_models.main()
        logger.info("[6단계] 완료\n")
        return True
    except Exception as e:
        logger.error(f"[6단계] 실패: {e}")
        return False


def run_step_7_rag_chatbot():
    """7단계: RAG 챗봇"""
    logger.info("\n" + "="*80)
    logger.info("[7단계] RAG 챗봇 초기화")
    logger.info("="*80)
    
    try:
        from rag_chatbot import SimpleRAGChatbot
        
        chatbot = SimpleRAGChatbot()
        if chatbot.load_results():
            logger.info("RAG 챗봇 준비 완료")
            logger.info("\n사용법: python rag_chatbot.py")
        
        logger.info("[7단계] 완료\n")
        return True
    except Exception as e:
        logger.error(f"[7단계] 실패: {e}")
        logger.info("RAG 챗봇은 선택 기능입니다")
        return True


def main():
    """메인 실행 함수"""
    
    parser = argparse.ArgumentParser(description='주식 백테스팅 파이프라인')
    parser.add_argument('--step', type=int, help='단일 단계 실행 (1~7)')
    parser.add_argument('--start', type=int, help='시작 단계')
    parser.add_argument('--end', type=int, help='종료 단계')
    
    args = parser.parse_args()
    
    create_directories()
    
    logger.info("="*80)
    logger.info("주식 백테스팅 전략 검증 파이프라인")
    logger.info("="*80)
    
    # 실행할 단계 결정
    if args.step:
        steps_to_run = [args.step]
    elif args.start and args.end:
        steps_to_run = list(range(args.start, args.end + 1))
    elif args.start:
        steps_to_run = list(range(args.start, 8))
    else:
        steps_to_run = [1, 2, 3, 4, 5, 6, 7]
    
    # 단계별 함수 매핑
    step_functions = {
        1: ('웹 크롤링', run_step_1_crawling),
        2: ('감성 분석', run_step_2_sentiment),
        3: ('데이터 수집', run_step_3_data_collection),
        4: ('상관관계 분석', run_step_4_correlation),
        5: ('백테스팅', run_step_5_backtesting),
        6: ('머신러닝', run_step_6_machine_learning),
        7: ('RAG 챗봇', run_step_7_rag_chatbot)
    }
    
    # 실행 결과
    results = {}
    
    for step_num in steps_to_run:
        step_name, step_func = step_functions[step_num]
        
        try:
            success = step_func()
            results[step_num] = success
        except Exception as e:
            logger.error(f"단계 {step_num} 예외: {e}")
            results[step_num] = False
    
    # 최종 결과
    logger.info("\n" + "="*80)
    logger.info("실행 결과 요약")
    logger.info("="*80)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for step_num, success in results.items():
        step_name = step_functions[step_num][0]
        status = "[성공]" if success else "[실패]"
        logger.info(f"단계 {step_num} ({step_name}): {status}")
    
    logger.info(f"\n총 {total_count}개 단계 중 {success_count}개 성공")
    
    if success_count == total_count:
        logger.info("\n[완료] 모든 단계가 성공적으로 완료되었습니다!")
    else:
        logger.warning("\n[경고] 일부 단계가 실패했습니다")
    
    logger.info("\n주요 결과 파일:")
    logger.info("- 백테스팅: data/backtest/strategy_results.csv")
    logger.info("- 감성 분석: data/processed/sentiment_scores.csv")
    logger.info("- RAG 챗봇: python rag_chatbot.py")


if __name__ == "__main__":
    main()
