#!/usr/bin/env python3
"""
GPU/RAM Monitor - Track resource usage for Ollama and other processes

Usage:
    python gpu_monitor.py

Dependencies:
    pip install gpustat psutil
"""

import subprocess
import time
import psutil

def monitor_resources():
    """Monitor GPU, RAM, and CPU usage"""
    try:
        # GPU stats (nvidia-smi)
        result = subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu',
                               '--format=csv,noheader,nounits'],
                               capture_output=True, text=True)

        print("="*60)
        print("GPU STATUS")
        print("="*60)

        for line in result.stdout.strip().split('\n'):
            idx, name, mem_used, mem_total, gpu_util, temp = line.split(', ')
            print(f"GPU {idx}: {name}")
            print(f"  VRAM: {mem_used} MB / {mem_total} MB ({int(mem_used)/int(mem_total)*100:.1f}%)")
            print(f"  GPU Util: {gpu_util}%")
            print(f"  Temp: {temp}°C")

        # RAM stats
        ram = psutil.virtual_memory()
        print(f"\nRAM: {ram.used / (1024**3):.1f} GB / {ram.total / (1024**3):.1f} GB ({ram.percent}%)")

        # CPU stats
        cpu = psutil.cpu_percent(interval=1)
        print(f"CPU: {cpu}%")

        # Find Ollama process
        print("\n" + "="*60)
        print("OLLAMA PROCESS")
        print("="*60)

        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            if 'ollama' in proc.info['name'].lower():
                mem_mb = proc.info['memory_info'].rss / (1024**2)
                print(f"PID: {proc.info['pid']}")
                print(f"RAM: {mem_mb:.0f} MB")
                print(f"CPU: {proc.info['cpu_percent']}%")

    except FileNotFoundError:
        print("nvidia-smi not found. Install NVIDIA drivers.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Monitoring resources (Ctrl+C to stop)...\n")
    try:
        while True:
            monitor_resources()
            time.sleep(5)  # Update every 5 seconds
    except KeyboardInterrupt:
        print("\nStopped monitoring.")
