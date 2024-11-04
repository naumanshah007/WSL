import streamlit as st
import pandas as pd
import re
from module1 import extract_lab_values
from module2 import prepare_database_ready_answers

# Streamlit setup for clinical trial data filtering and processing
st.set_page_config(page_title="Clinical Trials Data Processor", layout="wide")

# Display the image at the top of the page
st.image("1.png", use_column_width=True)

# Title directly below the image
st.title("Clinical Trials Data Processor - Labs")

# Load the clinical trials data file directly
@st.cache_data
def load_data():
    return pd.read_pickle("clinical_trials_data_filtered.pkl")

# Function to parse JSON-like output into structured DataFrame with modified column names for units
def parse_output(output_data, column_name="LAB_VALUES", is_database_ready=False):
    parsed_data = []
    for entry in output_data:
        nct_id = entry.get("NCTId")
        values_str = entry.get(column_name, "")
        parsed_entry = {"NCTId": nct_id}

        # Define base units for specific lab values
        base_units = {
            "Absolute neutrophil count (ANC) or absolute granulocyte count required": "x10^9/L",
            "Hemoglobin required": "g/L",
            "Platelet count required": "x10^9/L",
            "Creatinine clearance or GFR required": "ml/min",
            "Bilirubin required": "xULN"
        }

        # Regular expression to match "Lab Name required": ["relationship", "value"]
        matches = re.findall(r'"([^"]+ required)": \["([^"]*)", "([^"]*)"\]', values_str)
        for match in matches:
            lab_name = match[0]
            relationship = match[1]
            value = match[2]

            # If processing database-ready answers, modify column name to include unit
            if is_database_ready and lab_name in base_units:
                lab_name = f"{lab_name} ({base_units[lab_name]})"
            parsed_entry[lab_name] = f"{relationship} {value}".strip()
        
        # Alternative pattern to capture range values
        alt_matches = re.findall(r'"([^"]+ required)": \[([0-9.]+), ([0-9.]+)\]', values_str)
        for alt_match in alt_matches:
            lab_name = alt_match[0]
            lower_limit = alt_match[1]
            upper_limit = alt_match[2]

            # If processing database-ready answers, modify column name to include unit
            if is_database_ready and lab_name in base_units:
                lab_name = f"{lab_name} ({base_units[lab_name]})"
            parsed_entry[lab_name] = f"[{lower_limit}, {upper_limit}]"
        
        parsed_data.append(parsed_entry)
    
    return pd.DataFrame(parsed_data)

# Load the data automatically
try:
    df_all = load_data()
except FileNotFoundError:
    st.error("Data file not found. Please ensure 'clinical_trials_data_filtered.pkl' is in the project directory.")

# Initialize session state for filtered data and outputs if not already done
if 'df_filtered' not in st.session_state:
    st.session_state.df_filtered = pd.DataFrame()
if 'lab_values_output' not in st.session_state:
    st.session_state.lab_values_output = None
if 'db_ready_output' not in st.session_state:
    st.session_state.db_ready_output = None

# Process the data if loaded successfully
if 'df_all' in locals():
    # Function to flatten list columns if necessary
    def flatten_list_columns(df):
        for column in df.columns:
            if df[column].apply(lambda x: isinstance(x, list)).any():
                df[column] = df[column].apply(lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x)
        return df

    df_all = flatten_list_columns(df_all)
    df_all.columns = ['NCTId', 'Conditions', 'Keywords', 'BriefTitle', 'EligibilityCriteria']
    df_all['concatenated_text'] = df_all.apply(lambda row: "\n".join([str(cell) for cell in row]), axis=1)
    
    # Sidebar filter inputs
    st.sidebar.header("Filter Records by any of following Keywords/ Fields")
    nct_id = st.sidebar.text_input("Enter NCTId")
    conditions = st.sidebar.text_input("Enter Condition Keywords")
    brief_title = st.sidebar.text_input("Enter Brief Title Keywords")
    eligibility_criteria = st.sidebar.text_input("Enter Eligibility Criteria Keywords")
    
    if st.sidebar.button("Filter Records"):
        # Apply filters and store results in session state
        mask = (
            df_all['NCTId'].str.contains(nct_id, case=False) & 
            df_all['Conditions'].str.contains(conditions, case=False) &
            df_all['BriefTitle'].str.contains(brief_title, case=False) &
            df_all['EligibilityCriteria'].str.contains(eligibility_criteria, case=False)
        )
        st.session_state.df_filtered = df_all[mask]
        st.write("Filtered Records:")
        st.dataframe(st.session_state.df_filtered)
    
    # Display processing options if filtered data is available
    if not st.session_state.df_filtered.empty:
        st.subheader("Process Selected IDs")
        selected_ids = st.multiselect("Select NCTId(s) to Process", st.session_state.df_filtered['NCTId'].tolist())
        
        if st.button("Extract Lab Values"):
            selected_data = st.session_state.df_filtered[st.session_state.df_filtered['NCTId'].isin(selected_ids)]
            st.session_state.lab_values_output = extract_lab_values(selected_data)
            st.success("Lab Values Extraction Complete")
            
            # Display original JSON output
            st.write("Extracted Lab Values (JSON):")
            st.json(st.session_state.lab_values_output)
            
            # Parse and display extracted lab values in table format
            if st.session_state.lab_values_output:
                lab_values_df = parse_output(st.session_state.lab_values_output, column_name="LAB_VALUES")
                st.write("Extracted Lab Values in Table Format:")
                st.table(lab_values_df)
        
        if st.session_state.lab_values_output is not None:
            if st.button("Prepare Database Ready Answers"):
                st.session_state.db_ready_output = prepare_database_ready_answers(st.session_state.lab_values_output)
                st.success("Database Ready Answers Prepared")
                
                # Display original JSON output
                st.write("Database Ready Answers (JSON):")
                st.json(st.session_state.db_ready_output)
                
                # Parse and display database-ready answers in table format with unit in column name
                if st.session_state.db_ready_output:
                    db_ready_df = parse_output(st.session_state.db_ready_output, column_name="DatabaseReadyLabValues", is_database_ready=True)
                    st.write("Final Database Ready Answers in Table Format:")
                    st.table(db_ready_df)
