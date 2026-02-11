"""
상관관계 분석 (config.yaml 제거 버전)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_correlation(df, method='pearson'):
    """상관관계 분석"""
    # 숫자형 컬럼만
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Date 컬럼 제외
    numeric_cols = [col for col in numeric_cols if col != 'Date']
    
    # 상관관계 계산
    corr_matrix = df[numeric_cols].corr(method=method)
    
    return corr_matrix, numeric_cols


def plot_heatmap(corr_matrix, title, filename):
    """히트맵 생성"""
    plt.figure(figsize=(16, 14))
    
    sns.heatmap(
        corr_matrix,
        annot=False,
        cmap='coolwarm',
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8}
    )
    
    plt.title(title, fontsize=16, pad=20)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"히트맵 저장: {filename}")


def find_high_correlations(corr_matrix, threshold=0.7):
    """높은 상관관계 찾기"""
    high_corr = []
    
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_value = corr_matrix.iloc[i, j]
            
            if abs(corr_value) > threshold:
                high_corr.append({
                    'Variable 1': corr_matrix.columns[i],
                    'Variable 2': corr_matrix.columns[j],
                    'Correlation': corr_value
                })
    
    return pd.DataFrame(high_corr)


def main():
    """메인 실행"""
    
    os.makedirs('./data/processed', exist_ok=True)
    
    logger.info("="*80)
    logger.info("상관관계 분석")
    logger.info("="*80)
    
    # 데이터 로드
    data_path = './data/processed/kodex200_full_features.csv'
    df = pd.read_csv(data_path)
    logger.info(f"KODEX 200 데이터 로드: {df.shape}")
    
    # Pearson 상관관계
    logger.info("\n[1/2] Pearson 상관관계 분석")
    pearson_corr, numeric_cols = analyze_correlation(df, method='pearson')
    
    plot_heatmap(
        pearson_corr,
        'Pearson 상관관계 히트맵',
        './data/processed/Pearson_상관관계_히트맵.png'
    )
    
    # Spearman 상관관계
    logger.info("\n[2/2] Spearman 상관관계 분석")
    spearman_corr, _ = analyze_correlation(df, method='spearman')
    
    plot_heatmap(
        spearman_corr,
        'Spearman 상관관계 히트맵',
        './data/processed/Spearman_상관관계_히트맵.png'
    )
    
    # 높은 상관관계
    logger.info("\n높은 상관관계 찾기 (|r| > 0.7)")
    high_corr = find_high_correlations(pearson_corr, threshold=0.7)
    
    if len(high_corr) > 0:
        logger.info(f"발견: {len(high_corr)}개")
        
        # 상위 10개
        logger.info("\n상위 10개:")
        top_10 = high_corr.sort_values('Correlation', key=abs, ascending=False).head(10)
        for idx, row in top_10.iterrows():
            logger.info(f"  {row['Variable 1']} ↔ {row['Variable 2']}: {row['Correlation']:.4f}")
        
        # 저장
        output_path = './data/processed/high_correlations.csv'
        high_corr.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"\n저장: {output_path}")
    else:
        logger.info("높은 상관관계 없음")
    
    logger.info("\n" + "="*80)
    logger.info("상관관계 분석 완료")
    logger.info("="*80)


if __name__ == "__main__":
    main()
