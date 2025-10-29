import pandas as pd
import re
import dns.resolver
import smtplib
from pathlib import Path
import logging
from typing import List, Dict, Tuple
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailListCleaner:
    def __init__(self):
        # Common disposable email domains
        self.disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com', 'mailinator.com',
            'temp-mail.org', 'throwaway.email', 'yopmail.com', 'maildrop.cc',
            'tempm.com', 'getnada.com', '33mail.com', 'emailondeck.com'
        }
        
        # Common role-based email prefixes
        self.role_based_prefixes = {
            'admin', 'administrator', 'support', 'help', 'info', 'contact',
            'sales', 'marketing', 'webmaster', 'noreply', 'no-reply',
            'postmaster', 'hostmaster', 'listmaster', 'abuse', 'security'
        }
        
        # Statistics tracking
        self.stats = {
            'original_count': 0,
            'duplicates_removed': 0,
            'invalid_format': 0,
            'disposable_emails': 0,
            'role_based_emails': 0,
            'invalid_domains': 0,
            'final_count': 0
        }

    def clean_email_list(self, input_file: str, email_column: str = 'email', 
                        output_file: str = None, advanced_validation: bool = False) -> pd.DataFrame:
        """
        Main function to clean email list
        
        Parameters:
        input_file (str): Path to input CSV/Excel file
        email_column (str): Name of column containing emails
        output_file (str): Path for output file (optional)
        advanced_validation (bool): Enable DNS and SMTP validation (slower)
        
        Returns:
        pd.DataFrame: Cleaned email dataframe
        """
        
        print("🧹 EMAIL LIST CLEANER STARTING...")
        print("=" * 50)
        
        # Load data
        df = self._load_data(input_file)
        if df is None:
            return None
            
        # Verify email column exists
        if email_column not in df.columns:
            print(f"❌ Column '{email_column}' not found!")
            print(f"Available columns: {list(df.columns)}")
            return None
        
        self.stats['original_count'] = len(df)
        print(f"📊 Original email count: {self.stats['original_count']}")
        
        # Step 1: Basic cleaning
        df = self._basic_cleaning(df, email_column)
        
        # Step 2: Remove duplicates
        df = self._remove_duplicates(df, email_column)
        
        # Step 3: Validate email format
        df = self._validate_email_format(df, email_column)
        
        # Step 4: Remove disposable emails
        df = self._remove_disposable_emails(df, email_column)
        
        # Step 5: Remove role-based emails
        df = self._remove_role_based_emails(df, email_column)
        
        # Step 6: Advanced validation (optional)
        if advanced_validation:
            print("\n🔍 Running advanced validation...")
            df = self._advanced_validation(df, email_column)
        
        # Final statistics
        self.stats['final_count'] = len(df)
        self._print_summary()
        
        # Save cleaned data
        if output_file:
            self._save_cleaned_data(df, output_file)
        
        return df

    def _load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from CSV or Excel file"""
        try:
            file_ext = Path(file_path).suffix.lower()
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                print(f"❌ Unsupported file format: {file_ext}")
                return None
            
            print(f"✅ Loaded {len(df)} records from {file_path}")
            return df
            
        except Exception as e:
            print(f"❌ Error loading file: {str(e)}")
            return None

    def _basic_cleaning(self, df: pd.DataFrame, email_column: str) -> pd.DataFrame:
        """Basic cleaning: trim whitespace, convert to lowercase"""
        print("\n1️⃣ Basic cleaning...")
        
        # Remove leading/trailing whitespace and convert to lowercase
        df[email_column] = df[email_column].astype(str).str.strip().str.lower()
        
        # Remove rows with empty emails
        initial_count = len(df)
        df = df[df[email_column] != '']
        df = df[df[email_column] != 'nan']
        df = df.dropna(subset=[email_column])
        
        removed = initial_count - len(df)
        if removed > 0:
            print(f"   ✅ Removed {removed} empty email entries")
        
        return df

    def _remove_duplicates(self, df: pd.DataFrame, email_column: str) -> pd.DataFrame:
        """Remove duplicate email addresses"""
        print("\n2️⃣ Removing duplicates...")
        
        initial_count = len(df)
        df = df.drop_duplicates(subset=[email_column], keep='first')
        
        self.stats['duplicates_removed'] = initial_count - len(df)
        if self.stats['duplicates_removed'] > 0:
            print(f"   ✅ Removed {self.stats['duplicates_removed']} duplicate emails")
        else:
            print("   ✅ No duplicates found")
        
        return df

    def _validate_email_format(self, df: pd.DataFrame, email_column: str) -> pd.DataFrame:
        """Validate email format using regex"""
        print("\n3️⃣ Validating email format...")
        
        # Comprehensive email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Create mask for valid emails
        valid_mask = df[email_column].str.match(email_pattern, na=False)
        
        self.stats['invalid_format'] = len(df) - valid_mask.sum()
        df = df[valid_mask]
        
        if self.stats['invalid_format'] > 0:
            print(f"   ✅ Removed {self.stats['invalid_format']} emails with invalid format")
        else:
            print("   ✅ All emails have valid format")
        
        return df

    def _remove_disposable_emails(self, df: pd.DataFrame, email_column: str) -> pd.DataFrame:
        """Remove disposable/temporary email addresses"""
        print("\n4️⃣ Removing disposable emails...")
        
        # Extract domain from email
        df['domain'] = df[email_column].str.split('@').str[1]
        
        # Create mask for non-disposable emails
        non_disposable_mask = ~df['domain'].isin(self.disposable_domains)
        
        self.stats['disposable_emails'] = len(df) - non_disposable_mask.sum()
        df = df[non_disposable_mask]
        
        # Remove temporary domain column
        df = df.drop('domain', axis=1)
        
        if self.stats['disposable_emails'] > 0:
            print(f"   ✅ Removed {self.stats['disposable_emails']} disposable emails")
        else:
            print("   ✅ No disposable emails found")
        
        return df

    def _remove_role_based_emails(self, df: pd.DataFrame, email_column: str) -> pd.DataFrame:
        """Remove role-based email addresses (admin@, support@, etc.)"""
        print("\n5️⃣ Removing role-based emails...")
        
        # Extract local part (before @) from email
        df['local_part'] = df[email_column].str.split('@').str[0]
        
        # Create mask for non-role-based emails
        non_role_mask = ~df['local_part'].isin(self.role_based_prefixes)
        
        self.stats['role_based_emails'] = len(df) - non_role_mask.sum()
        df = df[non_role_mask]
        
        # Remove temporary local_part column
        df = df.drop('local_part', axis=1)
        
        if self.stats['role_based_emails'] > 0:
            print(f"   ✅ Removed {self.stats['role_based_emails']} role-based emails")
        else:
            print("   ✅ No role-based emails found")
        
        return df

    def _advanced_validation(self, df: pd.DataFrame, email_column: str) -> pd.DataFrame:
        """Advanced validation: DNS MX record checking"""
        print("\n6️⃣ Advanced domain validation...")
        
        # Extract unique domains
        domains = df[email_column].str.split('@').str[1].unique()
        valid_domains = set()
        invalid_domains = set()
        
        print(f"   🔍 Checking {len(domains)} unique domains...")
        
        for i, domain in enumerate(domains):
            if i % 50 == 0:  # Progress indicator
                print(f"   Progress: {i}/{len(domains)}")
            
            if self._check_domain_mx_record(domain):
                valid_domains.add(domain)
            else:
                invalid_domains.add(domain)
            
            # Small delay to avoid overwhelming DNS servers
            time.sleep(0.1)
        
        # Filter out emails with invalid domains
        df['domain'] = df[email_column].str.split('@').str[1]
        valid_domain_mask = df['domain'].isin(valid_domains)
        
        self.stats['invalid_domains'] = len(df) - valid_domain_mask.sum()
        df = df[valid_domain_mask]
        
        # Remove temporary domain column
        df = df.drop('domain', axis=1)
        
        if self.stats['invalid_domains'] > 0:
            print(f"   ✅ Removed {self.stats['invalid_domains']} emails with invalid domains")
        else:
            print("   ✅ All domains are valid")
        
        return df

    def _check_domain_mx_record(self, domain: str) -> bool:
        """Check if domain has valid MX record"""
        try:
            dns.resolver.resolve(domain, 'MX')
            return True
        except:
            return False

    def _print_summary(self):
        """Print cleaning summary statistics"""
        print("\n" + "=" * 50)
        print("📈 CLEANING SUMMARY")
        print("=" * 50)
        print(f"Original emails:        {self.stats['original_count']:,}")
        print(f"Duplicates removed:     {self.stats['duplicates_removed']:,}")
        print(f"Invalid format:         {self.stats['invalid_format']:,}")
        print(f"Disposable emails:      {self.stats['disposable_emails']:,}")
        print(f"Role-based emails:      {self.stats['role_based_emails']:,}")
        print(f"Invalid domains:        {self.stats['invalid_domains']:,}")
        print("-" * 50)
        print(f"Final clean emails:     {self.stats['final_count']:,}")
        
        if self.stats['original_count'] > 0:
            retention_rate = (self.stats['final_count'] / self.stats['original_count']) * 100
            print(f"Retention rate:         {retention_rate:.1f}%")

    def _save_cleaned_data(self, df: pd.DataFrame, output_file: str):
        """Save cleaned data to file"""
        try:
            file_ext = Path(output_file).suffix.lower()
            if file_ext == '.csv':
                df.to_csv(output_file, index=False)
            elif file_ext in ['.xlsx', '.xls']:
                df.to_excel(output_file, index=False)
            
            print(f"\n💾 Cleaned data saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving file: {str(e)}")

    def analyze_email_domains(self, df: pd.DataFrame, email_column: str) -> Dict:
        """Analyze email domains in the cleaned list"""
        domains = df[email_column].str.split('@').str[1].value_counts()
        
        print("\n📊 TOP EMAIL DOMAINS:")
        print("-" * 30)
        for domain, count in domains.head(10).items():
            print(f"{domain:<20} {count:>8}")
        
        return domains.to_dict()

# Convenience functions for quick use
def quick_clean_emails(input_file: str, email_column: str = 'email', 
                      output_file: str = None, advanced: bool = False):
    """Quick function to clean email list"""
    cleaner = EmailListCleaner()
    
    if output_file is None:
        # Auto-generate output filename
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}")
    
    cleaned_df = cleaner.clean_email_list(input_file, email_column, output_file, advanced)
    
    if cleaned_df is not None:
        # Show domain analysis
        cleaner.analyze_email_domains(cleaned_df, email_column)
    
    return cleaned_df

# Example usage and testing
if __name__ == "__main__":
    print("""
EMAIL LIST CLEANER
==================

To use this script, you can either:

1. QUICK CLEAN (basic validation only):
   quick_clean_emails('your_email_list.csv', 'Email', 'cleaned_emails.csv')

2. ADVANCED CLEAN (includes DNS validation - slower):
   quick_clean_emails('your_email_list.csv', 'Email', 'cleaned_emails.csv', advanced=True)

3. CUSTOM CLEANING:
   cleaner = EmailListCleaner()
   cleaned_data = cleaner.clean_email_list('input.csv', 'Email', 'output.csv')

FEATURES:
✅ Remove duplicates
✅ Validate email format
✅ Remove disposable emails (tempmail, etc.)
✅ Remove role-based emails (admin@, support@)
✅ Optional DNS validation
✅ Detailed statistics
✅ Support CSV and Excel files

EXAMPLE:
--------
# Basic cleaning
quick_clean_emails('my_emails.csv', 'email_address', 'clean_emails.csv')

# Advanced cleaning with DNS validation
quick_clean_emails('my_emails.csv', 'email_address', 'clean_emails.csv', advanced=True)
""")

# Uncomment to run with your file:
# quick_clean_emails('your_file.csv', 'your_email_column')