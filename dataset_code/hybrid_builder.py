import os
from scapy.all import rdpcap, wrpcap, UDP
from tqdm import tqdm

# 연구원님의 패키지 구조에 맞춘 임포트
try:
    from can_attack.csp import CSP
    from can_attack import attack_dos, attack_spoof, attack_fuzz
    from can_attack.attack_replay import ReplayAttacker
except ImportError as e:
    print(f" [!] 경고: can_attack 모듈을 불러오지 못했습니다. 경로를 확인하세요: {e}")

def build_hybrid_dataset(input_pcap, output_pcap, attack_type):
    print(f" [*] 하이브리드 생성 가동: {os.path.basename(input_pcap)} + [{attack_type}]")
    
    try:
        packets = rdpcap(input_pcap)
    except Exception as e:
        print(f" [!] PCAP 로드 실패 ({input_pcap}): {e}")
        return

    hybrid_packets = []
    
    # Replay 공격일 경우 엔진 초기화
    replay_engine = None
    if attack_type == "can_replay":
        try:
            replay_engine = ReplayAttacker()
        except NameError:
            pass
    
    attack_counter = 0

    for pkt in tqdm(packets, desc=f" Injecting {attack_type}"):
        # 공격 패킷 생성을 위한 필수 재료 추출
        if not pkt.haslayer(UDP):
            continue
            
        raw_payload = bytes(pkt[UDP].payload)
        if len(raw_payload) < 6:
            continue
            
        # CCSDS Header (첫 6바이트)와 CSP/Data 분리
        ccsds_header = raw_payload[:6]
        csp_and_data = raw_payload[6:]
        base_time = float(pkt.time)
        multiplier = 1 # 한 번에 1개씩 만들어 Burst 로직을 따름

        # 리플레이 공격을 위해 정상 페이로드 지속 저장
        if replay_engine and len(csp_and_data) > 0:
            replay_engine.save_payload(csp_and_data)
        
        # 상태 머신에 따른 공격 주입
        try:
            attack_pkts = []

            # 연구원님의 규격에 맞춘 함수 호출!
            if attack_type == "can_flood":
                attack_pkts = attack_fuzz.generate_fuzzing(pkt, base_time, ccsds_header, multiplier)
            elif attack_type == "can_spoofing":
                attack_pkts = attack_spoof.generate_spoofing(pkt, base_time, ccsds_header, multiplier)
            elif attack_type == "can_dos":
                attack_pkts = attack_dos.generate_dos(pkt, base_time, ccsds_header, multiplier)
            elif attack_type == "can_replay" and replay_engine:
                attack_pkts = replay_engine.generate_replay(pkt, base_time, ccsds_header, multiplier)
            elif attack_type == "can_none":
                attack_pkts = hybrid_packets.append(pkt)
            else:
                raise Exception
            # 함수가 반환한 리스트(attack_pkts)를 풀어서 추가 (extend)
            if attack_pkts:
                hybrid_packets.extend(attack_pkts)
                attack_counter += len(attack_pkts)

        except Exception as e:
            print(f"\n\n [!] 🚨 치명적 주입 에러 발생: {e}")
            print(f" [!] 문제가 된 공격 타입: {attack_type}")
            break

    try:
        wrpcap(output_pcap, hybrid_packets)
        size_mb = os.path.getsize(output_pcap) / (1024 * 1024)
        print(f" [!] 생성 완료: {os.path.basename(output_pcap)} ({size_mb:.2f} MB / {len(hybrid_packets)} pkts)")
    except Exception as e:
        print(f" [!] PCAP 저장 중 에러 발생: {e}")
