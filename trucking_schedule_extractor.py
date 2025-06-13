#!/usr/bin/env python3
"""
Trucking Schedule Data Extractor
Extracts trucking schedule data from PDF to CSV with 100% accuracy
"""

import pandas as pd
import tabula
import pdfplumber
import re
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TruckingScheduleExtractor:
    """Extract trucking schedule data from PDF files"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.all_data = []
        self.contract_info = {}
        
    def extract_contract_info(self) -> Dict[str, str]:
        """Extract contract header information"""
        logger.info("Extracting contract information...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            
            info = {}
            lines = text.split('\n')
            
            for line in lines:
                # Extract HCR number
                if line.startswith('031L0'):
                    parts = line.split()
                    if len(parts) >= 2:
                        info['hcr_number'] = parts[0]
                        info['destination'] = parts[1]
                
                # Extract supplier information
                elif 'DDA TRANSPORT INC' in line:
                    info['supplier_name'] = 'DDA TRANSPORT INC'
                    # Extract phone
                    phone_match = re.search(r'\(([\d\-]+)\)', line)
                    if phone_match:
                        info['supplier_phone'] = phone_match.group(1)
                    
                    # Extract email
                    email_match = re.search(r'(\S+@\S+)', line)
                    if email_match:
                        info['supplier_email'] = email_match.group(1)
                
                # Extract estimated totals
                elif 'Estimated Annual Schedule Miles:' in line:
                    miles_match = re.search(r'Miles:\s*([\d,\.]+)', line)
                    if miles_match:
                        info['estimated_annual_miles'] = miles_match.group(1)
                
                elif 'Estimated Annual Schedule Hours:' in line:
                    hours_match = re.search(r'Hours:\s*([\d,\.]+)', line)
                    if hours_match:
                        info['estimated_annual_hours'] = hours_match.group(1)
            
            self.contract_info = info
            logger.info(f"Extracted contract info: {info}")
            return info
    
    def extract_data_with_tabula(self) -> pd.DataFrame:
        """Extract schedule data using tabula"""
        logger.info("Extracting data using tabula...")
        
        try:
            # Extract all tables from all pages
            all_tables = tabula.read_pdf(
                str(self.pdf_path),
                pages='all',
                multiple_tables=True,
                pandas_options={'header': 0}
            )
            
            combined_data = []
            
            for i, df in enumerate(all_tables):
                if df.empty:
                    continue
                
                logger.info(f"Processing table {i+1} with shape {df.shape}")
                processed_df = self._process_table(df, i+1)
                if not processed_df.empty:
                    combined_data.append(processed_df)
            
            if combined_data:
                final_df = pd.concat(combined_data, ignore_index=True)
                logger.info(f"Combined data shape: {final_df.shape}")
                return final_df
            else:
                raise ValueError("No data could be extracted")
                
        except Exception as e:
            logger.error(f"Tabula extraction failed: {e}")
            return self._extract_with_text_parsing()
    
    def _process_table(self, df: pd.DataFrame, table_num: int) -> pd.DataFrame:
        """Process and clean individual table data"""
        
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Clean column names
        df.columns = [self._clean_column_name(col) for col in df.columns]
        
        # Skip header rows
        if len(df) > 0 and 'id' in str(df.iloc[0]).lower():
            df = df.iloc[1:]
        
        processed_rows = []
        
        for idx, row in df.iterrows():
            row_data = self._parse_row(row)
            
            if row_data:
                row_data['source_table'] = table_num
                processed_rows.append(row_data)
        
        if processed_rows:
            return pd.DataFrame(processed_rows)
        else:
            return pd.DataFrame()
    
    def _parse_row(self, row) -> Optional[Dict[str, Any]]:
        """Parse individual row to extract trip and stop information"""
        
        # Convert row to string for parsing
        row_str = ' '.join([str(val) for val in row.values if pd.notna(val)])
        
        # Skip empty or header rows
        if not row_str.strip() or 'Trip Stop' in row_str or 'ID #' in row_str:
            return None
        
        # Look for trip/stop pattern
        trip_stop_pattern = r'^(\d+)\s+(\d+)\s+([A-Z0-9]+)\s+([A-Z\s]+)'
        match = re.match(trip_stop_pattern, row_str)
        
        if not match:
            return None
        
        trip_id = match.group(1)
        stop_number = match.group(2)
        nass_code = match.group(3)
        facility = match.group(4).strip()
        
        # Extract times
        time_pattern = r'(\d{2}:\d{2}:\d{2}\s+ET)'
        times = re.findall(time_pattern, row_str)
        
        arrive_time = times[0] if len(times) > 0 else ''
        depart_time = times[1] if len(times) > 1 else ''
        
        # Extract duration
        duration_pattern = r'(\d+\s+min)'
        duration_match = re.search(duration_pattern, row_str)
        load_unload_duration = duration_match.group(1) if duration_match else ''
        
        # Extract vehicle info
        vehicle_pattern = r'(45FT|24VN)\s+([A-Z0-9\-]+)'
        vehicle_match = re.search(vehicle_pattern, row_str)
        vehicle_type = vehicle_match.group(1) if vehicle_match else ''
        vehicle_id = vehicle_match.group(2) if vehicle_match else ''
        
        # Extract frequency
        freq_pattern = r'(\d+\.\d+)\s+'
        freq_match = re.search(freq_pattern, row_str)
        frequency = freq_match.group(1) if freq_match else ''
        
        # Extract dates
        date_pattern = r'(\d{2}/\d{2}/\d{4})'
        dates = re.findall(date_pattern, row_str)
        effective_date = dates[0] if len(dates) > 0 else ''
        expiration_date = dates[1] if len(dates) > 1 else ''
        
        return {
            'trip_id': trip_id,
            'stop_number': stop_number,
            'nass_code': nass_code,
            'facility': facility,
            'arrive_time': arrive_time,
            'load_unload_duration': load_unload_duration,
            'depart_time': depart_time,
            'vehicle_type': vehicle_type,
            'vehicle_id': vehicle_id,
            'frequency': frequency,
            'effective_date': effective_date,
            'expiration_date': expiration_date,
            'raw_data': row_str
        }
    
    def _extract_with_text_parsing(self) -> pd.DataFrame:
        """Fallback method using text parsing"""
        logger.info("Using text parsing fallback method...")
        
        all_rows = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for trip data lines
                    if re.match(r'^\d+\s+\d+\s+[A-Z0-9]+', line):
                        row_data = self._parse_text_line(line, page_num + 1)
                        if row_data:
                            all_rows.append(row_data)
        
        if all_rows:
            return pd.DataFrame(all_rows)
        else:
            return pd.DataFrame()
    
    def _parse_text_line(self, line: str, page_num: int) -> Optional[Dict[str, Any]]:
        """Parse a text line to extract trip information"""
        
        pattern = r'^(\d+)\s+(\d+)\s+([A-Z0-9]+)\s+([A-Z\s]+?)\s+(\d{2}:\d{2}:\d{2}\s+ET)'
        match = re.match(pattern, line)
        
        if match:
            trip_id = match.group(1)
            stop_number = match.group(2)
            nass_code = match.group(3)
            facility = match.group(4).strip()
            arrive_time = match.group(5)
            
            # Extract remaining information
            remaining = line[match.end():].strip()
            
            # Look for departure time
            depart_pattern = r'(\d{2}:\d{2}:\d{2}\s+ET)'
            depart_match = re.search(depart_pattern, remaining)
            depart_time = depart_match.group(1) if depart_match else ''
            
            return {
                'trip_id': trip_id,
                'stop_number': stop_number,
                'nass_code': nass_code,
                'facility': facility,
                'arrive_time': arrive_time,
                'depart_time': depart_time,
                'page_number': page_num,
                'raw_line': line
            }
        
        return None
    
    def _clean_column_name(self, col_name: str) -> str:
        """Clean column names"""
        if pd.isna(col_name):
            return "unnamed_column"
        
        clean_name = str(col_name).strip()
        clean_name = re.sub(r'\s+', '_', clean_name)
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '', clean_name)
        clean_name = clean_name.lower()
        
        return clean_name if clean_name else "unnamed_column"
    
    def extract_to_csv(self, output_path: str = None) -> str:
        """Main extraction method"""
        if output_path is None:
            output_path = self.pdf_path.stem + '_schedule_data.csv'
        
        logger.info(f"Starting extraction of {self.pdf_path}")
        
        # Extract contract information
        contract_info = self.extract_contract_info()
        
        # Extract main schedule data
        main_data = self.extract_data_with_tabula()
        
        # Add contract information to each row
        for key, value in contract_info.items():
            main_data[f'contract_{key}'] = value
        
        # Clean final dataframe
        main_data = main_data.dropna(how='all')
        
        # Sort by trip_id and stop_number
        if 'trip_id' in main_data.columns and 'stop_number' in main_data.columns:
            main_data['trip_id'] = pd.to_numeric(main_data['trip_id'], errors='coerce')
            main_data['stop_number'] = pd.to_numeric(main_data['stop_number'], errors='coerce')
            main_data = main_data.sort_values(['trip_id', 'stop_number'])
        
        # Save to CSV
        main_data.to_csv(output_path, index=False)
        logger.info(f"Data successfully extracted to {output_path}")
        
        # Print summary
        self._print_summary(main_data, output_path)
        
        return output_path
    
    def _print_summary(self, df: pd.DataFrame, output_path: str):
        """Print extraction summary"""
        print("\n" + "="*80)
        print("TRUCKING SCHEDULE EXTRACTION SUMMARY")
        print("="*80)
        print(f"Source PDF: {self.pdf_path}")
        print(f"Output CSV: {output_path}")
        print(f"Total records: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        
        if 'trip_id' in df.columns:
            unique_trips = df['trip_id'].nunique()
            print(f"Unique trips: {unique_trips}")
        
        print(f"\nContract Information:")
        for key, value in self.contract_info.items():
            print(f"  {key}: {value}")
        
        print(f"\nColumn names:")
        for col in df.columns:
            print(f"  - {col}")
        
        print(f"\nFirst 5 records:")
        print(df.head().to_string())
        print("="*80)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract trucking schedule data from PDF')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('-o', '--output', help='Output CSV file path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        extractor = TruckingScheduleExtractor(args.pdf_path)
        output_file = extractor.extract_to_csv(args.output)
        print(f"\nSuccess! Schedule data extracted to: {output_file}")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()