"""
AI-Based Predictive Maintenance System
Moderate Stress Data Collection - 2 Hours at 0.5 Second Intervals

This script collects system performance data specifically for MODERATE load states.
It simulates realistic moderate workload patterns continuously for 2 hours.
"""

import psutil
import csv
import time
import os
import sys
import threading
from datetime import datetime
import math

class ModerateDataCollector:
    """
    Collects system data under moderate load conditions for 2 hours
    """
    
    def __init__(self, laptop_name="Laptop1", interval=0.5, duration_seconds=7200):
        """
        Initialize the collector
        
        Args:
            laptop_name: Identifier for the laptop (e.g., Laptop1, Laptop2)
            interval: Collection interval in seconds (0.5 seconds)
            duration_seconds: Total collection duration (7200 seconds = 2 hours)
        """
        self.laptop_name = laptop_name
        self.interval = interval
        self.duration = duration_seconds
        self.start_time = None
        self.sample_count = 0
        self.running = False
        
        # Track state distribution
        self.state_counts = {
            "Normal": 0,
            "Moderate": 0,
            "High": 0
        }
        
        # Current state
        self.current_state = "Moderate"  # We focus on Moderate state
        
        # Create output filename with timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = f"{laptop_name}_moderate_2hour_{self.timestamp}.csv"
        self.log_file = f"{laptop_name}_moderate_log_{self.timestamp}.txt"
        
        # Initialize CSV file
        self.init_csv()
        self.init_log()
        
    def init_csv(self):
        """Create CSV file with headers"""
        headers = [
            'timestamp',
            'cpu_percent',
            'cpu_frequency_mhz',
            'cpu_per_core_avg',
            'memory_percent',
            'memory_available_mb',
            'memory_used_mb',
            'memory_total_mb',
            'swap_percent',
            'disk_percent',
            'disk_read_mbps',
            'disk_write_mbps',
            'network_upload_mbps',
            'network_download_mbps',
            'process_count',
            'load_state',
            'cpu_temp_celsius',
            'system_uptime_seconds',
            'elapsed_minutes',
            'sample_number',
            'timestamp_seconds'
        ]
        
        with open(self.output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def init_log(self):
        """Create log file"""
        with open(self.log_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("MODERATE STRESS DATA COLLECTION\n")
            f.write("=" * 80 + "\n")
            f.write(f"Laptop: {self.laptop_name}\n")
            f.write(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: 2 hours ({self.duration} seconds)\n")
            f.write(f"Interval: {self.interval} seconds\n")
            f.write(f"Expected Samples: ~{int(self.duration / self.interval)}\n")
            f.write("=" * 80 + "\n\n")
            f.write("Collection Started...\n")
    
    def get_system_metrics(self):
        """
        Collect all system metrics using psutil
        """
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_freq = psutil.cpu_freq()
        cpu_frequency_mhz = cpu_freq.current if cpu_freq else 0
        
        # Per-core CPU
        try:
            per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_per_core_avg = sum(per_core) / len(per_core) if per_core else 0
        except:
            cpu_per_core_avg = 0
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_mb = memory.available / (1024 * 1024)
        memory_used_mb = memory.used / (1024 * 1024)
        memory_total_mb = memory.total / (1024 * 1024)
        
        # Swap memory
        swap = psutil.swap_memory()
        swap_percent = swap.percent if swap else 0
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Disk I/O (with 0.1 second sampling)
        disk_io_start = psutil.disk_io_counters()
        time.sleep(0.1)
        disk_io_end = psutil.disk_io_counters()
        
        read_bytes = disk_io_end.read_bytes - disk_io_start.read_bytes
        write_bytes = disk_io_end.write_bytes - disk_io_start.write_bytes
        disk_read_mbps = (read_bytes / (1024 * 1024)) / 0.1
        disk_write_mbps = (write_bytes / (1024 * 1024)) / 0.1
        
        # Network I/O
        net_io_start = psutil.net_io_counters()
        time.sleep(0.1)
        net_io_end = psutil.net_io_counters()
        
        upload_bytes = net_io_end.bytes_sent - net_io_start.bytes_sent
        download_bytes = net_io_end.bytes_recv - net_io_start.bytes_recv
        network_upload_mbps = (upload_bytes / (1024 * 1024)) / 0.1
        network_download_mbps = (download_bytes / (1024 * 1024)) / 0.1
        
        # Process count
        process_count = len(psutil.pids())
        
        # CPU Temperature
        try:
            temps = psutil.sensors_temperatures()
            cpu_temp = 0
            if temps:
                for name in ['coretemp', 'cpu_thermal', 'hwmon', 'k10temp', 'zenpower']:
                    if name in temps and temps[name]:
                        cpu_temp = temps[name][0].current
                        break
        except:
            cpu_temp = 0
        
        # System uptime
        uptime_seconds = time.time() - psutil.boot_time()
        
        # Elapsed time
        elapsed_seconds = time.time() - self.start_time if self.start_time else 0
        elapsed_minutes = elapsed_seconds / 60
        
        # Current timestamp
        now = datetime.now()
        
        return {
            'timestamp': now.isoformat(),
            'timestamp_seconds': now.timestamp(),
            'cpu_percent': round(cpu_percent, 2),
            'cpu_frequency_mhz': round(cpu_frequency_mhz, 2),
            'cpu_per_core_avg': round(cpu_per_core_avg, 2),
            'memory_percent': round(memory_percent, 2),
            'memory_available_mb': round(memory_available_mb, 2),
            'memory_used_mb': round(memory_used_mb, 2),
            'memory_total_mb': round(memory_total_mb, 2),
            'swap_percent': round(swap_percent, 2),
            'disk_percent': round(disk_percent, 2),
            'disk_read_mbps': round(disk_read_mbps, 2),
            'disk_write_mbps': round(disk_write_mbps, 2),
            'network_upload_mbps': round(network_upload_mbps, 2),
            'network_download_mbps': round(network_download_mbps, 2),
            'process_count': process_count,
            'load_state': self.current_state,
            'cpu_temp_celsius': round(cpu_temp, 2) if cpu_temp else 0,
            'system_uptime_seconds': round(uptime_seconds, 0),
            'elapsed_minutes': round(elapsed_minutes, 1),
            'sample_number': self.sample_count + 1
        }
    
    def save_metrics(self, metrics):
        """
        Save metrics to CSV file
        """
        with open(self.output_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                metrics['timestamp'],
                metrics['cpu_percent'],
                metrics['cpu_frequency_mhz'],
                metrics['cpu_per_core_avg'],
                metrics['memory_percent'],
                metrics['memory_available_mb'],
                metrics['memory_used_mb'],
                metrics['memory_total_mb'],
                metrics['swap_percent'],
                metrics['disk_percent'],
                metrics['disk_read_mbps'],
                metrics['disk_write_mbps'],
                metrics['network_upload_mbps'],
                metrics['network_download_mbps'],
                metrics['process_count'],
                metrics['load_state'],
                metrics['cpu_temp_celsius'],
                metrics['system_uptime_seconds'],
                metrics['elapsed_minutes'],
                metrics['sample_number'],
                metrics['timestamp_seconds']
            ])
    
    def generate_moderate_workload(self):
        """
        Generate realistic moderate workload patterns continuously
        """
        pattern_index = 0
        patterns = [
            {"name": "Office Work", "duration": 120, "intensity": 0.4},
            {"name": "Web Browsing", "duration": 90, "intensity": 0.3},
            {"name": "Document Editing", "duration": 120, "intensity": 0.35},
            {"name": "Data Processing", "duration": 60, "intensity": 0.6},
            {"name": "Light Coding", "duration": 100, "intensity": 0.5},
            {"name": "Email & Chat", "duration": 80, "intensity": 0.25},
            {"name": "Spreadsheet Work", "duration": 110, "intensity": 0.45},
            {"name": "PDF/Document Viewing", "duration": 70, "intensity": 0.2},
            {"name": "Database Query", "duration": 50, "intensity": 0.65},
            {"name": "Browsing with Tabs", "duration": 100, "intensity": 0.4},
        ]
        
        while self.running:
            # Select pattern
            pattern = patterns[pattern_index % len(patterns)]
            pattern_index += 1
            
            # Generate workload based on pattern
            self.current_state = "Moderate"
            self.generate_workload_pattern(pattern["intensity"], pattern["duration"])
            
            # Small break between patterns (maintains moderate state)
            time.sleep(1)
    
    def generate_workload_pattern(self, intensity, duration_seconds):
        """
        Generate specific workload pattern with given intensity
        """
        end_time = time.time() + duration_seconds
        temp_file = f"temp_moderate_{int(time.time())}.txt"
        memory_chunks = []
        
        # Calculate operation counts based on intensity
        cpu_ops = int(50000 * intensity)
        memory_alloc = int(100000 * intensity)
        disk_writes = int(1000 * intensity)
        
        try:
            while time.time() < end_time and self.running:
                # CPU operations (moderate)
                for i in range(cpu_ops):
                    x = i * i / 1000 + i
                    y = math.sin(x) * 100
                
                # Memory operations
                chunk_size = memory_alloc // 10
                for _ in range(10):
                    chunk = [0] * chunk_size
                    memory_chunks.append(chunk)
                if len(memory_chunks) > 100:
                    memory_chunks = memory_chunks[50:]
                
                # Disk operations
                with open(temp_file, 'a') as f:
                    f.write("M" * disk_writes)
                
                # Read back some data
                if os.path.exists(temp_file):
                    with open(temp_file, 'r') as f:
                        data = f.read(1000)
                
                # Simulate user thinking/processing
                time.sleep(0.05 + (1 - intensity) * 0.05)
                
        finally:
            # Clean up
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def collect_data(self):
        """
        Main data collection loop
        """
        self.running = True
        self.start_time = time.time()
        
        print("=" * 80)
        print("🔍 MODERATE STRESS DATA COLLECTION")
        print("=" * 80)
        print(f"📁 Laptop: {self.laptop_name}")
        print(f"⏱️  Duration: 2 hours ({self.duration} seconds)")
        print(f"📊 Interval: {self.interval} seconds")
        print(f"📈 State: Focused on MODERATE load")
        print(f"💾 Output: {self.output_file}")
        print("=" * 80)
        print("\n🔄 Generating moderate workload patterns...")
        print("   - Office work, web browsing, document editing")
        print("   - Data processing, light coding, email")
        print("   - Continuous moderate load for 2 hours\n")
        print("📊 Starting data collection...")
        print("-" * 80)
        
        # Start workload generator in background thread
        workload_thread = threading.Thread(target=self.generate_moderate_workload)
        workload_thread.daemon = True
        workload_thread.start()
        
        # Main collection loop
        last_display_update = time.time()
        last_sample_time = time.time()
        
        while self.running and (time.time() - self.start_time) < self.duration:
            try:
                # Ensure we don't collect faster than interval
                current_time = time.time()
                if current_time - last_sample_time < self.interval:
                    time.sleep(0.01)
                    continue
                
                # Collect metrics
                metrics = self.get_system_metrics()
                self.sample_count += 1
                self.state_counts[self.current_state] += 1
                
                # Save to CSV
                self.save_metrics(metrics)
                
                # Update display
                if time.time() - last_display_update >= 0.5:
                    elapsed = time.time() - self.start_time
                    progress = (elapsed / self.duration) * 100
                    remaining = self.duration - elapsed
                    
                    # Format remaining time
                    hours = int(remaining // 3600)
                    minutes = int((remaining % 3600) // 60)
                    seconds = int(remaining % 60)
                    
                    # Create progress bar
                    bar_length = 30
                    filled = int(bar_length * progress / 100)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    
                    # Print status
                    print(f"\r[{bar}] {progress:5.1f}% | "
                          f"Samples: {self.sample_count:6d} | "
                          f"CPU: {metrics['cpu_percent']:5.1f}% | "
                          f"Memory: {metrics['memory_percent']:5.1f}% | "
                          f"Remaining: {hours:02d}h {minutes:02d}m {seconds:02d}s",
                          end='', flush=True)
                    
                    # Also write to log periodically
                    if self.sample_count % 100 == 0:
                        with open(self.log_file, 'a') as f:
                            f.write(f"Sample {self.sample_count}: "
                                   f"CPU={metrics['cpu_percent']}%, "
                                   f"Memory={metrics['memory_percent']}%, "
                                   f"Elapsed={elapsed/60:.1f}min\n")
                    
                    last_display_update = time.time()
                
                last_sample_time = current_time
                
            except KeyboardInterrupt:
                self.running = False
                print("\n\n⏹️ Collection stopped by user.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(1)
        
        # Collection complete
        self.running = False
        print("\n\n" + "=" * 80)
        print("✅ DATA COLLECTION COMPLETE!")
        print("=" * 80)
        
        # Show statistics
        elapsed = time.time() - self.start_time
        print(f"📊 Total Samples: {self.sample_count}")
        print(f"⏱️  Duration: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
        print(f"📈 Average Rate: {self.sample_count/(elapsed/60):.1f} samples/min")
        
        print("\n📈 State Distribution:")
        total = sum(self.state_counts.values())
        for state, count in self.state_counts.items():
            if total > 0:
                percentage = (count / total) * 100
                bar = '█' * int(percentage/2) + '░' * (50 - int(percentage/2))
                print(f"  {state}: {count:6d} samples ({percentage:5.1f}%) {bar}")
        
        print(f"\n💾 Data saved to: {self.output_file}")
        print(f"📋 Log saved to: {self.log_file}")
        print("=" * 80)
        
        # Write final statistics to log
        with open(self.log_file, 'a') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write("COLLECTION COMPLETE\n")
            f.write("=" * 80 + "\n")
            f.write(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Samples: {self.sample_count}\n")
            f.write(f"Duration: {elapsed/60:.1f} minutes\n")
            f.write("\nState Distribution:\n")
            for state, count in self.state_counts.items():
                if total > 0:
                    f.write(f"  {state}: {count} samples ({count/total*100:.1f}%)\n")
            f.write("=" * 80 + "\n")

def main():
    """
    Main entry point
    """
    print("=" * 80)
    print("🖥️  AI-Based Predictive Maintenance System")
    print("   Moderate Stress Data Collection (2 Hours)")
    print("=" * 80)
    print()
    
    # Get laptop name
    laptop_name = input("Enter laptop identifier (e.g., Laptop1, Laptop2, Laptop3): ").strip()
    if not laptop_name:
        laptop_name = "Laptop1"
    
    # Show configuration
    print("\n" + "=" * 80)
    print("📋 CONFIGURATION")
    print("=" * 80)
    print(f"  Laptop: {laptop_name}")
    print(f"  Duration: 2 hours (7200 seconds)")
    print(f"  Interval: 0.5 seconds")
    print(f"  Expected Samples: ~14,400")
    print(f"  Focus: Moderate load states")
    print("=" * 80)
    
    # Show requirements
    print("\n⚠️  REQUIREMENTS:")
    print("  1. Close heavy applications (games, video editing, etc.)")
    print("  2. Keep laptop plugged in (avoid power throttling)")
    print("  3. Ensure at least 100 MB free disk space")
    print("  4. Do NOT close this window during collection")
    print("  5. The system will be under MODERATE load")
    print("  6. The laptop will generate its own moderate workload")
    print()
    print("📌 The script will run for 2 hours continuously.")
    print("   Press Ctrl+C at any time to stop early.\n")
    
    # Confirm start
    confirm = input("Ready to start collection? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n❌ Collection cancelled.")
        return
    
    # Check psutil
    try:
        import psutil
        print(f"✅ psutil version: {psutil.__version__}")
    except ImportError:
        print("\n❌ psutil is not installed!")
        print("   Install it with: pip install psutil")
        return
    
    # Create and run collector
    collector = ModerateDataCollector(
        laptop_name=laptop_name,
        interval=0.5,
        duration_seconds=7200  # 2 hours
    )
    
    try:
        collector.collect_data()
    except KeyboardInterrupt:
        print("\n\n⏹️ Collection interrupted by user.")
        collector.running = False
        time.sleep(1)
        collector.collect_data()  # This will show the summary

if __name__ == "__main__":
    main()