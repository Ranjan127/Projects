#!/usr/bin/env python3
"""
Excel Industry Splitter - Command Line Tool
Usage:
    python seprate_cli.py analyze <filename.xlsx>
    python seprate_cli.py split <filename.xlsx> <column_name> [--separate|--single]
"""

import pandas as pd
import os
import sys
from pathlib import Path

def analyze_file_structure(file_path):
    """Analyze the Excel file structure to identify potential industry columns"""
    try:
        df = pd.read_excel(file_path)
        print(f"📊 File Analysis for: {file_path}")
        print(f"📈 Rows: {len(df)}")
        print(f"📋 Columns: {len(df.columns)}")
        print("\n🔍 Column Analysis:")
        
        for col in df.columns:
            unique_values = df[col].nunique()
            sample_values = df[col].dropna().unique()[:5]
            print(f"\n{col}:")
            print(f"  - Unique values: {unique_values}")
            print(f"  - Sample values: {list(sample_values)}")
            
            # Suggest if this might be the industry column
            if unique_values > 2 and unique_values < len(df) * 0.5:
                print(f"  ⭐ This might be your industry column! ⭐")
                
    except Exception as e:
        print(f"❌ Error analyzing file: {str(e)}")

def split_excel_by_industry(file_path, industry_column_name, output_format='separate_files'):
    """Split Excel file by industry into separate files or sheets"""
    
    try:
        # Read the Excel file
        print("📖 Reading Excel file...")
        df = pd.read_excel(file_path)
        print(f"✅ Successfully loaded {len(df)} rows and {len(df.columns)} columns")
        
        # Verify the column exists
        if industry_column_name not in df.columns:
            print(f"❌ Error: Column '{industry_column_name}' not found in the file")
            print("Available columns:")
            for col in df.columns:
                print(f"  - {col}")
            return
        
        # Get unique industries
        industries = df[industry_column_name].dropna().unique()
        print(f"\n🔍 Found {len(industries)} unique industries:")
        for industry in sorted(industries):
            count = len(df[df[industry_column_name] == industry])
            print(f"  - {industry}: {count} records")
        
        # Create output directory
        output_dir = Path("industry_split_output")
        output_dir.mkdir(exist_ok=True)
        
        if output_format == 'separate_files':
            # Create separate Excel files for each industry
            print("\n📁 Creating separate files for each industry...")
            
            for industry in industries:
                industry_data = df[df[industry_column_name] == industry]
                
                # Create safe filename
                safe_filename = "".join(c for c in str(industry) if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_filename = safe_filename.replace(' ', '_')
                output_file = output_dir / f"{safe_filename}.xlsx"
                
                # Save to Excel
                industry_data.to_excel(output_file, index=False)
                print(f"  ✅ Created: {output_file} ({len(industry_data)} rows)")
        
        elif output_format == 'single_file_multiple_sheets':
            # Create single Excel file with multiple sheets
            output_file = output_dir / "all_industries_by_sheet.xlsx"
            print(f"\n📄 Creating single file with multiple sheets: {output_file}")
            
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                for industry in industries:
                    industry_data = df[df[industry_column_name] == industry]
                    
                    # Create safe sheet name
                    safe_sheet_name = str(industry)[:31]
                    safe_sheet_name = "".join(c for c in safe_sheet_name if c.isalnum() or c in (' ', '-', '_'))
                    
                    industry_data.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                    print(f"  ✅ Created sheet: {safe_sheet_name} ({len(industry_data)} rows)")
        
        print(f"\n🎉 Successfully split the data! Output saved in: {output_dir}")
        
        # Summary
        total_processed = sum(len(df[df[industry_column_name] == industry]) for industry in industries)
        print(f"\n📊 Summary:")
        print(f"  - Original rows: {len(df)}")
        print(f"  - Processed rows: {total_processed}")
        print(f"  - Industries: {len(industries)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Please check your file path and ensure the Excel file is not open in another program")

def print_help():
    """Print help message for command-line usage"""
    print("""
🎯 Excel Industry Splitter - Command Line Usage
==============================================

Commands:
1. Analyze file structure:
   python seprate_cli.py analyze <filename.xlsx>

2. Split into separate files:
   python seprate_cli.py split <filename.xlsx> <column_name>

3. Split into single file with multiple sheets:
   python seprate_cli.py split <filename.xlsx> <column_name> --single

Examples:
   python seprate_cli.py analyze laura accounts.xlsx
   python seprate_cli.py split laura accounts.xlsx Industry
   python seprate_cli.py split laura accounts.xlsx Sector --single
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
    
    elif command == 'analyze':
        if len(sys.argv) < 3:
            print("❌ Usage: python seprate_cli.py analyze <filename.xlsx>")
            return
        file_path = sys.argv[2]
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        analyze_file_structure(file_path)
    
    elif command == 'split':
        if len(sys.argv) < 4:
            print("❌ Usage: python seprate_cli.py split <filename.xlsx> <column_name> [--single]")
            return
        
        file_path = sys.argv[2]
        column_name = sys.argv[3]
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        output_format = 'separate_files'
        if len(sys.argv) > 4 and sys.argv[4] == '--single':
            output_format = 'single_file_multiple_sheets'
        
        split_excel_by_industry(file_path, column_name, output_format)
    
    else:
        print(f"❌ Unknown command: {command}")
        print_help()

if __name__ == "__main__":
    main()
