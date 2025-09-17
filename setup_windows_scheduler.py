#!/usr/bin/env python3
"""
WINDOWS TASK SCHEDULER SETUP
Sets up daily automation to run via Windows Task Scheduler

This script creates a Windows Task Scheduler task that runs the daily automation
every day at a specified time with proper environment variables and logging.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, time
import json

def main():
    print("🕐 WINDOWS TASK SCHEDULER SETUP")
    print("=" * 60)
    print("Setting up daily automation for InvestingDojo.co")
    print()
    
    # Get current directory
    current_dir = Path.cwd()
    automation_script = current_dir / "COMPLETE_DAILY_AUTOMATION.py"
    
    print(f"📁 Project directory: {current_dir}")
    print(f"🐍 Python executable: {sys.executable}")
    print(f"📜 Automation script: {automation_script}")
    print()
    
    # Check if script exists
    if not automation_script.exists():
        print("❌ ERROR: COMPLETE_DAILY_AUTOMATION.py not found!")
        return False
    
    # Get user input for schedule
    print("⏰ SCHEDULE CONFIGURATION")
    print("-" * 30)
    
    # Default to 6:00 AM
    default_hour = 6
    default_minute = 0
    
    try:
        hour_input = input(f"Enter hour (0-23) [default: {default_hour}]: ").strip()
        hour = int(hour_input) if hour_input else default_hour
        
        minute_input = input(f"Enter minute (0-59) [default: {default_minute}]: ").strip()
        minute = int(minute_input) if minute_input else default_minute
        
        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            raise ValueError("Invalid time")
            
    except ValueError:
        print("❌ Invalid time entered. Using default: 06:00")
        hour, minute = default_hour, default_minute
    
    schedule_time = f"{hour:02d}:{minute:02d}"
    print(f"✅ Scheduled time: {schedule_time}")
    print()
    
    # Get API key
    print("🔑 API KEY CONFIGURATION")
    print("-" * 30)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        api_key = input("Enter your GEMINI_API_KEY: ").strip()
        if not api_key:
            print("❌ ERROR: GEMINI_API_KEY is required!")
            return False
    else:
        print("✅ GEMINI_API_KEY found in environment")
    
    print()
    
    # Create batch file for task scheduler
    batch_file = current_dir / "run_daily_automation.bat"
    
    batch_content = f"""@echo off
REM InvestingDojo Daily Automation
REM Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

cd /d "{current_dir}"

REM Set environment variables
set GEMINI_API_KEY={api_key}

REM Run the automation
"{sys.executable}" "{automation_script}"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Log completion
echo Automation completed at %date% %time% >> logs\\scheduler_log.txt
"""
    
    print("📝 CREATING BATCH FILE")
    print("-" * 30)
    
    try:
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        print(f"✅ Batch file created: {batch_file}")
    except Exception as e:
        print(f"❌ Error creating batch file: {e}")
        return False
    
    print()
    
    # Create the scheduled task
    task_name = "InvestingDojo-Daily-Automation"
    
    print("📅 CREATING SCHEDULED TASK")
    print("-" * 30)
    
    # Delete existing task if it exists
    try:
        subprocess.run([
            "schtasks", "/delete", "/tn", task_name, "/f"
        ], capture_output=True, check=False)
    except:
        pass
    
    # Create new task
    try:
        cmd = [
            "schtasks", "/create",
            "/tn", task_name,
            "/tr", str(batch_file),
            "/sc", "daily",
            "/st", schedule_time,
            "/f"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Scheduled task created successfully!")
        print(f"   Task name: {task_name}")
        print(f"   Schedule: Daily at {schedule_time}")
        print(f"   Command: {batch_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating scheduled task: {e}")
        print(f"   Command output: {e.stdout}")
        print(f"   Command error: {e.stderr}")
        return False
    
    print()
    
    # Create configuration file
    config = {
        "task_name": task_name,
        "schedule_time": schedule_time,
        "batch_file": str(batch_file),
        "automation_script": str(automation_script),
        "created_date": datetime.now().isoformat(),
        "python_executable": sys.executable,
        "project_directory": str(current_dir)
    }
    
    config_file = current_dir / "scheduler_config.json"
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"📋 Configuration saved: {config_file}")
    except Exception as e:
        print(f"⚠️ Warning: Could not save configuration: {e}")
    
    print()
    
    # Show management commands
    print("🛠️ TASK MANAGEMENT COMMANDS")
    print("-" * 30)
    print(f"View task:   schtasks /query /tn \"{task_name}\"")
    print(f"Run now:     schtasks /run /tn \"{task_name}\"")
    print(f"Delete task: schtasks /delete /tn \"{task_name}\" /f")
    print(f"Disable:     schtasks /change /tn \"{task_name}\" /disable")
    print(f"Enable:      schtasks /change /tn \"{task_name}\" /enable")
    print()
    
    # Show log locations
    print("📊 LOG LOCATIONS")
    print("-" * 30)
    print(f"Automation logs: {current_dir / 'logs'}")
    print(f"Scheduler log:   {current_dir / 'logs' / 'scheduler_log.txt'}")
    print()
    
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("Your daily automation is now scheduled to run every day")
    print(f"at {schedule_time}. Check the logs directory for execution details.")
    print()
    print("💡 NEXT STEPS:")
    print("1. Test the automation manually:")
    print(f"   python {automation_script}")
    print("2. Test the scheduled task:")
    print(f"   schtasks /run /tn \"{task_name}\"")
    print("3. Monitor logs for successful execution")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)