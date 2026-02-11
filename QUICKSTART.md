# ⚡ 빠른 시작 가이드 (5분)

주식 백테스팅 파이프라인을 5분 안에 실행하세요!

## 🚀 3단계로 시작

### 1️⃣ 환경 설정 (2분)

```bash
# 1. 가상환경 생성
conda create -n stock python=3.10
conda activate stock

# 2. 패키지 설치
pip install -r requirements.txt
```

### 2️⃣ 전체 실행 (2분)

```bash
# 한 번에 전체 실행
python run_pipeline.py --start 1 --end 7
```

### 3️⃣ 결과 확인 (1분)

```bash
# RAG 챗봇으로 결과 조회
python rag_chatbot.py
```

---

## 💡 개별 실행

### 크롤링만
```bash
python crawler.py
# 결과: data/raw/discussion_data.csv
```

### 감성 분석만
```bash
python sentiment_analysis.py
# 결과: data/processed/sentiment_scores.csv
```

### 백테스팅만
```bash
python backtesting.py
# 결과: data/backtest/strategy_results.csv
```

### RAG 챗봇
```bash
python rag_chatbot.py

질문: 최고 전략은?
질문: 100만원 투자하면?
질문: 머신러닝 결과는?
```

---

## 📊 주요 결과

### 백테스팅
```
최고 전략: MA_Cross_10_60
수익률: 86.13%
100만원 → 186만원
```

### 머신러닝
```
최고 모델: LinearRegression
R² Score: 0.9855 (98.55%)
```

### 감성 분석
```
긍정: 25.2%
부정: 23.2%
중립: 51.7%
```

---

## 🎯 다음 단계

1. `docs/` 폴더의 상세 가이드 확인
2. 실제 데이터로 재검증
3. 전략 커스터마이징

---

**준비 완료!** 🎉
