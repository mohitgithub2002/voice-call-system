#!/usr/bin/env python3
"""
Fee Payment Reminder - Voice Call System
Main CLI application to send fee reminders via voice calls

Usage:
    python main.py <excel_file>
    python main.py sample_students.xlsx --dry-run
    python main.py sample_students.xlsx --limit 5
"""

import sys
import os
import time
import argparse
from dotenv import load_dotenv

from excel_reader import read_students, create_sample_excel
from vobiz_caller import VobizCaller


def print_banner():
    """Print application banner."""
    print("\n" + "="*50)
    print("  📞 Fee Payment Reminder - Voice Call System")
    print("="*50 + "\n")


def main():
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Send fee payment reminders via voice calls'
    )
    parser.add_argument(
        'excel_file',
        nargs='?',
        default='sample_students.xlsx',
        help='Path to Excel file with student data'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would happen without making actual calls'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of calls to make'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=2,
        help='Delay between calls in seconds (default: 2)'
    )
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='Create a sample Excel file and exit'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Create sample file if requested
    if args.create_sample:
        create_sample_excel('sample_students.xlsx')
        print("\n📝 Add your student data to this file and run again.")
        return
    
    # Check if Excel file exists
    if not os.path.exists(args.excel_file):
        print(f"❌ Excel file not found: {args.excel_file}")
        print("\n💡 Tip: Run with --create-sample to create a template file")
        sys.exit(1)
    
    # Read student data
    print(f"📂 Reading: {args.excel_file}")
    try:
        students = read_students(args.excel_file)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    if not students:
        print("⚠️  No students found in the Excel file")
        sys.exit(1)
    
    print(f"✅ Found {len(students)} students with pending fees\n")
    
    # Apply limit if specified
    if args.limit:
        students = students[:args.limit]
        print(f"📌 Limited to {args.limit} students\n")
    
    # Dry run mode
    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual calls will be made\n")
        print("-" * 40)
        for student in students:
            print(f"📱 {student['student_name']}")
            print(f"   Phone: {student['phone_number']}")
            print(f"   Fees: ₹{student['pending_fees']}")
            print(f"   Due: {student['due_date']}")
            print()
        print("-" * 40)
        print(f"\n✅ Would call {len(students)} students")
        return
    
    # Initialize Vobiz caller
    try:
        caller = VobizCaller()
    except ValueError as e:
        print(f"❌ {e}")
        print("\n💡 Add your Vobiz credentials to .env file")
        sys.exit(1)
    
    # Confirm before making calls
    print("⚠️  You are about to make real phone calls!")
    print(f"   Students: {len(students)}")
    print(f"   Delay between calls: {args.delay} seconds\n")
    
    confirm = input("Continue? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Cancelled")
        return
    
    print("\n" + "="*50)
    print("Starting calls...")
    print("="*50 + "\n")
    
    # Track results
    results = {
        'success': 0,
        'failed': 0,
        'calls': []
    }
    
    # Make calls
    for i, student in enumerate(students, 1):
        print(f"[{i}/{len(students)}] Calling {student['student_name']}...", end=" ")
        
        result = caller.make_call(student)
        
        if result['status'] == 'initiated':
            print(f"✅ Call initiated (UUID: {result['call_uuid'][:20]}...)")
            results['success'] += 1
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            results['failed'] += 1
        
        results['calls'].append(result)
        
        # Delay between calls (except for last one)
        if i < len(students):
            time.sleep(args.delay)
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"✅ Successful: {results['success']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📊 Total: {len(students)}")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
