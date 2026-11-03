import os
import random
from scapy.all import Raw, UDP, IP
from .csp import CSP

def generate_fuzzing(original_pkt, base_time, ccsds_header, multiplier):
    attack_packets = []
    
    for i in range(multiplier):
        attack_csp = CSP(
            priority=random.randint(0, 3),
            source=random.randint(0, 31),
            destination=random.randint(0, 31),
            dst_port=random.randint(0, 63),
            src_port=random.randint(0, 63)
        )
        attack_data = os.urandom(4) 
        new_payload = ccsds_header + bytes(attack_csp) + attack_data
        
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
