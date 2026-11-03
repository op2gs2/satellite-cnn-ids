import os
import glob
import pandas as pd
import numpy as np
from tqdm import tqdm

from cosmos_runner import generate_base_pcap
from hybrid_builder import build_hybrid_dataset
try:
    import feature_extractor
except ImportError:
    pass

# =====================================================================
# 설정 및 라벨 맵
# =====================================================================
SCRIPT_DIR = "/home/ubuntu/Desktop/hybrid_ids_project/scripts"
INTERFACE = "any"
DIR_PCAP = "/home/ubuntu/Desktop/hybrid_ids_project/data/pcap"
DIR_CSV = "/home/ubuntu/Desktop/hybrid_ids_project/data/csv"
MASTER_CSV = "/home/ubuntu/Desktop/hybrid_ids_project/data/master_dataset.csv"

SCENARIOS = [
    "normal_ops_script.txt", "command_flood_script.txt", 
    "data_injection_script.txt", "storage_exhaustion_script.txt", 
    "defence_impairment_script.txt"
]

CAN_ATTACKS = ["can_flood", "can_spoofing", "can_dos", "can_replay"]

CCSDS_MAP = {"normal_ops": 0, "command_flood": 1, "data_injection": 2, "storage_exhaustion": 3, "defence_impairment": 4}
CAN_MAP = {"none": 0, "can_flood": 1, "can_spoofing": 2, "can_dos": 3, "can_replay": 4}

def merge_and_label_csvs():
    print("\n[Phase 4] 파일 컨텍스트 기반 일괄 라벨링 및 병합")
    all_csv_files = [f for f in glob.glob(os.path.join(DIR_CSV, "*.csv")) if "master" not in f]
    
    if not all_csv_files:
        return

    dataframe_list = []
    for file_path in tqdm(all_csv_files, desc=" Labeling & Merging"):
        file_name = os.path.basename(file_path).lower()
        
        # 파일명에서 라벨 추출
        ccsd_context = next((k for k in CCSDS_MAP if k in file_name), "normal_ops")
        can_context = next((k for k in CAN_MAP if k in file_name), "none")
        
        df = pd.read_csv(file_path)
        df['CCSDS_Label'] = CCSDS_MAP[ccsd_context]
        df['CAN_Label'] = CAN_MAP[can_context]
        df['Is_Attack'] = np.where((df['CAN_Label'] > 0) | (df['CCSDS_Label'] > 0), 1, 0)
        
        dataframe_list.append(df)

    master_df = pd.concat(dataframe_list, ignore_index=True)
    master_df.to_csv(MASTER_CSV, index=False)
    
    print(f"\n [+] 🚀 마스터 데이터셋 완성: {MASTER_CSV}")
    print(f" [+] 총 행(Rows): {len(master_df):,} | 크기: {os.path.getsize(MASTER_CSV)/(1024*1024):.2f} MB")

def main():
    os.makedirs(DIR_PCAP, exist_ok=True)
    os.makedirs(DIR_CSV, exist_ok=True)
    print("="*75)
    print(" 🚀 하이브리드 IDS 초고속 데이터 공장 가동")
    print("="*75)

    print("\n[Phase 1] 원본 CCSDS 트래픽 수집")
    base_pcaps = {} 
    for script in SCENARIOS:
        ccsd_name = script.replace("_script.txt", "")
        base_pcap_name = os.path.join(DIR_PCAP, f"base_{ccsd_name}.pcap")
        if not (os.path.exists(base_pcap_name) and os.path.getsize(base_pcap_name) > 1024):
            generate_base_pcap(SCRIPT_DIR, script, INTERFACE, base_pcap_name)
        base_pcaps[ccsd_name] = base_pcap_name

    print("\n[Phase 2] 내부망 공격 교차 주입")
    for ccsd_name, base_pcap_path in base_pcaps.items():
        for can_attack in CAN_ATTACKS:
            hybrid_pcap = os.path.join(DIR_PCAP, f"hybrid_{ccsd_name}_{can_attack}.pcap")
            if not os.path.exists(hybrid_pcap):
                build_hybrid_dataset(base_pcap_path, hybrid_pcap, can_attack)

    print("\n[Phase 3] 피처 추출")
    for ccsd_name in base_pcaps.keys():
        for can_attack in CAN_ATTACKS:
            hybrid_pcap = os.path.join(DIR_PCAP, f"hybrid_{ccsd_name}_{can_attack}.pcap")
            output_csv = os.path.join(DIR_CSV, f"hybrid_{ccsd_name}_{can_attack}.csv")
            if os.path.exists(hybrid_pcap) and not os.path.exists(output_csv):
                feature_extractor.extract_features_to_csv(hybrid_pcap, output_csv)

    merge_and_label_csvs()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        os.system("sudo pkill -f tcpdump")
