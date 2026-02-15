"""Main pipeline orchestration."""
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from orchestration.run_context import RunContext
from transforms.normalize import normalize_loans_df, normalize_sfy_df, normalize_prime_df
from transforms.enrichment import (
    tag_loans_by_group, add_seller_loan_number, mark_repurchased_loans, enrich_buy_df
)
from rules.purchase_price import check_purchase_price, get_purchase_price_exceptions
from rules.underwriting import check_underwriting, get_underwriting_exceptions
from rules.comap import check_comap_prime, check_comap_sfy, check_comap_notes
from rules.eligibility import check_eligibility_prime, check_eligibility_sfy
from outputs.excel_exports import export_exception_reports
from outputs.eligibility_reports import export_eligibility_report
from storage import get_storage_backend
from db.models import PipelineRun, RunStatus, LoanException, LoanFact
from orchestration.archive_run import archive_run
from db.connection import SessionLocal
from config.settings import settings
from utils.date_utils import calculate_pipeline_dates
from utils.file_discovery import discover_input_files
from utils.json_serial import to_json_safe
from config.rejection_criteria import (
    get_rejection_criteria,
    DISPOSITION_TO_PURCHASE,
    DISPOSITION_PROJECTED,
    DISPOSITION_REJECTED,
)

logger = logging.getLogger(__name__)

WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _weekday_from_pdate(pdate: str):
    """Return (weekday_index 0-6, weekday_name) from pdate YYYY-MM-DD."""
    try:
        dt = datetime.strptime(pdate, "%Y-%m-%d")
        return dt.weekday(), WEEKDAY_NAMES[dt.weekday()]
    except (ValueError, TypeError):
        return None, None


class PipelineExecutor:
    """Main pipeline execution engine."""
    
    def __init__(self, context: RunContext):
        self.context = context
        self.db = SessionLocal()
        self.run_record: Optional[PipelineRun] = None
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def load_reference_data(self, folder: str) -> Dict[str, pd.DataFrame]:
        """Load all reference data files."""
        data = {}
        
        try:
            # Load master sheets
            data['loans_types'] = pd.read_excel(f"{folder}/files_required/MASTER_SHEET.xlsx")
            data['notes'] = pd.read_excel(f"{folder}/files_required/MASTER_SHEET - Notes.xlsx")
            data['existing_file'] = pd.read_csv(f"{folder}/files_required/current_assets.csv")
            
            # Load underwriting grids
            underwriting_file = f"{folder}/files_required/Underwriting_Grids_COMAP.xlsx"
            data['underwriting_sfy'] = pd.read_excel(underwriting_file, sheet_name='SFY')
            data['underwriting_prime'] = pd.read_excel(underwriting_file, sheet_name='Prime')
            data['underwriting_sfy_notes'] = pd.read_excel(underwriting_file, sheet_name='SFY - Notes')
            data['underwriting_prime_notes'] = pd.read_excel(underwriting_file, sheet_name='Prime - Notes')
            
            # Load CoMAP grids
            data['sfy_comap'] = pd.read_excel(underwriting_file, sheet_name='SFY COMAP')
            data['sfy_comap2'] = pd.read_excel(underwriting_file, sheet_name='SFY COMAP2')
            data['prime_comap'] = pd.read_excel(underwriting_file, sheet_name='Prime CoMAP')
            data['sfy_comap_oct25'] = pd.read_excel(underwriting_file, sheet_name='SFY COMAP')
            data['sfy_comap_oct25_2'] = pd.read_excel(underwriting_file, sheet_name='SFY COMAP2')
            data['prime_comap_oct25'] = pd.read_excel(underwriting_file, sheet_name='Prime CoMAP')
            data['notes_comap'] = pd.read_excel(underwriting_file, sheet_name='Notes CoMAP')
            
            logger.info("Reference data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading reference data: {e}")
            raise
        
        return data
    
    def load_input_files(self, folder: str) -> Dict[str, pd.DataFrame]:
        """Load input loan files with dynamic file discovery."""
        files = {}
        
        try:
            # Calculate dates for file discovery
            pdate, yesterday, last_end = calculate_pipeline_dates(self.context.pdate)
            
            # Discover input files
            file_paths = discover_input_files(
                directory=folder,
                yesterday=yesterday,
                sfy_date=None,  # Auto-discover most recent
                prime_date=None  # Auto-discover most recent
            )
            
            # Load tape loans
            if file_paths['loans']:
                files['loans'] = pd.read_csv(file_paths['loans'])
            else:
                raise FileNotFoundError("Tape20Loans file not found")
            
            # Load SFY and Prime files
            if file_paths['sfy_file']:
                sfy_df = pd.read_excel(file_paths['sfy_file'])
                files['sfy_df'] = normalize_sfy_df(sfy_df)
            else:
                raise FileNotFoundError("SFY file not found")
            
            if file_paths['prime_file']:
                prime_df = pd.read_excel(file_paths['prime_file'])
                files['prime_df'] = normalize_prime_df(prime_df)
            else:
                raise FileNotFoundError("PRIME file not found")
            
            logger.info(f"Input files loaded successfully from {folder}")
            
        except Exception as e:
            logger.error(f"Error loading input files: {e}")
            raise
        
        return files
    
    def create_run_record(self) -> PipelineRun:
        """Create pipeline run record in database (with day-of-week from pdate)."""
        run_weekday, run_weekday_name = _weekday_from_pdate(self.context.pdate)
        run_record = PipelineRun(
            run_id=self.context.run_id,
            status=RunStatus.PENDING,
            sales_team_id=self.context.sales_team_id,
            created_by_id=self.context.created_by_id,
            pdate=self.context.pdate,
            irr_target=self.context.irr_target,
            input_file_path=self.context.input_file_path,
            output_dir=self.context.output_dir,
            run_weekday=run_weekday,
            run_weekday_name=run_weekday_name,
        )
        
        self.db.add(run_record)
        self.db.commit()
        self.db.refresh(run_record)
        self.run_record = run_record
        
        logger.info(f"Created run record: {self.context.run_id} (weekday={run_weekday_name})")
        return run_record
    
    def update_run_status(self, status: RunStatus, **kwargs):
        """Update run status and metadata."""
        if self.run_record:
            self.run_record.status = status
            if status == RunStatus.RUNNING:
                self.run_record.started_at = datetime.utcnow()
            elif status in [RunStatus.COMPLETED, RunStatus.FAILED]:
                self.run_record.completed_at = datetime.utcnow()
            
            for key, value in kwargs.items():
                if hasattr(self.run_record, key):
                    setattr(self.run_record, key, value)
            
            self.db.commit()

    def _set_phase(self, phase: str) -> None:
        """Record the current pipeline phase (for diagnosing stuck runs: data vs code)."""
        if self.run_record and hasattr(self.run_record, "last_phase"):
            self.run_record.last_phase = phase
            self.db.commit()
    
    def save_exceptions(self, exceptions: List[Dict[str, Any]]):
        """Save loan exceptions to database with canonical rejection_criteria."""
        for exc_data in exceptions:
            exc_type = exc_data.get("exception_type", "")
            exc_cat = exc_data.get("exception_category", "unknown")
            rejection_criteria = get_rejection_criteria(exc_type, exc_cat) or exc_data.get("rejection_criteria")
            exception = LoanException(
                run_id=self.run_record.id,
                seller_loan_number=exc_data["seller_loan_number"],
                exception_type=exc_type,
                exception_category=exc_cat,
                severity=exc_data.get("severity", "warning"),
                message=exc_data.get("message", ""),
                rejection_criteria=rejection_criteria,
                loan_data=to_json_safe(exc_data.get("loan_data") or {}),
            )
            self.db.add(exception)
        
        self.db.commit()
        logger.info(f"Saved {len(exceptions)} exceptions")
    
    def save_loan_facts(
        self,
        final_df: pd.DataFrame,
        rejected_loans: Optional[Dict[str, str]] = None,
    ):
        """Save loan facts with disposition (to_purchase / projected / rejected) and rejection_criteria."""
        rejected_loans = rejected_loans or {}
        facts = []
        
        for _, row in final_df.iterrows():
            seller = row.get("SELLER Loan #", "UNKNOWN")
            if seller in rejected_loans:
                disposition = DISPOSITION_REJECTED
                rejection_criteria = rejected_loans[seller]
            else:
                disposition = DISPOSITION_TO_PURCHASE
                rejection_criteria = None
            
            fact = LoanFact(
                run_id=self.run_record.id,
                seller_loan_number=seller,
                platform=row.get("platform"),
                loan_program=row.get("loan program"),
                application_type=row.get("Application Type"),
                orig_balance=row.get("Orig. Balance"),
                purchase_price=row.get("Purchase Price"),
                lender_price_pct=row.get("Lender Price(%)"),
                fico_borrower=row.get("FICO Borrower"),
                dti=row.get("DTI"),
                pti=row.get("PTI"),
                term=row.get("Term"),
                apr=row.get("APR"),
                property_state=row.get("Property State"),
                purchase_price_check=row.get("purchase_price_check", False),
                disposition=disposition,
                rejection_criteria=rejection_criteria,
                loan_data=to_json_safe(row.to_dict()),
            )
            facts.append(fact)
        
        self.db.bulk_save_objects(facts)
        self.db.commit()
        logger.info(f"Saved {len(facts)} loan facts (to_purchase vs rejected by criteria)")
    
    def execute(self, folder: str) -> Dict[str, Any]:
        """Execute the full pipeline."""
        try:
            # Create run record
            self.create_run_record()
            self.update_run_status(RunStatus.RUNNING)
            self._set_phase("load_reference_data")
            
            # Load data
            ref_data = self.load_reference_data(folder)
            self._set_phase("load_input_files")
            input_files = self.load_input_files(folder)
            
            self._set_phase("normalize_loans")
            # Process loans
            loans = normalize_loans_df(input_files['loans'])
            loans = tag_loans_by_group(loans)
            loans = add_seller_loan_number(loans)
            loans = mark_repurchased_loans(loans)
            
            # Process SFY and Prime data
            sfy_df = input_files['sfy_df']
            prime_df = input_files['prime_df']
            
            sfy_df['Platform'] = "SFY"
            prime_df['Platform'] = "PRIME"
            
            tuloans = sfy_df[sfy_df.get('TU144', 0) == 1]['SELLER Loan #'].values if 'TU144' in sfy_df.columns else []
            if 'TU144' in sfy_df.columns:
                sfy_df.drop(columns=['TU144'], inplace=True)
            
            # Combine buy data
            buy_df = pd.concat([prime_df, sfy_df])
            buy_df.rename(columns={"Loan Program": "loan program"}, inplace=True)
            # Convert to string and handle NaN before string operations
            if 'loan program' in buy_df.columns:
                buy_df['loan program'] = buy_df['loan program'].astype(str).replace('nan', '')
            buy_df['loan program'] = buy_df.apply(
                lambda x: str(x['loan program']) + 'notes' if x.get('Application Type') == 'HD NOTE' else str(x['loan program']),
                axis=1
            )
            
            # Prepare loan types
            df_loans_types = ref_data['loans_types'].copy()
            # Convert to string and handle NaN before calling .str.upper()
            if 'platform' in df_loans_types.columns:
                df_loans_types['platform'] = df_loans_types['platform'].astype(str).replace('nan', '')
                df_loans_types["Platform"] = df_loans_types['platform'].str.upper()
            
            notes = ref_data['notes'].copy()
            # Convert to string and handle NaN before string operations
            if 'loan program' in notes.columns:
                notes['loan program'] = notes['loan program'].astype(str).replace('nan', '')
            notes['loan program'] = notes['loan program'].apply(lambda x: str(x) + 'notes' if pd.notna(x) else 'notes')
            # Convert to string and handle NaN before calling .str.upper()
            if 'platform' in notes.columns:
                notes['platform'] = notes['platform'].astype(str).replace('nan', '')
                notes["Platform"] = notes['platform'].str.upper()
            df_loans_types = pd.concat([df_loans_types, notes])
            
            # Enrich buy dataframe
            buy_df = enrich_buy_df(buy_df, df_loans_types, self.context.pdate, self.context.irr_target)
            
            # Process existing file
            existing_file = ref_data['existing_file'].copy()
            existing_file['Submit Date'] = pd.to_datetime(existing_file['Submit Date'])
            existing_file['Purchase_Date'] = pd.to_datetime(existing_file['Purchase_Date'])
            existing_file['Monthly Payment Date'] = pd.to_datetime(existing_file['Monthly Payment Date'])
            
            # Mark repurchased loans
            repurchased_loans = loans[loans['Repurchased'] == True]['SELLER Loan #'].values
            existing_file.loc[existing_file['SELLER Loan #'].isin(repurchased_loans), 'Repurchase'] = True
            
            # Combine final dataframes
            final_df = pd.concat([buy_df, existing_file[existing_file['Purchase_Date'] > '2025-10-01']])
            final_df_all = pd.concat([buy_df, existing_file])
            
            # Run validations
            buy_df = check_purchase_price(buy_df)
            final_df = check_purchase_price(final_df)
            
            self._set_phase("underwriting")
            # Collect exceptions
            all_exceptions = []
            
            # Purchase price exceptions
            purchase_exceptions = get_purchase_price_exceptions(final_df)
            all_exceptions.extend(purchase_exceptions)
            
            # Underwriting checks (returns tuple: (flagged_loans, min_income_loans))
            flagged_loans_sfy, min_income_sfy = check_underwriting(
                buy_df, ref_data['underwriting_sfy'], is_notes=False, tuloans=list(tuloans)
            )
            flagged_loans_prime, min_income_prime = check_underwriting(
                buy_df, ref_data['underwriting_prime'], is_notes=False, tuloans=list(tuloans)
            )
            flagged_loans = flagged_loans_sfy + flagged_loans_prime
            
            flagged_notes, min_income_notes = check_underwriting(
                buy_df, ref_data['underwriting_sfy_notes'], is_notes=True, tuloans=list(tuloans)
            )
            
            all_exceptions.extend(get_underwriting_exceptions(buy_df, flagged_loans_sfy, 'underwriting_sfy'))
            all_exceptions.extend(get_underwriting_exceptions(buy_df, flagged_loans_prime, 'underwriting_prime'))
            all_exceptions.extend(get_underwriting_exceptions(buy_df, flagged_notes, 'underwriting_notes'))
            
            self._set_phase("comap")
            # CoMAP checks
            loan_not_in_comap = check_comap_prime(
                buy_df, ref_data['prime_comap'], ref_data['prime_comap_oct25'],
                ref_data['prime_comap_oct25'], pd.to_datetime(self.context.pdate)
            )
            loan_not_in_comap.extend(check_comap_sfy(
                buy_df, ref_data['sfy_comap'], ref_data['sfy_comap2'],
                ref_data['sfy_comap_oct25'], ref_data['sfy_comap_oct25_2'],
                pd.to_datetime(self.context.pdate)
            ))
            loan_not_in_comap.extend(check_comap_notes(buy_df, ref_data['notes_comap']))
            
            # CoMAP exceptions for DB and rejection_criteria mapping
            for (seller_loan_number, _prog, platform) in loan_not_in_comap:
                exc_type = "comap_prime" if platform == "PRIME" else ("comap_sfy" if platform == "SFY" else "comap_notes")
                match = buy_df[buy_df["SELLER Loan #"] == seller_loan_number]
                row = match.iloc[0].to_dict() if len(match) > 0 else {}
                all_exceptions.append({
                    "seller_loan_number": seller_loan_number,
                    "exception_type": exc_type,
                    "exception_category": "not_in_comap",
                    "severity": "error",
                    "message": f"Loan not in CoMAP grid ({platform})",
                    "loan_data": row,
                })
            
            self._set_phase("eligibility")
            # Eligibility checks (pass buy_df for SFY check_l5)
            eligibility_prime = check_eligibility_prime(final_df_all)
            eligibility_sfy = check_eligibility_sfy(final_df_all, buy_df=buy_df)
            
            self._set_phase("export_reports")
            # Prepare exception reports
            purchase_mismatch = final_df[final_df['purchase_price_check'] == False]
            flagged_df = buy_df[buy_df['SELLER Loan #'].isin(flagged_loans)]
            notes_flagged_df = buy_df[buy_df['SELLER Loan #'].isin(flagged_notes)]
            comap_failed_df = buy_df[buy_df['SELLER Loan #'].isin([i[0] for i in loan_not_in_comap])]
            
            # Export reports to configured storage (local in dev, S3 in test/prod).
            # Store per-run outputs under a stable prefix so the frontend can download them.
            output_prefix = self.context.output_dir or f"runs/{self.context.run_id}"
            share_prefix = output_prefix
            storage_outputs = get_storage_backend(area="outputs")
            storage_share = get_storage_backend(area="output_share")

            reports = export_exception_reports(
                purchase_mismatch,
                flagged_df,
                notes_flagged_df,
                comap_failed_df,
                output_prefix=output_prefix,
                output_share_prefix=share_prefix,
                storage=storage_outputs,
                share_storage=storage_share,
            )
            
            # Export eligibility check results
            eligibility_report_path = export_eligibility_report(
                eligibility_prime,
                eligibility_sfy,
                f"{settings.OUTPUT_DIR}/{output_prefix}" if settings.STORAGE_TYPE == "local" else f"/tmp/{output_prefix}"
            )
            reports['eligibility_report'] = eligibility_report_path
            
            # Build rejected_loans map: first rejection_criteria per loan (for disposition)
            rejected_loans = {}
            for exc in all_exceptions:
                sn = exc.get("seller_loan_number")
                if not sn or sn in rejected_loans:
                    continue
                rc = get_rejection_criteria(
                    exc.get("exception_type", ""),
                    exc.get("exception_category", ""),
                )
                if rc:
                    rejected_loans[sn] = rc
            
            self._set_phase("save_db")
            # Save to database
            self.save_exceptions(all_exceptions)
            self.save_loan_facts(final_df, rejected_loans=rejected_loans)
            
            # Update run summary
            self.update_run_status(
                RunStatus.COMPLETED,
                total_loans=len(final_df),
                total_balance=float(final_df['Orig. Balance'].sum()),
                exceptions_count=len(all_exceptions)
            )
            
            # Archive input and output files to archive/{run_id}/input and archive/{run_id}/output
            eligibility_report_path = reports.get("eligibility_report")
            archive_run(
                run_id=self.context.run_id,
                folder=folder,
                pdate=self.context.pdate,
                output_prefix=output_prefix,
                reports=reports,
                output_storage=storage_outputs,
                eligibility_report_local_path=eligibility_report_path,
            )
            
            # Store eligibility results in run record
            eligibility_summary = {
                'prime': {
                    'total_checks': len(eligibility_prime),
                    'passed': sum(1 for v in eligibility_prime.values() if isinstance(v, dict) and v.get('pass') == True),
                    'failed': sum(1 for v in eligibility_prime.values() if isinstance(v, dict) and v.get('pass') == False)
                },
                'sfy': {
                    'total_checks': len(eligibility_sfy),
                    'passed': sum(1 for v in eligibility_sfy.values() if isinstance(v, dict) and v.get('pass') == True),
                    'failed': sum(1 for v in eligibility_sfy.values() if isinstance(v, dict) and v.get('pass') == False)
                }
            }
            
            result = {
                'run_id': self.context.run_id,
                'status': 'completed',
                'total_loans': len(final_df),
                'total_balance': float(final_df['Orig. Balance'].sum()),
                'exceptions_count': len(all_exceptions),
                'reports': reports,
                'eligibility_prime': eligibility_prime,
                'eligibility_sfy': eligibility_sfy,
                'eligibility_summary': eligibility_summary
            }
            
            logger.info(f"Pipeline completed successfully: {self.context.run_id}")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            self.update_run_status(RunStatus.FAILED, errors=[str(e)])
            raise
