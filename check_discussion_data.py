"""
게시글 내용 확인 스크립트
"""
import pandas as pd

# 데이터 로드
df = pd.read_csv('./data/raw/discussion_data.csv', encoding='utf-8-sig')

print("="*80)
print("게시글 내용 분석")
print("="*80)

print(f"\n총 게시글: {len(df)}개")
print(f"\n컬럼: {df.columns.tolist()}")

# 내용 확인
print("\n=== 샘플 게시글 (첫 10개) ===")
for idx in range(min(10, len(df))):
    print(f"\n[{idx+1}] 닉네임: {df.iloc[idx]['닉네임']}")
    print(f"제목: {df.iloc[idx]['제목']}")
    print(f"내용: {str(df.iloc[idx]['내용'])[:200]}")
    print("-"*80)

# 통계
print("\n=== 내용 통계 ===")
print(f"내용이 'N/A'인 게시글: {(df['내용'] == 'N/A').sum()}개")
print(f"내용이 비어있는 게시글: {df['내용'].isna().sum()}개")
print(f"내용이 '내용 없음'인 게시글: {(df['내용'] == '내용 없음').sum()}개")

# 실제 내용이 있는 게시글
has_content = df[
    (df['내용'] != 'N/A') & 
    (~df['내용'].isna()) & 
    (df['내용'] != '내용 없음') &
    (df['내용'].str.len() > 10)
]

print(f"\n실제 내용이 있는 게시글: {len(has_content)}개 ({len(has_content)/len(df)*100:.1f}%)")

if len(has_content) > 0:
    print("\n=== 실제 내용 샘플 (5개) ===")
    for idx in range(min(5, len(has_content))):
        row = has_content.iloc[idx]
        print(f"\n제목: {row['제목']}")
        print(f"내용: {str(row['내용'])[:200]}...")
