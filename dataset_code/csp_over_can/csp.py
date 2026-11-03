from scapy.all import Packet, BitField

class CSP(Packet):
    """CSP Header (4 Bytes) - CAN Extended ID에서 추출된 라우팅 정보"""
    name = "CSP"
    fields_desc = [
        BitField("priority", 0, 2),
        BitField("source", 0, 5),
        BitField("destination", 0, 5),
        BitField("dst_port", 0, 6),
        BitField("src_port", 0, 6),
        BitField("reserved", 0, 8)
    ]
