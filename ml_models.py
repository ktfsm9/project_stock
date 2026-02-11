"""
머신러닝 모델 학습 (config.yaml 제거 버전)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, VotingRegressor, StackingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import xgboost as xgb
import matplotlib.pyplot as plt
import logging
import joblib
import os

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLPipeline:
    """머신러닝 파이프라인"""
    
    def __init__(self):
        self.models = {}
        self.results = []
        self.scaler = StandardScaler()
        
    def prepare_data(self, df):
        """데이터 준비"""
        # 날짜 제외
        feature_cols = [col for col in df.columns if col not in ['Date', 'Close']]
        
        X = df[feature_cols]
        y = df['Close']
        
        # Train/Test 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 스케일링
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train_models(self, X_train, X_test, y_train, y_test):
        """모델 학습"""
        
        # 모델 정의
        models_dict = {
            'LinearRegression': LinearRegression(),
            'Ridge': Ridge(alpha=1.0),
            'Lasso': Lasso(alpha=1.0),
            'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42),
            'XGBoost': xgb.XGBRegressor(n_estimators=100, random_state=42)
        }
        
        logger.info("="*80)
        logger.info("모델 학습 시작")
        logger.info("="*80)
        
        for name, model in models_dict.items():
            try:
                logger.info(f"\n[{name}] 학습 중...")
                
                # 학습
                model.fit(X_train, y_train)
                
                # 예측
                y_pred = model.predict(X_test)
                
                # 평가
                r2 = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                
                # 방향 정확도
                y_test_direction = np.diff(y_test.values) > 0
                y_pred_direction = np.diff(y_pred) > 0
                direction_accuracy = np.mean(y_test_direction == y_pred_direction) * 100
                
                result = {
                    'Model': name,
                    'R2': r2,
                    'RMSE': rmse,
                    'MAE': mae,
                    'Direction_Accuracy': direction_accuracy
                }
                
                self.results.append(result)
                self.models[name] = model
                
                logger.info(f"R² Score: {r2:.4f}")
                logger.info(f"RMSE: {rmse:.2f}")
                logger.info(f"MAE: {mae:.2f}")
                logger.info(f"방향 정확도: {direction_accuracy:.2f}%")
                
            except Exception as e:
                logger.error(f"[{name}] 실패: {e}")
        
        # Voting
        try:
            logger.info(f"\n[Voting] 학습 중...")
            voting = VotingRegressor([
                ('lr', LinearRegression()),
                ('ridge', Ridge()),
                ('lasso', Lasso())
            ])
            voting.fit(X_train, y_train)
            
            y_pred = voting.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            
            self.results.append({
                'Model': 'Voting',
                'R2': r2,
                'RMSE': rmse,
                'MAE': mae,
                'Direction_Accuracy': 0
            })
            self.models['Voting'] = voting
            
            logger.info(f"R² Score: {r2:.4f}")
            
        except Exception as e:
            logger.error(f"[Voting] 실패: {e}")
        
        # Stacking
        try:
            logger.info(f"\n[Stacking] 학습 중...")
            stacking = StackingRegressor(
                estimators=[
                    ('lr', LinearRegression()),
                    ('ridge', Ridge())
                ],
                final_estimator=LinearRegression()
            )
            stacking.fit(X_train, y_train)
            
            y_pred = stacking.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            
            self.results.append({
                'Model': 'Stacking',
                'R2': r2,
                'RMSE': rmse,
                'MAE': mae,
                'Direction_Accuracy': 0
            })
            self.models['Stacking'] = stacking
            
            logger.info(f"R² Score: {r2:.4f}")
            
        except Exception as e:
            logger.error(f"[Stacking] 실패: {e}")
    
    def save_models(self):
        """모델 저장"""
        os.makedirs('./models', exist_ok=True)
        
        for name, model in self.models.items():
            path = f'./models/{name}.pkl'
            joblib.dump(model, path)
            logger.info(f"모델 저장: {path}")
    
    def get_results_df(self):
        """결과 DataFrame"""
        return pd.DataFrame(self.results).sort_values('R2', ascending=False)


def main():
    """메인 실행"""
    
    logger.info("="*80)
    logger.info("머신러닝 모델 학습")
    logger.info("="*80)
    
    # 데이터 로드
    data_path = './data/processed/kodex200_full_features.csv'
    df = pd.read_csv(data_path)
    logger.info(f"데이터 로드: {df.shape}")
    
    # 파이프라인
    pipeline = MLPipeline()
    
    # 데이터 준비
    X_train, X_test, y_train, y_test = pipeline.prepare_data(df)
    logger.info(f"Train: {X_train.shape}, Test: {X_test.shape}")
    
    # 모델 학습
    pipeline.train_models(X_train, X_test, y_train, y_test)
    
    # 결과
    results_df = pipeline.get_results_df()
    
    logger.info("\n" + "="*80)
    logger.info("학습 결과 요약")
    logger.info("="*80)
    print("\n", results_df.to_string(index=False))
    
    # 최고 모델
    best_model = results_df.iloc[0]
    logger.info(f"\n최고 모델: {best_model['Model']}")
    logger.info(f"  R² Score: {best_model['R2']:.4f}")
    logger.info(f"  RMSE: {best_model['RMSE']:.2f}")
    logger.info(f"  MAE: {best_model['MAE']:.2f}")
    
    # 모델 저장
    pipeline.save_models()
    
    # 결과 저장
    output_path = './data/processed/ml_results.csv'
    results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"\n결과 저장: {output_path}")
    
    logger.info("\n" + "="*80)
    logger.info("머신러닝 완료")
    logger.info("="*80)


if __name__ == "__main__":
    main()
