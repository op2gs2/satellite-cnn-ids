import csv
import math
import os
from collections import defaultdict, deque
from typing import Deque, Dict, Iterable

import numpy as np
from scapy.all import PcapReader, UDP


BASE_HEADERS = [
    "Timestamp",
    "CCSDS_Version", "CCSDS_Type", "CCSDS_SecHdrFlag", "CCSDS_APID",
    "CCSDS_SeqFlags", "CCSDS_SeqCount", "CCSDS_DataLen",
    "CSP_Priority", "CSP_Source", "CSP_Dest", "CSP_DPort", "CSP_SPort", "CSP_Flags",
    "Payload_Len",
    "Time_Delta", "Time_Delta_Log", "Flags_Change", "Payload_Diff", "APID_Count",
    "P_Mean", "P_Std", "P_Entropy", "P_Entropy_Log", "P_First", "P_Entropy_Diff",
    "P_Sum", "P_Sum_Diff",
]

COMPACT_ENGINEERED_HEADERS = [
    "Global_Time_Delta_Log",
    "APID_Time_Delta_Log",
    "APID_Changed_Roll10",
    "CCSDS_DataLen_AbsDiff",
    "CCSDS_SeqCount_AbsDiff",
    "Packet_Rate_Roll10_Log",
    "CSP_Nonzero_Roll10",
    "CSP_Route_Changed_Roll10",
    "Payload_Len_RollStd10",
    "P_Entropy_Log_RollStd10",
]

CSV_HEADERS = BASE_HEADERS + COMPACT_ENGINEERED_HEADERS

BASE_FEATURES_20 = [
    "CCSDS_APID", "CCSDS_DataLen",
    "CSP_Priority", "CSP_Source", "CSP_Dest", "CSP_DPort", "CSP_SPort", "CSP_Flags",
    "Payload_Len",
    "Time_Delta_Log", "Flags_Change", "Payload_Diff", "APID_Count",
    "P_Mean", "P_Std", "P_Entropy_Log", "P_First", "P_Entropy_Diff", "P_Sum", "P_Sum_Diff",
]

COMPACT_FEATURES_10 = COMPACT_ENGINEERED_HEADERS.copy()
MODEL_FEATURES_30 = BASE_FEATURES_20 + COMPACT_FEATURES_10

CAN_ATTACK_TOKENS = [
    "can_flood",
    "can_fuzz",
    "can_spoofing",
    "can_dos",
    "can_replay",
]


def infer_can_context_from_filename(path: str) -> str:
    name = os.path.basename(path).lower()
    for token in CAN_ATTACK_TOKENS:
        if token in name:
            return token
    if "_none" in name or "can_none" in name or name.startswith("base_"):
        return "can_none"
    return "unknown"


def should_parse_csp_header(path: str) -> bool:
    """
    CSP routing fields are parsed only for CAN attack-context files.
    For base/can_none files, bytes after the CCSDS primary header are treated as payload,
    not as CSP routing fields.
    """
    return infer_can_context_from_filename(path) in CAN_ATTACK_TOKENS


def safe_log1p_nonnegative(x: float) -> float:
    return math.log1p(max(float(x), 0.0))


def seq_count_absdiff(curr: int, prev: int) -> float:
    diff = float(curr - prev)
    if diff > 8192:
        diff -= 16384
    elif diff < -8192:
        diff += 16384
    return abs(diff)


def rolling_sum(values: Iterable[float]) -> float:
    vals = list(values)
    return float(np.sum(vals)) if vals else 0.0


def rolling_std(values: Iterable[float]) -> float:
    vals = list(values)
    if len(vals) < 2:
        return 0.0
    return float(np.std(vals, ddof=1))


def csp_route_code(csp: Dict[str, int]) -> float:
    return float(
        int(csp["source"]) * 100000
        + int(csp["dest"]) * 1000
        + int(csp["dport"]) * 10
        + int(csp["sport"])
    )


def parse_ccsds_header(payload: bytes) -> Dict[str, int]:
    c_w1 = int.from_bytes(payload[0:2], byteorder="big")
    c_w2 = int.from_bytes(payload[2:4], byteorder="big")
    c_len = int.from_bytes(payload[4:6], byteorder="big")
    return {
        "version": (c_w1 >> 13) & 0x07,
        "type": (c_w1 >> 12) & 0x01,
        "sec_hdr_flag": (c_w1 >> 11) & 0x01,
        "apid": c_w1 & 0x07FF,
        "seq_flags": (c_w2 >> 14) & 0x03,
        "seq_count": c_w2 & 0x3FFF,
        "data_len": c_len,
    }


def parse_csp_header(payload: bytes, parse_enabled: bool) -> Dict[str, int]:
    if not parse_enabled or len(payload) < 10:
        return {"priority": 0, "source": 0, "dest": 0, "dport": 0, "sport": 0, "flags": 0}
    csp_raw = int.from_bytes(payload[6:10], byteorder="big")
    return {
        "priority": (csp_raw >> 30) & 0x03,
        "source": (csp_raw >> 25) & 0x1F,
        "dest": (csp_raw >> 20) & 0x1F,
        "dport": (csp_raw >> 14) & 0x3F,
        "sport": (csp_raw >> 8) & 0x3F,
        "flags": csp_raw & 0xFF,
    }


def payload_stats(payload: bytes, parse_csp_enabled: bool) -> Dict[str, float]:
    app_payload = payload[10:] if parse_csp_enabled and len(payload) >= 10 else payload[6:]
    if len(app_payload) == 0:
        return {"mean": 0.0, "std": 0.0, "entropy": 0.0, "entropy_log": 0.0, "first": 0, "sum": 0}

    arr = np.frombuffer(app_payload, dtype=np.uint8)
    p_mean = float(arr.mean())
    p_std = float(arr.std())
    p_first = int(arr[0])
    p_sum = int(arr.sum())

    counts = np.bincount(arr, minlength=256).astype(np.float64)
    probs = counts[counts > 0] / arr.size
    p_entropy = float(-(probs * np.log(probs)).sum())
    p_entropy_log = math.log1p(p_entropy)

    return {
        "mean": p_mean,
        "std": p_std,
        "entropy": p_entropy,
        "entropy_log": p_entropy_log,
        "first": p_first,
        "sum": p_sum,
    }


def extract_features_to_csv(hybrid_pcap: str, output_csv: str, roll_window: int = 10) -> None:
    print(f"[*] Compact protocol-aware feature extraction: {os.path.basename(hybrid_pcap)}")

    can_context = infer_can_context_from_filename(hybrid_pcap)
    parse_csp_enabled = should_parse_csp_header(hybrid_pcap)

    print(f"    - inferred CAN context: {can_context}")
    print(f"    - parse CSP header: {parse_csp_enabled}")
    print(f"    - roll window: {roll_window}")

    output_dir = os.path.dirname(output_csv)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    apid_state = defaultdict(lambda: {
        "prev_timestamp": None,
        "prev_payload_len": None,
        "prev_entropy": None,
        "prev_csp_flags": None,
        "prev_payload_sum": None,
        "count": 0,
    })

    prev_timestamp = None
    prev_apid = None
    prev_data_len = None
    prev_seq_count = None
    prev_route_code = None

    ts_buf: Deque[float] = deque(maxlen=roll_window)
    apid_changed_buf: Deque[float] = deque(maxlen=roll_window)
    csp_nonzero_buf: Deque[float] = deque(maxlen=roll_window)
    route_changed_buf: Deque[float] = deque(maxlen=roll_window)
    payload_len_buf: Deque[float] = deque(maxlen=roll_window)
    entropy_log_buf: Deque[float] = deque(maxlen=roll_window)

    count = 0
    skipped_non_udp = 0
    skipped_short = 0

    try:
        reader = PcapReader(hybrid_pcap)
    except Exception as e:
        print(f" [!] PCAP 로드 실패: {hybrid_pcap} | {e}")
        return

    with reader, open(output_csv, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)

        for pkt in reader:
            if not pkt.haslayer(UDP):
                skipped_non_udp += 1
                continue

            payload = bytes(pkt[UDP].payload)
            payload_len = len(payload)

            if payload_len < 6:
                skipped_short += 1
                continue

            pkt_time = float(pkt.time)
            ccsds = parse_ccsds_header(payload)
            csp = parse_csp_header(payload, parse_enabled=parse_csp_enabled)
            pstat = payload_stats(payload, parse_csp_enabled=parse_csp_enabled)

            apid = ccsds["apid"]
            current_route_code = csp_route_code(csp)

            if prev_timestamp is None:
                global_time_delta_log = 0.0
            else:
                global_time_delta_log = safe_log1p_nonnegative(pkt_time - prev_timestamp)

            apid_changed = 0.0 if prev_apid is None else float(apid != prev_apid)

            ccsds_data_len_absdiff = 0.0 if prev_data_len is None else abs(float(ccsds["data_len"] - prev_data_len))
            ccsds_seq_count_absdiff = 0.0 if prev_seq_count is None else seq_count_absdiff(ccsds["seq_count"], prev_seq_count)

            csp_nonzero = float(
                abs(csp["priority"])
                + abs(csp["source"])
                + abs(csp["dest"])
                + abs(csp["dport"])
                + abs(csp["sport"])
                + abs(csp["flags"])
                > 0
            )

            csp_route_changed = 0.0 if prev_route_code is None else float(current_route_code != prev_route_code)

            state = apid_state[apid]
            if state["prev_timestamp"] is None:
                time_delta = 0.0
                payload_diff = 0.0
                entropy_diff = 0.0
                flags_change = 0.0
                payload_sum_diff = 0.0
            else:
                time_delta = max(pkt_time - state["prev_timestamp"], 0.0)
                payload_diff = float(payload_len - state["prev_payload_len"])
                entropy_diff = float(pstat["entropy"] - state["prev_entropy"])
                flags_change = float(csp["flags"] - state["prev_csp_flags"])
                payload_sum_diff = float(pstat["sum"] - state["prev_payload_sum"])

            time_delta_log = safe_log1p_nonnegative(time_delta)
            apid_time_delta_log = time_delta_log
            apid_count = int(state["count"] + 1)

            ts_buf.append(pkt_time)
            apid_changed_buf.append(apid_changed)
            csp_nonzero_buf.append(csp_nonzero)
            route_changed_buf.append(csp_route_changed)
            payload_len_buf.append(float(payload_len))
            entropy_log_buf.append(float(pstat["entropy_log"]))

            apid_changed_roll10 = rolling_sum(apid_changed_buf)
            csp_nonzero_roll10 = rolling_sum(csp_nonzero_buf)
            csp_route_changed_roll10 = rolling_sum(route_changed_buf)
            payload_len_rollstd10 = rolling_std(payload_len_buf)
            p_entropy_log_rollstd10 = rolling_std(entropy_log_buf)

            if len(ts_buf) >= roll_window:
                span = max(ts_buf[-1] - ts_buf[0], 0.0)
                packet_rate_roll10_log = math.log1p((roll_window - 1) / span) if span > 0 else 0.0
            else:
                packet_rate_roll10_log = 0.0

            writer.writerow([
                pkt_time,
                ccsds["version"], ccsds["type"], ccsds["sec_hdr_flag"], ccsds["apid"],
                ccsds["seq_flags"], ccsds["seq_count"], ccsds["data_len"],
                csp["priority"], csp["source"], csp["dest"], csp["dport"], csp["sport"], csp["flags"],
                payload_len,
                time_delta, time_delta_log, flags_change, payload_diff, apid_count,
                pstat["mean"], pstat["std"], pstat["entropy"], pstat["entropy_log"], pstat["first"], entropy_diff,
                pstat["sum"], payload_sum_diff,
                global_time_delta_log, apid_time_delta_log, apid_changed_roll10,
                ccsds_data_len_absdiff, ccsds_seq_count_absdiff, packet_rate_roll10_log,
                csp_nonzero_roll10, csp_route_changed_roll10,
                payload_len_rollstd10, p_entropy_log_rollstd10,
            ])

            state["prev_timestamp"] = pkt_time
            state["prev_payload_len"] = payload_len
            state["prev_entropy"] = pstat["entropy"]
            state["prev_csp_flags"] = csp["flags"]
            state["prev_payload_sum"] = pstat["sum"]
            state["count"] = apid_count

            prev_timestamp = pkt_time
            prev_apid = apid
            prev_data_len = ccsds["data_len"]
            prev_seq_count = ccsds["seq_count"]
            prev_route_code = current_route_code

            count += 1

    print(f" [+] 완료: {os.path.basename(output_csv)}")
    print(f"     - rows: {count:,}")
    print(f"     - skipped non-UDP: {skipped_non_udp:,}")
    print(f"     - skipped short <6 bytes: {skipped_short:,}")
    print(f"     - output columns: {len(CSV_HEADERS)}")
    print(f"     - model feature candidates: {len(MODEL_FEATURES_30)}")