import os
import glob
import pandas as pd
import numpy as np
from tqdm import tqdm

# =====================================================================
# 1. 라벨 체계 정의
# =====================================================================
CCSDS_MAP = {
    "normal_ops": 0,
    "command_flood": 1,
    "data_injection": 2,
    "storage_exhaustion": 3,
    "defence_impairment": 4
}

CAN_MAP = {
    "none": 0,
    "can_flood": 1,
    "can_spoofing": 2,
    "can_dos": 3,
    "can_replay": 4
}

DIR_CSV = "/home/ubuntu/Desktop/hybrid_ids_project/data/csv"
OUTPUT_FILE = "/home/ubuntu/Desktop/hybrid_ids_project/data/master_dataset.csv"

def merge_and_label_csvs():
    print("="*60)
    print(" 🚀 하이브리드 데이터셋 병합 및 일괄 라벨링 (Pandas)")
    print("="*60)

    # 폴더 내의 모든 CSV 파일 찾기 (master 파일 제외)
    all_csv_files = [f for f in glob.glob(os.path.join(DIR_CSV, "*.csv")) if "master" not in f]
    
    if not all_csv_files:
        print(" [!] CSV 파일을 찾을 수 없습니다.")
        return

    dataframe_list = []

    for file_path in tqdm(all_csv_files, desc=" Processing CSVs"):
        file_name = os.path.basename(file_path).lower()
        
        # 1. 파일 이름에서 시나리오 컨텍스트 추출
        ccsd_context = next((k for k in CCSDS_MAP if k in file_name), "normal_ops")
        can_context = next((k for k in CAN_MAP if k in file_name), "none")
        
        # 2. CSV 파일 로드
        df = pd.read_csv(file_path)
        
        # 3. 데이터 일괄 라벨링 (핵심 수정 사항)
        # 이전처럼 PayloadLength 등을 검사하지 않고, 파일 전체에 컨텍스트를 덮어씌웁니다.
        df['CCSDS_Label'] = CCSDS_MAP[ccsd_context]
        df['CAN_Label'] = CAN_MAP[can_context]
        
        # [통합 공격 여부] 둘 중 하나라도 0보다 크면 1(공격), 아니면 0(정상)
        df['Is_Attack'] = np.where((df['CAN_Label'] > 0) | (df['CCSDS_Label'] > 0), 1, 0)
        
        # 리스트에 추가
        dataframe_list.append(df)

    # 4. 모든 데이터프레임을 하나로 병합 (수백만 행)
    print(f"\n [*] 총 {len(dataframe_list)}개의 파일을 하나로 병합 중...")
    master_df = pd.concat(dataframe_list, ignore_index=True)
    
    # 5. 결과 저장
    master_df.to_csv(OUTPUT_FILE, index=False)
    
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"\n [+] 마스터 데이터셋 완성! : {OUTPUT_FILE}")
    print(f" [+] 총 행(Rows) 수: {len(master_df):,}")
    print(f" [+] 파일 크기: {size_mb:.2f} MB")

if __name__ == "__main__":
    merge_and_label_csvs()
