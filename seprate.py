import pandas as pd
import os
from pathlib import Path

def split_excel_by_industry(file_path, industry_column_name=None, output_format='separate_files', output_path=None, verbose=True):
    """
    Split Excel file by industry into separate files or sheets

    Parameters:
    file_path (str): Path to your Excel file
    industry_column_name (str): Name of the column containing industry data
    output_format (str): 'separate_files' or 'single_file_multiple_sheets'
    output_path (str): Custom output path (file path for single file, directory for separate files)
    verbose (bool): Whether to print progress messages
    """

    try:
        # Read the Excel file
        if verbose:
            print("Reading Excel file...")
        df = pd.read_excel(file_path)
        if verbose:
            print(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")

        # Display column names to help identify industry column
        if verbose:
            print("\nColumn names in your file:")
            for i, col in enumerate(df.columns):
                print(f"{i+1}. {col}")

        # If industry column not specified, try to auto-detect
        if industry_column_name is None:
            # Look for columns that might contain industry data
            potential_columns = [col for col in df.columns
                               if any(keyword in col.lower()
                                     for keyword in ['industry', 'sector', 'business', 'category', 'type'])]

            if potential_columns:
                industry_column_name = potential_columns[0]
                if verbose:
                    print(f"\nAuto-detected industry column: '{industry_column_name}'")
            else:
                if verbose:
                    print("\nPlease specify the industry column name manually")
                return

        # Verify the column exists
        if industry_column_name not in df.columns:
            if verbose:
                print(f"Error: Column '{industry_column_name}' not found in the file")
            return

        # Get unique industries
        industries = df[industry_column_name].dropna().unique()
        if verbose:
            print(f"\nFound {len(industries)} unique industries:")
            for industry in sorted(industries):
                count = len(df[df[industry_column_name] == industry])
                print(f"  - {industry}: {count} records")
        
        # Determine output location
        if output_path:
            if output_format == 'separate_files':
                output_dir = Path(output_path)
                output_dir.mkdir(exist_ok=True)
            else:  # single_file_multiple_sheets
                output_dir = Path(output_path).parent
                output_dir.mkdir(exist_ok=True)
        else:
            output_dir = Path("industry_split_output")
            output_dir.mkdir(exist_ok=True)

        if output_format == 'separate_files':
            # Create separate Excel files for each industry
            if verbose:
                print("\nCreating separate files for each industry...")

            for industry in industries:
                # Filter data for this industry
                industry_data = df[df[industry_column_name] == industry]

                # Create safe filename
                safe_filename = "".join(c for c in str(industry) if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_filename = safe_filename.replace(' ', '_')
                if output_path:
                    output_file = Path(output_path) / f"{safe_filename}.xlsx"
                else:
                    output_file = output_dir / f"{safe_filename}.xlsx"

                # Save to Excel
                industry_data.to_excel(output_file, index=False)
                if verbose:
                    print(f"  ✓ Created: {output_file} ({len(industry_data)} rows)")

        elif output_format == 'single_file_multiple_sheets':
            # Create single Excel file with multiple sheets
            if output_path:
                output_file = Path(output_path)
            else:
                output_file = output_dir / "all_industries_by_sheet.xlsx"
            if verbose:
                print(f"\nCreating single file with multiple sheets: {output_file}")

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                for industry in industries:
                    # Filter data for this industry
                    industry_data = df[df[industry_column_name] == industry]

                    # Create safe sheet name (Excel sheet names have limitations)
                    safe_sheet_name = str(industry)[:31]  # Excel sheet name limit
                    safe_sheet_name = "".join(c for c in safe_sheet_name if c.isalnum() or c in (' ', '-', '_'))

                    # Write to sheet
                    industry_data.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                    if verbose:
                        print(f"  ✓ Created sheet: {safe_sheet_name} ({len(industry_data)} rows)")

        output_location = output_path if output_path else str(output_dir)
        if verbose:
            print(f"\n✅ Successfully split the data! Output saved in: {output_location}")

        # Summary statistics
        total_processed = sum(len(df[df[industry_column_name] == industry]) for industry in industries)
        if verbose:
            print(f"\nSummary:")
            print(f"  - Original rows: {len(df)}")
            print(f"  - Processed rows: {total_processed}")
            print(f"  - Industries: {len(industries)}")

    except Exception as e:
        if verbose:
            print(f"Error: {str(e)}")
            print("Please check your file path and ensure the Excel file is not open in another program")
        raise  # Re-raise the exception for the web app to handle

# Example usage functions
def quick_split_separate_files(file_path, industry_column_name):
    """Quick function to split into separate files"""
    split_excel_by_industry(file_path, industry_column_name, 'separate_files')

def quick_split_single_file(file_path, industry_column_name):
    """Quick function to split into single file with multiple sheets"""
    split_excel_by_industry(file_path, industry_column_name, 'single_file_multiple_sheets')

def analyze_file_structure(file_path):
    """Analyze the Excel file structure to identify potential industry columns"""
    try:
        df = pd.read_excel(file_path)
        print(f"File Analysis for: {file_path}")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print("\nColumn Analysis:")
        
        for col in df.columns:
            unique_values = df[col].nunique()
            sample_values = df[col].dropna().unique()[:5]
            print(f"\n{col}:")
            print(f"  - Unique values: {unique_values}")
            print(f"  - Sample values: {list(sample_values)}")
            
            # Suggest if this might be the industry column
            if unique_values > 2 and unique_values < len(df) * 0.5:
                print(f"  *** This might be your industry column! ***")
                
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")

# HOW TO USE:
print("""
HOW TO USE THIS SCRIPT:

1. BASIC USAGE (if you know your industry column name):
   split_excel_by_industry('your_file.xlsx', 'Industry_Column_Name')

2. ANALYZE YOUR FILE FIRST (to find column names):
   analyze_file_structure('your_file.xlsx')

3. QUICK SPLIT INTO SEPARATE FILES:
   quick_split_separate_files('your_file.xlsx', 'Industry_Column_Name')

4. QUICK SPLIT INTO SINGLE FILE WITH MULTIPLE SHEETS:
   quick_split_single_file('your_file.xlsx', 'Industry_Column_Name')

EXAMPLES:
   # If your industry column is named 'Industry'
   split_excel_by_industry('my_data.xlsx', 'Industry')
   
   # If your industry column is named 'Sector'
   split_excel_by_industry('my_data.xlsx', 'Sector')
   
   # To analyze file structure first
   analyze_file_structure('my_data.xlsx')
""")

# Uncomment and modify the line below to run with your file:
# split_excel_by_industry('your_excel_file.xlsx', 'your_industry_column_name')