# hybrid_ids_project/can_attack/__init__.py

"""
CAN Bus Attack Simulation Package for Space Systems
이 패키지는 CSP over CAN 네트워크의 다양한 이상 징후를 모사합니다.
"""

# 패키지 레벨에서 바로 사용할 수 있도록 모듈의 핵심 요소들을 끌어올립니다.
from .csp import CSP
from .attack_dos import generate_dos
from .attack_spoof import generate_spoofing
from .attack_fuzz import generate_fuzzing
from .attack_replay import ReplayAttacker

# 패키지 외부로 노출할 이름들을 지정합니다.
__all__ = [
    "CSP",
    "generate_dos",
    "generate_spoofing",
    "generate_fuzzing",
    "ReplayAttacker"
]
