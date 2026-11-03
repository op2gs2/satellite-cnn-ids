#!/usr/bin/env python3
import argparse
import sys
from typing import List

import numpy as np
import pandas as pd

# =====================================================================
# 1. 최신 하이브리드 스키마 정의 (순수 헤더 15개 + 라벨 3개 = 총 18개)
# =====================================================================
HYBRID_COLUMNS: List[str] = [
    # Metadata
    "Timestamp",
    
    # CCSDS Header Features
    "CCSDS_Version", "CCSDS_Type", "CCSDS_SecHdrFlag", "CCSDS_APID",
    "CCSDS_SeqFlags", "CCSDS_SeqCount", "CCSDS_DataLen",
    
    # CSP Header Features
    "CSP_Priority", "CSP_Source", "CSP_Dest", "CSP_DPort", "CSP_SPort", "CSP_Flags",
    
    # Payload
    "Payload_Len",
    
    # Multi-Labels
    "CCSDS_Label", "CAN_Label"
]

# Timestamp만 Float, 나머지는 모두 Int형으로 분류
HYBRID_FLOAT_COLS = {"Timestamp"}
HYBRID_INT_COLS = set(HYBRID_COLUMNS) - HYBRID_FLOAT_COLS

VALID_SCENARIO_LABELS = {0, 1, 2, 3, 4}
VALID_ATTACK_LABELS = {0, 1}

# =====================================================================
# 2. 유틸리티 함수
# =====================================================================
def fail(msg: str) -> None:
    print(f" [FAIL] {msg}")
    sys.exit(1)

def ok(msg: str) -> None:
    print(f" [OK] {msg}")

# =====================================================================
# 3. 검증 로직
# =====================================================================
def enforce_columns(df: pd.DataFrame, expected: List[str]) -> None:
    got = list(df.columns)
    if set(got) != set(expected):
        extra = sorted(set(got) - set(expected))
        missing = sorted(set(expected) - set(got))
        fail(f"스키마 불일치! \n  - 추가된 열: {extra}\n  - 누락된 열: {missing}")
    ok(f"스키마 검증 완료. (18개 피처 일치)")

def enforce_no_missing(df: pd.DataFrame) -> None:
    if df.isna().any().any():
        miss = df.isna().sum()
        miss = miss[miss > 0].sort_values(ascending=False)
        fail("결측치(NaN)가 감지되었습니다:\n" + miss.to_string())
    ok("결측치 없음 (No Missing Values).")

def enforce_all_numeric(df: pd.DataFrame) -> None:
    non_numeric = [(c, str(df[c].dtype)) for c in df.columns if not pd.api.types.is_numeric_dtype(df[c].dtype)]
    if non_numeric:
        fail(f"비수치형(Non-numeric) 열 감지됨: {non_numeric}")
    ok("모든 열이 수치형 데이터입니다.")

def enforce_dtypes(df: pd.DataFrame) -> None:
    bad = []
    for c in sorted(HYBRID_INT_COLS):
        if c in df.columns:
            s = df[c].to_numpy()
            if not np.all(np.isclose(s, np.round(s))):
                bad.append((c, "정수형태(int-like)가 아님"))
                
    if bad:
        fail("데이터 타입 검증 실패:\n" + "\n".join([f"  - {c}: {msg}" for c, msg in bad]))
    ok("데이터 타입 무결성(Int/Float) 검증 완료.")

def validate_labels(df: pd.DataFrame) -> None:
    # 3가지 라벨 컬럼 존재 여부 확인
    for col in ["CCSDS_Label", "CAN_Label"]:
        if col not in df.columns:
            fail(f"'{col}' 열이 존재하지 않습니다.")
            
    # 각 라벨의 유효성 검사
    ccsd_labels = set(int(x) for x in np.unique(df["CCSDS_Label"].dropna().to_numpy()))
    can_labels = set(int(x) for x in np.unique(df["CAN_Label"].dropna().to_numpy()))
    
    invalid_ccsd = ccsd_labels - VALID_SCENARIO_LABELS
    invalid_can = can_labels - VALID_SCENARIO_LABELS
    
    if invalid_ccsd: fail(f"유효하지 않은 CCSDS_Label 감지됨: {invalid_ccsd}")
    if invalid_can: fail(f"유효하지 않은 CAN_Label 감지됨: {invalid_can}")
        
    ok(f"다중 라벨 검증 완료.")
    print(f"    - CCSDS_Label 분포: {ccsd_labels}")
    print(f"    - CAN_Label 분포: {can_labels}")

# =====================================================================
# 4. 메인 실행 블록
# =====================================================================
def main() -> None:
    p = argparse.ArgumentParser(description="하이브리드(CCSDS+CSP) IDS 데이터셋 무결성 검증기")
    p.add_argument("--input", required=True, help="검증할 CSV 파일 경로")
    args = p.parse_args()

    print("="*60)
    print(f" 📊 마스터 데이터셋 무결성 검증 시작: {args.input}")
    print("="*60)

    try:
        df = pd.read_csv(args.input, low_memory=False)
    except Exception as e:
        fail(f"CSV 파일 로드 실패: {e}")

    print(f"[*] 데이터 형태(Shape): {df.shape[0]:,} rows, {df.shape[1]} columns\n")

    enforce_columns(df, HYBRID_COLUMNS)
    enforce_no_missing(df)
    enforce_all_numeric(df)
    enforce_dtypes(df)
    validate_labels(df)

    print("\n" + "="*60)
    ok(f"최종 결과: '{args.input}' 파일이 머신러닝 모델 학습에 완벽하게 적합합니다!")
    print("="*60)

if __name__ == "__main__":
    main()
