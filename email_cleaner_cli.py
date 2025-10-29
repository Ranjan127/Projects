#!/usr/bin/env python3
"""
Email List Cleaner - Command Line Tool
Usage:
    python email_cleaner_cli.py clean <filename> <email_column> [options]
    python email_cleaner_cli.py analyze <filename> <email_column>
"""

import sys
import os
from pathlib import Path
from cleaner import EmailListCleaner

def print_help():
    """Print help message for command-line usage"""
    print("""
📧 Email List Cleaner - Command Line Usage
=========================================

Commands:
1. Clean email list:
   python email_cleaner_cli.py clean <filename> <email_column> [options]

2. Analyze email domains:
   python email_cleaner_cli.py analyze <filename> <email_column>

Options:
   --output FILE    Specify output filename (default: auto-generated)
   --advanced       Enable DNS validation (slower but more thorough)
   --format FORMAT  Output format: csv or excel (default: same as input)

Examples:
   python email_cleaner_cli.py clean emails.csv email
   python email_cleaner_cli.py clean emails.csv Email --advanced
   python email_cleaner_cli.py clean data.xlsx email_address --output cleaned_emails.csv
   python email_cleaner_cli.py analyze emails.csv email
""")

def main():
    """Main command-line interface"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command in ['help', '--help', '-h']:
        print_help()
        return
    
    elif command == 'clean':
        if len(sys.argv) < 4:
            print("❌ Usage: python email_cleaner_cli.py clean <filename> <email_column> [options]")
            return
        
        filename = sys.argv[2]
        email_column = sys.argv[3]
        
        # Parse options
        output_file = None
        advanced = False
        output_format = None
        
        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == '--output' and i + 1 < len(sys.argv):
                output_file = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--advanced':
                advanced = True
                i += 1
            elif sys.argv[i] == '--format' and i + 1 < len(sys.argv):
                output_format = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        # Check if file exists
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return
        
        # Auto-generate output filename if not provided
        if output_file is None:
            input_path = Path(filename)
            output_file = str(input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}")
        
        # Run cleaning
        cleaner = EmailListCleaner()
        cleaned_df = cleaner.clean_email_list(filename, email_column, output_file, advanced)
        
        if cleaned_df is not None:
            print(f"\n✅ Cleaning completed! Cleaned data saved to: {output_file}")
    
    elif command == 'analyze':
        if len(sys.argv) < 4:
            print("❌ Usage: python email_cleaner_cli.py analyze <filename> <email_column>")
            return
        
        filename = sys.argv[2]
        email_column = sys.argv[3]
        
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return
        
        # Load data and analyze
        import pandas as pd
        try:
            file_ext = Path(filename).suffix.lower()
            if file_ext == '.csv':
                df = pd.read_csv(filename)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(filename)
            else:
                print("❌ Unsupported file format")
                return
            
            if email_column not in df.columns:
                print(f"❌ Column '{email_column}' not found")
                print(f"Available columns: {list(df.columns)}")
                return
            
            # Analyze domains
            cleaner = EmailListCleaner()
            cleaner.analyze_email_domains(df, email_column)
            
        except Exception as e:
            print(f"❌ Error analyzing file: {str(e)}")
    
    else:
        print(f"❌ Unknown command: {command}")
        print_help()

if __name__ == "__main__":
    main()
