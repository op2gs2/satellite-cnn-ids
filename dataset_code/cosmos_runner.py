import subprocess
import time
import os
import fcntl

def generate_base_pcap(script_dir, script_name, interface, output_pcap):
    """
    BPF 필터를 사용하여 유효한 CCSDS 패킷만 50,000개 선별 캡처합니다. (시간제한 없음)
    DNS(53), mDNS(5353) 등 불필요한 백그라운드 노이즈를 송수신 양방향에서 완벽 차단합니다.
    """
    container_name = "cosmos-openc3-operator-1"
    host_script_path = os.path.join(script_dir, script_name)
    
    print(f"\n[+] 시나리오 실행 준비 (무제한 캡처): {script_name}")
    
    # 1. 스크립트 도커 내부로 복사
    if not os.path.exists(host_script_path):
        print(f" [!] 에러: 파일 없음 -> {host_script_path}")
        return
    os.system(f"sudo docker cp {host_script_path} {container_name}:/tmp/{script_name}")

    # 2. tcpdump 가동 (CCSDS 전용 & 양방향 노이즈 완전 차단 BPF 필터)
    # 출발지와 목적지 포트 모두 1000 이상이어야 하며, 53, 5353, 5355 포트는 명시적으로 배제합니다.
    bpf_filter = "udp and (udp[8] & 0xe0 == 0) and (src portrange 1000-65535) and (dst portrange 1000-65535) and not port 53 and not port 5353 and not port 5355"
    
    os.system("sudo pkill -f tcpdump")
    time.sleep(1)
    
    tcpdump_cmd = [
        "sudo", "tcpdump", "-i", interface, 
        "-w", output_pcap, 
        "-n", "-U", "-c", "50000", 
        bpf_filter
    ]
    
    tcpdump_proc = subprocess.Popen(tcpdump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f" [*] 스마트 캡처 가동 (BPF: '{bpf_filter}')")
    time.sleep(2) 

    # 3. 도커 내부 루비 스크립트 실행
    docker_cmd = [
        "sudo", "docker", "exec",
        "-e", "HOME=/tmp",
        "-e", "GEM_HOME=/var/lib/gems/2.5.0",
        "-e", "GEM_PATH=/var/lib/gems/2.5.0",
        "-e", "RUBYLIB=/cosmos/lib",
        "-w", "/cosmos",
        container_name,
        "ruby", "-Ilib", "-r", "cosmos/script", f"/tmp/{script_name}"
    ]
    
    docker_proc = subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # 로그 읽기를 비차단(Non-blocking) 모드로 설정
    fd = docker_proc.stdout.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    print(" [*] --- 실시간 모니터링 가동 (무제한 대기) ---")

    try:
        while True:
            # [A] tcpdump 종료 여부 체크 (5만 개 선별 수집 완료 시)
            if tcpdump_proc.poll() is not None:
                print("\n [!] 목표 패킷(50,000개) 수집 완료! 다음 단계로 넘어갑니다.")
                break

            # [B] 루비 로그 감시 (비차단)
            try:
                line = docker_proc.stdout.readline()
                if line:
                    clean_line = line.strip()
                    print(f"    [COSMOS] {clean_line}")
                    if "Successfully!" in clean_line:
                        print("\n [!] 시나리오 완주 신호 감지!")
                        break
            except IOError:
                pass # 아직 읽을 로그가 없음

            time.sleep(0.1)

    finally:
        # 4. 프로세스 정리
        docker_proc.terminate()
        os.system("sudo pkill -f tcpdump")
        time.sleep(1)
        
        if os.path.exists(output_pcap):
            size_mb = os.path.getsize(output_pcap) / (1024 * 1024)
            print(f"[+] 최종 결과: {output_pcap} ({size_mb:.2f} MB)")
