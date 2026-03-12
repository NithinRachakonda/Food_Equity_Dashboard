# %%
import pandas as pd

# %% [markdown]
# ## Unemployment Data (Averaging the unemployment rates)

# %%
unemployment = pd.read_excel("s3://food-equity-dashboard/raw-data/Unemployment_rate.xlsx", dtype={'State FIPS Code': str, 'County FIPS Code': str}, header=0)

# %%
unemployment.head()

# %%
unemployment = unemployment.drop(["LAUS Code", "Labor Force", "Employed", "Unemployed"], axis=1)

# %%
unemployment.tail()

# %%
unemployment = unemployment.drop([45094, 45095])
unemployment.tail()

# %%
unemployment.dtypes

# %%
# 1. Force everything to numeric. The '–' for all oct 25 entries will become NaN (null)
unemployment["Unemploy-ment Rate (%)"] = pd.to_numeric(unemployment["Unemploy-ment Rate (%)"], errors='coerce')

# 2. Drop the rows that are now NaN
unemployment = unemployment.dropna(subset=["Unemploy-ment Rate (%)"])

unemployment['full_fips'] = (
    unemployment['State FIPS Code'].astype(str).str.zfill(2) + 
    unemployment['County FIPS Code'].astype(str).str.zfill(3)
)

# 3. Now convert to int
unemployment["Unemploy-ment Rate (%)"] = unemployment["Unemploy-ment Rate (%)"].astype(int)

# %%
unemployment = unemployment.groupby(["full_fips", "County Name/State Abbreviation"]).agg(unemployment_rate = ("Unemploy-ment Rate (%)", "mean")).reset_index()

# %%
unemployment.tail()

# %%
state_map = {
    # 50 States
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
    
    # District & Territories
    'DC': 'District of Columbia',
    'PR': 'Puerto Rico',
    'VI': 'Virgin Islands',
    'GU': 'Guam',
    'AS': 'American Samoa',
    'MP': 'Northern Mariana Islands'
}

# %%
# Split the column into two temporary parts
# n=1 ensures we only split at the last comma
split_data = unemployment['County Name/State Abbreviation'].str.split(',', n=1, expand=True)

# 2. Clean up the abbreviation (remove spaces)
# We use the 'state_map' dictionary we created earlier
state_abbr = split_data[1].str.strip().str.upper()
state_full = state_abbr.map(state_map)

# 3. Create the new combined column
# split_data[0] is the County Name
unemployment['County Name/State'] = split_data[0] + ", " + state_full

# %%
unemployment.head()

# %%
unemployment["County Name/State"].isna().sum()

# %%
missingrows = unemployment[unemployment['County Name/State'].isna()]
print(missingrows)

# %%
# df.loc[condition, column] = value
unemployment.loc[unemployment['County Name/State Abbreviation'] == 'District of Columbia', 'County Name/State'] = 'District of Columbia, District of Columbia'

# %%
unemployment_final = unemployment.drop("County Name/State Abbreviation", axis=1)

unemployment_final['unemployment_rate'] = unemployment_final['unemployment_rate']/100

# %%
unemployment_final.tail()

# %%
unemployment_final["County Name/State"].isna().sum()

# %% [markdown]
# ## Poverty Rate (dublicate rows and a few calculated columns)

# %%
poverty = pd.read_csv("s3://food-equity-dashboard/raw-data/Poverty_rate.csv", header=0)

# %%
poverty.head()

# %%
poverty = poverty.drop("Unnamed: 4", axis=1)

# %%
# bfill(axis=0) pulls data UP from the row below
poverty = poverty.bfill(axis=0, limit=1)

# Filter out the estimate rows
poverty = poverty[~poverty['County'].str.contains('estimate', case=False, na=False)]

# %%
poverty = poverty.reset_index()

# %%
poverty.tail()

# %%
for i in ['Population', 'Poverty', 'Poverty_Ugstudents']:
    poverty[i] = pd.to_numeric(poverty[i].str.replace(',', ''), errors='coerce')

# %%
poverty['poverty_rate'] = (poverty['Poverty'] - poverty['Poverty_Ugstudents'])/poverty['Population']

# %%
poverty_final = poverty.drop(["Population", "Poverty", 'Poverty_Ugstudents'], axis = 1)

# %%
poverty_final.tail()

# %%
poverty_final["County"].isna().sum()

# %% [markdown]
# ### Checking for mismatches with county names in poverty and unemployment dfs as county names is the only common column to join them

# %%
missing_county =  set(unemployment_final['County Name/State']) - set(poverty['County'])
print(missing_county)

# %%
missing_county =  set(poverty['County']) - set(unemployment_final['County Name/State'])
print(missing_county)

# %%
import unicodedata

def make_common_key(text):
    if pd.isna(text): return "nan"
    
    # 1. Standardize text
    text = str(text).lower().replace(',', '').replace('/', ' ')
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
    
    # 2. PROTECT THE INDEPENDENT CITIES
    # These 6 cities have same-named counties. We detect "city" before it's stripped.
    cities_to_protect = ['baltimore', 'st. louis', 'fairfax', 'franklin', 'richmond', 'roanoke']
    is_independent_city = any(city in text for city in cities_to_protect) and "city" in text
    
    # 3. Strip "Noise" words
    noise_words = [
        "municipio", "municipality", "city and borough", "borough/city", 
        "county/city", "county/town", "borough", "town", "city", "county"
    ]
    for word in noise_words:
        text = text.replace(word, "")
    
    # Clean extra spaces
    cleaned_text = " ".join(text.split())
    
    # 4. APPEND SUFFIX if it was a protected city
    if is_independent_city:
        return f"{cleaned_text} city"
    
    return cleaned_text

# %%
# Apply to both DataFrames
unemployment_final['common_key'] = unemployment_final['County Name/State'].apply(make_common_key)
poverty_final['common_key'] = poverty_final['County'].apply(make_common_key)

# %%
missing_county =  set(unemployment_final['common_key']) - set(poverty_final['common_key'])
print(missing_county)

# %%
missing_county =  set(poverty_final['common_key']) - set(unemployment_final['common_key']) 
print(missing_county)

# %%
# Select rows where county is kalawao county, hawaii to check if it exists
filtered_df = poverty_final[poverty_final['County'] == 'Kalawao County, Hawaii']
filtered_df.head()

# %%
# Select rows where county is maui county to check its unemployment rate as kalawao is mixed with that county
filtered_df2 = unemployment_final[unemployment_final['County Name/State'] == 'Maui County, Hawaii']
filtered_df2.head()

# %%
# Add the respective row to unemployment_df, the fips code is 15005

# Define the values for Kalawao County
# Using Maui County's rate as the proxy per BLS/Census standard
new_row = {
    'full_fips': '15005',
    'unemployment_rate': 0.02538462,
    'County Name/State': 'Kalawao County, Hawaii',
    'common_key': 'kalawao hawaii'
}

# Insert into the DataFrame
# loc[len(df)] appends it to the very bottom
unemployment_final.loc[len(unemployment_final)] = new_row

# %%
unemployment_final.tail()

# %%
unemployment_final = unemployment_final.drop('County Name/State', axis=1)

# %%
poverty_final = poverty_final.drop(['County', 'index'], axis =1)

# %% [markdown]
# ## Disability rate

# %%
disability = pd.read_csv("s3://food-equity-dashboard/raw-data/Disability_rate.csv", header=0)

# %%
disability.head(10)

# %%
# bfill(axis=0) pulls data UP from the row below
disability = disability.bfill(axis=0, limit=1)

# Filter out the estimate rows
disability = disability[~disability['County'].str.contains('estimate', case=False, na=False)]
disability = disability[~disability['County'].str.contains('total', case=False, na=False)]
# Keep rows where the County is NOT exactly "with a disability", we did not use "str.contains" because in that case "percent with a disability" also gets deleted
disability = disability[disability['County'].str.strip() != 'With a disability']

# %%
disability.head(5)

# %%
# Getting the percentages aligned to the county names
disability = disability.bfill(axis=0, limit=1)

# Removing the redundant rows
disability = disability[disability['County'].str.strip() != 'Percent with a disability']

# renaming column name
disability.columns = ['County', 'disability_rate']

# %%
disability.dtypes

# %%
disability.tail()

# %%
disability['disability_rate'] = pd.to_numeric(disability['disability_rate'].astype(str).str.replace('%', ''), errors='coerce')
disability['disability_rate'] = disability['disability_rate']/100

# %%
disability.tail()

# %%
disability["County"].isna().sum()

# %%
# Use the predefined function to make the county names same for all datasets
disability['common_key'] = disability['County'].apply(make_common_key)

# resetting index
disability_final = disability.reset_index()

# %%
disability_final.tail() 

# %%
disability_final = disability_final.drop(['County', 'index'], axis = 1)

# %% [markdown]
# ## Homeownership rate

# %%
homeownership = pd.read_csv("s3://food-equity-dashboard/raw-data/Homeownership_rate.csv", header=0)

# %%
homeownership.tail()

# %%
homeownership.columns = ["County", "homeownership_rate"]

# %%
homeownership = homeownership[homeownership["County"].str.strip() != "Estimate"]

# %%
homeownership.tail()

# %%
homeownership = homeownership.bfill(axis=0, limit=1)

homeownership = homeownership[homeownership["County"].str.strip() != "Percent"]

homeownership_final = homeownership.reset_index()

# %%
homeownership_final.tail()

# %%
homeownership_final["homeownership_rate"] = homeownership_final["homeownership_rate"].astype(str).str.replace("%", "", regex=False).astype(float)/100

# %%


# %%
homeownership_final['common_key'] = homeownership_final['County'].apply(make_common_key)

# %%
homeownership_final.head()

# %%
homeownership_final = homeownership_final.drop(['County', 'index'], axis=1)

# %% [markdown]
# ## Average Meal Prices

# %%
amp = pd.read_csv("s3://food-equity-dashboard/raw-data/average_meal_prices.csv", header=0)

# %%
amp.tail()

# %%
amp['Cost Per Meal ($)'] = amp["Cost Per Meal"].str.replace("$", "", regex=False).astype(float)

# %%
amp = amp.drop("Cost Per Meal", axis=1)

# %%
amp["common_key"] = amp["County, State"].apply(make_common_key)

# %%
amp.tail()

# %%
missing_counties = set(poverty_final['common_key']) - set(amp['common_key'])
missing_counties

# %%
# Can ignore the below code as when we do inner join the puerto rico rows automatically will not be added to the final merged df

poverty_final = poverty_final[~poverty_final['common_key'].str.contains('puerto rico', case=False, na=False)]
homeownership_final = homeownership_final[~homeownership_final['common_key'].str.contains('puerto rico', case=False, na=False)]
unemployment_final = unemployment_final[~unemployment_final['common_key'].str.contains('puerto rico', case=False, na=False)]
disability_final = disability_final[~disability_final['common_key'].str.contains('puerto rico', case=False, na=False)]

# %%
amp_final = amp

# %%
print(len(poverty_final))
print(len(homeownership_final))
print(len(unemployment_final))
print(len(disability_final))
print(len(amp_final))

# %% [markdown]
# ## Population

# %%
pop = pd.read_csv("s3://food-equity-dashboard/raw-data/population.csv", header=0)

# %%
pop.columns = ["County", "population"]

# %%
pop.head()

# %%
pop = pop[pop["County"].str.strip() != "Margin of Error"]

pop = pop.bfill(axis=0, limit=1)

pop = pop[pop["County"].str.strip() != "Estimate"]

pop = pop.reset_index()

# %%
pop['population'] = pop['population'].str.replace(',', '').astype(int)
pop.head()

# %%
pop['common_key'] = pop['County'].apply(make_common_key)
pop_final = pop.drop(["County","index"], axis=1)

pop_final.head()

# %%


# %% [markdown]
# ## Calculating Food Insecurity Rate

# %%
merged_df = ( unemployment_final.merge(poverty_final, on='common_key', how='inner')
                                .merge(homeownership_final, on='common_key', how='inner')
                                .merge(disability_final, on='common_key', how='inner')
                                .merge(amp_final, on='common_key', how='inner')
                                .merge(pop_final, on='common_key', how='inner')
            )

# %%
merged_df.head()

# %%
(merged_df == 0).sum()

# %%
len(merged_df)

# %%
# Split the 'County, State' column into two new columns
# expand=True turns the result into a DataFrame instead of a list
merged_df[['county', 'state']] = merged_df['County, State'].str.split(',', n=1, expand=True)

# 2. Clean up leading/trailing spaces (important for joining!)
merged_df['county'] = merged_df['county'].str.strip()
merged_df['state'] = merged_df['state'].str.strip()

# %%
merged_df = merged_df.drop("County, State", axis=1)

# %%
order = ["common_key", "full_fips", "county", "state", "population", "unemployment_rate", "poverty_rate", "disability_rate", "homeownership_rate", "Cost Per Meal ($)"]

merged_df = merged_df[order]

# %%
merged_df.head()

# %%
# The final 2025/2023-based calculation
# Assuming rates are decimals (e.g., 0.12 for 12%)
merged_df['insecurity_rate'] = (
    0.101 + 0.013 + # Constant + 2023 Fixed Effect
    (merged_df['unemployment_rate'] * 0.460) +
    (merged_df['poverty_rate'] * 0.332) +
    (merged_df['disability_rate'] * 0.198) -
    (merged_df['homeownership_rate'] * 0.071)
)

# %%
merged_df.tail()

# %%
distinct_count = merged_df['state'].nunique()

distinct_count

# %%
state_to_abbr = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
    'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'district of columbia': 'DC',
    'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL',
    'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA',
    'maine': 'ME', 'maryland': 'MD', 'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN',
    'mississippi': 'MS', 'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
    'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
    'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK', 'oregon': 'OR',
    'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC', 'south dakota': 'SD',
    'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT', 'virginia': 'VA',
    'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
}

# %%
# Ensure the column is lowercase and stripped to match the dictionary keys
merged_df['state_abbr'] = merged_df['state'].str.lower().str.strip().map(state_to_abbr)

# Check if any states failed to map (returns NaN if not in dictionary)
missing_states = merged_df[merged_df['state_abbr'].isna()]['state'].unique()
if len(missing_states) > 0:
    print(f"Warning: These values did not match the dictionary: {missing_states}")

# %%
merged_df['state'] = merged_df['state_abbr']

merged_df = merged_df.drop("state_abbr", axis=1)

# %%
region_map = {
    # Northeast (NE)
    'CT': 'NE', 'ME': 'NE', 'MA': 'NE', 'NH': 'NE', 'RI': 'NE', 'VT': 'NE',
    'NJ': 'NE', 'NY': 'NE', 'PA': 'NE',
    
    # Midwest (MW)
    'IL': 'MW', 'IN': 'MW', 'MI': 'MW', 'OH': 'MW', 'WI': 'MW',
    'IA': 'MW', 'KS': 'MW', 'MN': 'MW', 'MO': 'MW', 'NE': 'MW', 'ND': 'MW', 'SD': 'MW',
    
    # South (S)
    'DE': 'S', 'DC': 'S', 'FL': 'S', 'GA': 'S', 'MD': 'S', 'NC': 'S', 'SC': 'S', 'VA': 'S', 'WV': 'S',
    'AL': 'S', 'KY': 'S', 'MS': 'S', 'TN': 'S',
    'AR': 'S', 'LA': 'S', 'OK': 'S', 'TX': 'S',
    
    # West (W)
    'AZ': 'W', 'CO': 'W', 'ID': 'W', 'MT': 'W', 'NV': 'W', 'NM': 'W', 'UT': 'W', 'WY': 'W',
    'AK': 'W', 'CA': 'W', 'HI': 'W', 'OR': 'W', 'WA': 'W'
}


# Create the 'region' column
merged_df['region'] = merged_df['state'].map(region_map)

# Validation check: Ensure no state was missed
if merged_df['region'].isna().any():
    print("Warning: Some states were not assigned a region!")
    print(merged_df[merged_df['region'].isna()]['state'].unique())

# %%
merged_df.head()

# %%
import numpy as np

merged_df['food_insecure_population'] = np.ceil(merged_df['population']*merged_df['insecurity_rate']).astype(int)

# %%
merged_df

# %% [markdown]
# ## Annual Budget Shortfall

# %%
# Define Map the Meal Gap 2023-based constants
NATIONAL_AVG_MEAL_COST = 3.58       # National average meal cost
NATIONAL_AVG_WEEK_SHORTFALL = 22.37 # National average weekly shortfall
WEEKS_IN_YEAR = 52
MONTHS_OF_INSECURITY_FACTOR = 7/12  # Average duration factor per person

# Calculate localized weekly shortfall per person
# Logic: $22.37 * (Local Cost Per Meal / $3.58)
merged_df['weekly_shortfall_per_person'] = (
    NATIONAL_AVG_WEEK_SHORTFALL * (merged_df['Cost Per Meal ($)'] / NATIONAL_AVG_MEAL_COST)
)

# Calculate the total Annual Budget Shortfall
# Logic: Insecure Population * Local Weekly Shortfall * 52 weeks * 7/12 months
merged_df['annual_budget_shortfall'] = (
    merged_df['food_insecure_population'] * merged_df['weekly_shortfall_per_person'] * WEEKS_IN_YEAR * MONTHS_OF_INSECURITY_FACTOR
).round(0).astype(int)

# Drop the intermediate weekly column if not needed
final_df = merged_df.drop(columns=['weekly_shortfall_per_person'])

# %%
# --- FINAL EXPORT STEP ---
# This saves your processed data to the 'final-output' folder in S3
output_path = "s3://food-equity-dashboard/final-output/final_cleaned_data.csv"

# index=False ensures we don't save the row numbers as a separate column
final_df.to_csv(output_path, index=False)

print(f"Success! File saved to {output_path}")




# %%



