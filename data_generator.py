"""
Synthetic Health Insurance Claims Data Generator
Generates realistic-looking claims data for dashboard demonstration purposes.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random


def generate_claims_data(n_claims: int = 5000, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic health insurance claims data.

    Parameters:
    -----------
    n_claims : int
        Number of unique claims to generate
    seed : int
        Random seed for reproducibility

    Returns:
    --------
    pd.DataFrame
        DataFrame containing synthetic claims data
    """
    np.random.seed(seed)
    random.seed(seed)

    # Define reference data
    groups = ['GRP001', 'GRP002', 'GRP003', 'GRP004', 'GRP005', 'GRP006', 'GRP007', 'GRP008']
    subgroups = ['A', 'B', 'C', 'D', 'E']
    packages = ['Gold', 'Silver', 'Bronze', 'Platinum']

    claim_types = ['Medical', 'Pharmacy', 'Dental', 'Vision', 'Mental Health']
    claim_type_weights = [0.55, 0.20, 0.10, 0.05, 0.10]

    place_of_service = ['Office', 'Inpatient Hospital', 'Outpatient Hospital', 'Emergency Room',
                        'Ambulatory Surgical Center', 'Skilled Nursing Facility', 'Home Health',
                        'Telehealth', 'Urgent Care', 'Laboratory']

    provider_types = ['Primary Care', 'Specialist', 'Hospital', 'Pharmacy', 'Lab',
                      'Imaging Center', 'Therapist', 'Dentist', 'Optometrist']

    network_statuses = ['In-Network', 'Out-of-Network', 'Preferred']
    network_weights = [0.75, 0.15, 0.10]

    claim_statuses = ['Paid', 'Denied', 'Pending', 'Adjusted', 'Partially Paid']
    status_weights = [0.78, 0.08, 0.05, 0.05, 0.04]

    denial_reasons = ['Not Covered', 'Prior Auth Required', 'Duplicate Claim',
                      'Timely Filing', 'Invalid Diagnosis', 'Coordination of Benefits',
                      'Member Not Eligible', 'Benefit Maximum Reached']

    states = ['CA', 'TX', 'NY', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI',
              'NJ', 'VA', 'WA', 'AZ', 'MA', 'TN', 'IN', 'MO', 'MD', 'WI']

    # Service duration options with weights
    service_durations = [0, 0, 0, 1, 2, 3, 5, 7, 14, 30]
    duration_weights = [0.5, 0.15, 0.1, 0.05, 0.05, 0.03, 0.05, 0.03, 0.02, 0.02]

    # Line count options with weights
    line_counts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    line_weights = [0.35, 0.25, 0.15, 0.10, 0.05, 0.04, 0.02, 0.02, 0.01, 0.01]

    # Generate base claim data
    claims = []

    # Date range for claims (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    for i in range(n_claims):
        claim_id = f'CLM{str(i+1).zfill(10)}'

        # Generate subscriber info
        subscriber_id = f'SUB{str(random.randint(1, 9999)).zfill(8)}'
        member_id = f'MBR{str(random.randint(1, 14999)).zfill(8)}'
        group = random.choice(groups)
        subgroup = random.choice(subgroups)
        package = random.choice(packages)

        # Generate dates with realistic relationships
        # First service date - use Python random for timedelta compatibility
        days_from_start = random.randint(0, 729)
        first_service_date = start_date + timedelta(days=days_from_start)

        # Last service date (same day to 30 days after first service)
        service_duration = random.choices(service_durations, weights=duration_weights, k=1)[0]
        last_service_date = first_service_date + timedelta(days=service_duration)

        # Received date (1-60 days after last service, with most within 30 days)
        days_to_receive = min(int(random.expovariate(1/10)) + 1, 90)
        received_date = last_service_date + timedelta(days=days_to_receive)

        # Paid/Processed date (1-45 days after received, with some outliers)
        processing_time = int(random.expovariate(1/8)) + 1
        # Add some outliers for timeliness analysis
        if random.random() < 0.1:  # 10% are delayed
            processing_time = random.randint(30, 89)
        if random.random() < 0.03:  # 3% are significantly delayed
            processing_time = random.randint(60, 179)
        paid_date = received_date + timedelta(days=processing_time)

        # Ensure paid_date doesn't exceed current date
        if paid_date > end_date:
            paid_date = end_date

        # Claim details
        claim_type = random.choices(claim_types, weights=claim_type_weights, k=1)[0]
        pos = random.choice(place_of_service)
        provider_type = random.choice(provider_types)
        network = random.choices(network_statuses, weights=network_weights, k=1)[0]

        # Financial data
        # Billed amount based on claim type and place of service
        base_amounts = {
            'Medical': random.lognormvariate(5.5, 1.2),
            'Pharmacy': random.lognormvariate(4.0, 1.0),
            'Dental': random.lognormvariate(5.0, 0.8),
            'Vision': random.lognormvariate(4.5, 0.6),
            'Mental Health': random.lognormvariate(5.2, 0.9)
        }
        billed_amount = round(base_amounts[claim_type], 2)

        # Allowed amount (percentage of billed, varies by network)
        allowed_pcts = {
            'In-Network': random.uniform(0.60, 0.90),
            'Out-of-Network': random.uniform(0.40, 0.70),
            'Preferred': random.uniform(0.75, 0.95)
        }
        allowed_amount = round(billed_amount * allowed_pcts[network], 2)

        # Member cost sharing
        deductible_options = [0, 0, 0, 250, 500, 1000]
        deductible = round(min(allowed_amount * random.uniform(0, 0.3),
                              random.choice(deductible_options)), 2)

        remaining_after_ded = allowed_amount - deductible

        # Coinsurance (member portion after deductible)
        coinsurance_options = [0.10, 0.20, 0.30, 0.40]
        coinsurance_weights_opt = [0.3, 0.4, 0.2, 0.1]
        coinsurance_pct = random.choices(coinsurance_options, weights=coinsurance_weights_opt, k=1)[0]
        coinsurance = round(remaining_after_ded * coinsurance_pct, 2)

        # Copay (fixed amount for certain services)
        copay_options = [0, 0, 15, 25, 35, 50, 75]
        copay = round(random.choice(copay_options), 2)

        # Paid amount (what insurance pays)
        paid_amount = round(max(0, allowed_amount - deductible - coinsurance - copay), 2)

        # Member responsibility
        member_responsibility = round(allowed_amount - paid_amount, 2)

        # Claim status
        status = random.choices(claim_statuses, weights=status_weights, k=1)[0]

        # Denial reason (only for denied claims)
        denial_reason = None
        if status == 'Denied':
            denial_reason = random.choice(denial_reasons)
            paid_amount = 0

        # Number of line items (1-10, weighted toward fewer)
        n_lines = random.choices(line_counts, weights=line_weights, k=1)[0]

        # Generate line items
        for line_num in range(1, n_lines + 1):
            # Distribute amounts across lines
            line_pct = 1 / n_lines if line_num < n_lines else 1 - (n_lines - 1) / n_lines

            # Add some variation
            line_pct *= random.uniform(0.7, 1.3)

            claims.append({
                'claim_id': claim_id,
                'line_number': line_num,
                'subscriber_id': subscriber_id,
                'member_id': member_id,
                'group_id': group,
                'subgroup_id': subgroup,
                'package': package,
                'first_service_date': first_service_date.date(),
                'last_service_date': last_service_date.date(),
                'received_date': received_date.date(),
                'paid_date': paid_date.date(),
                'claim_type': claim_type,
                'place_of_service': pos,
                'provider_type': provider_type,
                'provider_id': f'PRV{str(random.randint(1, 4999)).zfill(6)}',
                'provider_state': random.choice(states),
                'network_status': network,
                'diagnosis_code': f'{chr(random.randint(65, 90))}{random.randint(10, 99)}.{random.randint(0, 9)}',
                'procedure_code': f'{random.randint(10000, 99999)}',
                'billed_amount': round(billed_amount * line_pct, 2),
                'allowed_amount': round(allowed_amount * line_pct, 2),
                'deductible': round(deductible * line_pct, 2),
                'coinsurance': round(coinsurance * line_pct, 2),
                'copay': copay if line_num == 1 else 0,  # Copay only on first line
                'paid_amount': round(paid_amount * line_pct, 2),
                'member_responsibility': round(member_responsibility * line_pct, 2),
                'claim_status': status,
                'denial_reason': denial_reason,
                'units': random.randint(1, 9),
                'days_to_receive': days_to_receive,
                'days_to_process': processing_time,
                'total_turnaround_days': days_to_receive + processing_time
            })

    df = pd.DataFrame(claims)

    # Add derived columns for timeliness analysis
    df['received_within_30_days'] = df['days_to_receive'] <= 30
    df['processed_within_14_days'] = df['days_to_process'] <= 14
    df['processed_within_30_days'] = df['days_to_process'] <= 30
    df['timely_filing'] = df['days_to_receive'] <= 90

    # Add month/year columns for trending
    df['service_month'] = pd.to_datetime(df['first_service_date']).dt.to_period('M')
    df['received_month'] = pd.to_datetime(df['received_date']).dt.to_period('M')
    df['paid_month'] = pd.to_datetime(df['paid_date']).dt.to_period('M')

    return df


def get_summary_stats(df: pd.DataFrame) -> dict:
    """Calculate summary statistics for the claims data."""
    return {
        'total_claims': df['claim_id'].nunique(),
        'total_lines': len(df),
        'total_billed': df['billed_amount'].sum(),
        'total_allowed': df['allowed_amount'].sum(),
        'total_paid': df['paid_amount'].sum(),
        'avg_processing_days': df.groupby('claim_id')['days_to_process'].first().mean(),
        'avg_turnaround_days': df.groupby('claim_id')['total_turnaround_days'].first().mean(),
        'pct_processed_14_days': df.groupby('claim_id')['processed_within_14_days'].first().mean() * 100,
        'pct_processed_30_days': df.groupby('claim_id')['processed_within_30_days'].first().mean() * 100,
    }


if __name__ == '__main__':
    # Generate sample data and save to CSV
    df = generate_claims_data(n_claims=5000)
    df.to_csv('sample_claims_data.csv', index=False)
    print(f"Generated {len(df)} claim lines from {df['claim_id'].nunique()} unique claims")
    print("\nSample data:")
    print(df.head())
    print("\nColumn types:")
    print(df.dtypes)
