import pandas as pd
import boto3
import json
import io

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    data_key = 'final-output/final_cleaned_data.csv'
    config_key = 'scripts/cpi_config.json'
    
    # Load Config and Data
    config_obj = s3.get_object(Bucket=bucket, Key=config_key)
    config = json.loads(config_obj['Body'].read())
    
    data_obj = s3.get_object(Bucket=bucket, Key=data_key)
    df = pd.read_csv(io.BytesIO(data_obj['Body'].read()))
    
    # Apply Fixed-Base Adjustment
    def apply_inflation(row):
        region_stats = config['regions'].get(row['region'])
        
        if region_stats:
            # Always calculate ratio from the 2023 baseline
            ratio = region_stats['current_cpi'] / region_stats['base_cpi_2023']
            
            row['annual_budget_shortfall'] = round(row['annual_budget_shortfall'] * ratio)
            row['Cost Per Meal ($)'] = round(row['Cost Per Meal ($)'] * ratio, 2)
        return row

    df = df.apply(apply_inflation, axis=1)
    
    # 3. Save to the Presentation Layer file
    output_key = 'final-output/adjusted_final_data.csv'
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    s3.put_object(Bucket=bucket, Key=output_key, Body=csv_buffer.getvalue())
    
    return {"status": "success"}