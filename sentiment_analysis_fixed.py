"""
고급 감성 분석 시스템 (수정 버전)
- 불용어 제거
- 형태소 분석
- 감성 점수 계산 (긍정/부정/중립)
"""

import pandas as pd
import re
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """감성 분석기"""
    
    def __init__(self):
        # 불용어 사전
        self.stopwords = {
            '의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자', '에', '와', '한', '하다',
            '그', '저', '것', '수', '등', '년', '월', '일', '때', '더', '또', '및', '하', '게', '된', '할',
            '께', '께서', '에게', '한테', '부터', '밖에', '만', '조차', '마저',
            '위', '아래', '앞', '뒤', '여기', '거기', '저기', '어디', '무엇', '누구', '언제', '왜', '어떻게',
            '입니다', '합니다', '있습니다', '없습니다', '됩니다', '같습니다'
        }
        
        # 긍정 감성 사전 (확장)
        self.positive_words = {
            # 주식 관련 긍정어
            '상승': 2, '급등': 3, '폭등': 3, '쩜상': 3, '상한가': 3, '상한': 3,
            '수익': 2, '이익': 2, '순이익': 2, '영업이익': 2, '배당': 2, '배당금': 2,
            '성장': 2, '호재': 3, '대박': 3, '돌파': 2, '신고가': 3, '고가': 2,
            '강세': 2, '우상향': 2, '매수': 1, '매수세': 2, '수급': 1, '외인': 1,
            '올라': 2, '오른': 2, '오를': 2, '상승세': 2, '반등': 2,
            
            # 일반 긍정어
            '좋': 1, '좋다': 1, '좋은': 1, '좋네': 1, '좋아': 1,
            '최고': 2, '훌륭': 2, '우수': 2, '멋진': 2, '완벽': 2,
            '성공': 2, '승리': 2, '기쁨': 1, '행복': 2, '만족': 2,
            '희망': 1, '기대': 1, '믿': 1, '신뢰': 1, '확신': 2,
            '웃': 1, '즐거': 1, '화이팅': 2, '파이팅': 2, '응원': 1,
            
            # 추가 긍정어
            '빵': 2, '개꿀': 2, '꿀': 1, '존버': 1, '홀딩': 1,
            '가즈아': 2, '가자': 1, '갑니다': 1, '갑시다': 1,
            '개': 2, '쩐다': 2, '굿': 1, '좋겠': 1, '기대되': 1
        }
        
        # 부정 감성 사전 (확장)
        self.negative_words = {
            # 주식 관련 부정어
            '하락': -2, '급락': -3, '폭락': -3, '쩜하': -3, '하한가': -3, '하한': -3,
            '손실': -2, '적자': -2, '손해': -2, '악재': -3, '리스크': -1,
            '약세': -2, '하방': -2, '매도': -1, '매도세': -2, '물려': -2,
            '손절': -2, '청산': -1, '망했': -3, '망한': -3, '망해': -3,
            '떨어': -2, '내려': -2, '하락세': -2, '조정': -1,
            
            # 일반 부정어
            '나쁜': -1, '나빠': -1, '않': -1, '못': -1, '없': -1, '싫': -1,
            '실망': -2, '화': -2, '짜증': -2, '슬픔': -2, '불만': -2,
            '최악': -3, '끔찍': -3, '참담': -3, '절망': -3, '비참': -3,
            '실패': -2, '패배': -2, '위험': -2, '걱정': -1, '불안': -2,
            '두려': -2, '무서': -1, '조심': -1,
            
            # 추가 부정어
            '망': -3, '조지': -2, '박살': -3, '개판': -3, '쓰레기': -3,
            '죽': -2, '끝': -1, '안': -1, '아니': -1, '문제': -1,
            '멍청': -2, '바보': -2
        }
        
    def tokenize(self, text):
        """형태소 추출 (한글 1글자 이상, 숫자 제외)"""
        if not text or pd.isna(text):
            return []
        
        text = str(text)
        # 한글만 추출 (1글자 이상)
        words = re.findall(r'[가-힣]+', text)
        return words
    
    def remove_stopwords(self, words):
        """불용어 제거"""
        return [w for w in words if w not in self.stopwords and len(w) >= 2]
    
    def get_sentiment_score(self, word):
        """단어 감성 점수"""
        # 완전 일치
        if word in self.positive_words:
            return self.positive_words[word]
        if word in self.negative_words:
            return self.negative_words[word]
        
        # 부분 일치 (포함)
        for pos_word, score in self.positive_words.items():
            if pos_word in word:
                return score
            if word in pos_word and len(word) >= 2:
                return score
        
        for neg_word, score in self.negative_words.items():
            if neg_word in word:
                return score
            if word in neg_word and len(word) >= 2:
                return score
        
        return 0
    
    def analyze_text(self, text):
        """텍스트 감성 분석"""
        if not text or pd.isna(text) or text == '내용 없음':
            return {
                'morphemes': [],
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'total_score': 0,
                'sentiment': '중립',
                'confidence': 0
            }
        
        # 형태소 추출 및 불용어 제거
        words = self.tokenize(text)
        morphemes = self.remove_stopwords(words)
        
        # 감성 점수 계산
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        total_score = 0
        
        for word in morphemes:
            score = self.get_sentiment_score(word)
            total_score += score
            
            if score > 0:
                positive_count += 1
            elif score < 0:
                negative_count += 1
            else:
                neutral_count += 1
        
        # 감성 판단
        if positive_count > negative_count:
            sentiment = '긍정'
        elif negative_count > positive_count:
            sentiment = '부정'
        else:
            if total_score > 0:
                sentiment = '긍정'
            elif total_score < 0:
                sentiment = '부정'
            else:
                sentiment = '중립'
        
        # 신뢰도 계산
        total_morphemes = len(morphemes) if morphemes else 1
        sentiment_morphemes = positive_count + negative_count
        confidence = sentiment_morphemes / total_morphemes if total_morphemes > 0 else 0
        
        return {
            'morphemes': morphemes[:10],  # 상위 10개만
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'total_score': total_score,
            'sentiment': sentiment,
            'confidence': round(confidence, 3)
        }
    
    def analyze_dataframe(self, df, text_column='내용'):
        """DataFrame 전체 감성 분석"""
        results = []
        
        logger.info(f"감성 분석 시작: {len(df)}개 문장")
        
        for idx, row in df.iterrows():
            text = row[text_column]
            result = self.analyze_text(text)
            results.append(result)
            
            if (idx + 1) % 100 == 0:
                logger.info(f"진행: {idx+1}/{len(df)}")
        
        logger.info("감성 분석 완료")
        return results


def main():
    """메인 실행"""
    os.makedirs('./data/processed', exist_ok=True)
    
    logger.info("="*80)
    logger.info("고급 감성 분석 시스템")
    logger.info("="*80)
    
    # 데이터 로드
    input_path = './data/raw/discussion_data.csv'
    logger.info(f"\n데이터 로드: {input_path}")
    
    df = pd.read_csv(input_path, encoding='utf-8-sig')
    logger.info(f"총 {len(df)}개 게시글 로드")
    
    # 감성 분석
    analyzer = SentimentAnalyzer()
    results = analyzer.analyze_dataframe(df)
    
    # 결과 추가
    df['형태소'] = [', '.join(r['morphemes']) for r in results]
    df['긍정_형태소_수'] = [r['positive_count'] for r in results]
    df['부정_형태소_수'] = [r['negative_count'] for r in results]
    df['중립_형태소_수'] = [r['neutral_count'] for r in results]
    df['감성_점수'] = [r['total_score'] for r in results]
    df['감성'] = [r['sentiment'] for r in results]
    df['신뢰도'] = [r['confidence'] for r in results]
    
    # 저장
    output_path = './data/processed/sentiment_scores.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"\n저장 완료: {output_path}")
    
    # 통계
    logger.info("\n=== 감성 분석 통계 ===")
    sentiment_counts = df['감성'].value_counts()
    for sentiment in ['긍정', '부정', '중립']:
        count = sentiment_counts.get(sentiment, 0)
        logger.info(f"{sentiment}: {count}개 ({count/len(df)*100:.1f}%)")
    
    logger.info(f"\n평균 감성 점수: {df['감성_점수'].mean():.2f}")
    logger.info(f"평균 신뢰도: {df['신뢰도'].mean():.3f}")
    
    # 샘플 출력
    logger.info("\n=== 감성 샘플 (긍정 5개) ===")
    positive = df[df['감성'] == '긍정'].head(5)
    for idx, row in positive.iterrows():
        logger.info(f"\n[{idx+1}] 제목: {row['제목']}")
        logger.info(f"내용: {str(row['내용'])[:100]}...")
        logger.info(f"형태소: {row['형태소']}")
        logger.info(f"감성: {row['감성']} (점수: {row['감성_점수']}, 신뢰도: {row['신뢰도']})")


if __name__ == "__main__":
    main()
