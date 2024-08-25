import streamlit as st
import pandas as pd
import plotly.express as px

# Function to calculate max value in Baseline based on the Activity condition
def calculate_max(df):
    activities = ['00.01', '00.02', '00.03', '00.04']
    activity_mapping = {
        '00.01': 'Feasibility',
        '00.02': 'Design',
        '00.03': 'Execution',
        '00.04': 'Closure'
    }
    df['Activity'] = df['Activity'].map(activity_mapping)
    filtered_df = df[df['Activity'].isin(activity_mapping.values())]
    max_values = filtered_df.groupby('Project')['Baseline'].max().reset_index()
    max_values.rename(columns={'Baseline': 'Max Baseline (child)'}, inplace=True)
    merged_df = pd.merge(filtered_df, max_values, on='Project', how='left')
    selected_columns = [
        'Project', 'Project (child)', 'Project Status', 'Baseline', 'Max Baseline (child)',
        'Baseline Status', 'Activity', 'Activity (child)', 'Baseline Start Date', 'Baseline Finish Date'
    ]
    merged_df = merged_df[selected_columns]
    final_df = merged_df[merged_df['Baseline'] == merged_df['Max Baseline (child)']]
    return final_df

# Function to read and display fields from the new excel file and perform pivoting
def read_and_pivot_excel(file):
    required_columns = [
        'Project ID', 'Feasibility Start', 'Feasibility Finish', 
        'Design Start', 'Design Finish', 'Execution Start', 
        'Execution Finish', 'Closure Start', 'Closure Finish'
    ]
    df_new = pd.read_excel(file, sheet_name="Current AMP BL NominalFY25$", skiprows=3)
    if all(col in df_new.columns for col in required_columns):
        df_filtered = df_new[required_columns]
        df_pivot = pd.DataFrame()
        phases = ['Feasibility', 'Design', 'Execution', 'Closure']
        for phase in phases:
            temp_df = df_filtered[['Project ID', f'{phase} Start', f'{phase} Finish']].copy()
            temp_df.columns = ['Project ID', 'CLB Start Date', 'CLB Finish Date']
            temp_df['Activity'] = phase
            df_pivot = pd.concat([df_pivot, temp_df], ignore_index=True)
        return df_pivot
    else:
        return "The required columns are not present in the Excel sheet."

# Function to compare dates between first and second file based on Project ID and Activity
def compare_dates(first_df, second_df):
    merged_df = pd.merge(
        second_df,
        first_df,
        left_on=['Project ID', 'Activity'],
        right_on=['Project', 'Activity'],
        how='left'
    )
    
    # Calculate variance in dates
    merged_df['Start Date Variance (days)'] = (merged_df['CLB Start Date'] - merged_df['Baseline Start Date']).dt.days
    merged_df['Finish Date Variance (days)'] = (merged_df['CLB Finish Date'] - merged_df['Baseline Finish Date']).dt.days
    
    # Select relevant columns for display
    comparison_columns = [
        'Project ID', 'Activity', 'Baseline Start Date', 'CLB Start Date', 'Start Date Variance (days)', 
        'Baseline Finish Date', 'CLB Finish Date', 'Finish Date Variance (days)'
    ]
    final_df = merged_df[comparison_columns]
    
    # Rename the columns
    final_df.rename(columns={
        'Baseline Start Date': 'LN Baseline Start Date',
        'Baseline Finish Date': 'LN Baseline Finish Date',
        'CLB Start Date': 'CLB Start Date',
        'CLB Finish Date': 'CLB Finish Date'
    }, inplace=True)
    
    # Sort and reset index
    final_df.sort_values(by=['Project ID'], inplace=True)
    final_df = final_df.reset_index(drop=True)
    return final_df

# Function to filter and generate downloadable files for each case
def generate_case_files(df):
    # Filter data for each of the six cases
    ln_blank_clb_not_df = df[(df['LN Baseline Start Date'].isna()) & (df['LN Baseline Finish Date'].isna()) &
                             (df['CLB Start Date'].notna()) & (df['CLB Finish Date'].notna())]
    clb_blank_ln_not_df = df[(df['CLB Start Date'].isna()) & (df['CLB Finish Date'].isna()) &
                             (df['LN Baseline Start Date'].notna()) & (df['LN Baseline Finish Date'].notna())]
    ln_start_blank_clb_not_df = df[(df['LN Baseline Start Date'].isna()) & (df['CLB Start Date'].notna())]
    ln_finish_blank_clb_not_df = df[(df['LN Baseline Finish Date'].isna()) & (df['CLB Finish Date'].notna())]
    clb_start_blank_ln_not_df = df[(df['CLB Start Date'].isna()) & (df['LN Baseline Start Date'].notna())]
    clb_finish_blank_ln_not_df = df[(df['CLB Finish Date'].isna()) & (df['LN Baseline Finish Date'].notna())]

    # Return the filtered dataframes
    return ln_blank_clb_not_df, clb_blank_ln_not_df, ln_start_blank_clb_not_df, ln_finish_blank_clb_not_df, clb_start_blank_ln_not_df, clb_finish_blank_ln_not_df

# Function to create the combined bar chart for all six visuals with counts and percentages
def plot_combined_chart_with_counts(df):
    total_rows = len(df)

    # Calculate counts for each of the six cases
    ln_blank_clb_not = df[(df['LN Baseline Start Date'].isna()) & (df['LN Baseline Finish Date'].isna()) &
                          (df['CLB Start Date'].notna()) & (df['CLB Finish Date'].notna())].shape[0]
    clb_blank_ln_not = df[(df['CLB Start Date'].isna()) & (df['CLB Finish Date'].isna()) &
                          (df['LN Baseline Start Date'].notna()) & (df['LN Baseline Finish Date'].notna())].shape[0]
    ln_start_blank_clb_not = df[(df['LN Baseline Start Date'].isna()) & (df['CLB Start Date'].notna())].shape[0]
    ln_finish_blank_clb_not = df[(df['LN Baseline Finish Date'].isna()) & (df['CLB Finish Date'].notna())].shape[0]
    clb_start_blank_ln_not = df[(df['CLB Start Date'].isna()) & (df['LN Baseline Start Date'].notna())].shape[0]
    clb_finish_blank_ln_not = df[(df['CLB Finish Date'].isna()) & (df['LN Baseline Finish Date'].notna())].shape[0]

    # Prepare data for chart
    data = {
        'Visual Name': [
            'LN Start & Finish Blank, CLB Not Blank',
            'CLB Start & Finish Blank, LN Not Blank',
            'LN Start Blank, CLB Start Not Blank',
            'LN Finish Blank, CLB Finish Not Blank',
            'CLB Start Blank, LN Start Not Blank',
            'CLB Finish Blank, LN Finish Not Blank'
        ],
        'Count': [ln_blank_clb_not, clb_blank_ln_not, ln_start_blank_clb_not, 
                  ln_finish_blank_clb_not, clb_start_blank_ln_not, clb_finish_blank_ln_not],
        'Percentage': [(count / total_rows) * 100 if total_rows > 0 else 0 
                       for count in [ln_blank_clb_not, clb_blank_ln_not, ln_start_blank_clb_not, 
                                     ln_finish_blank_clb_not, clb_start_blank_ln_not, clb_finish_blank_ln_not]]
    }

    combined_df = pd.DataFrame(data)

    # Create the bar chart
    fig = px.bar(
        combined_df,
        x='Visual Name',
        y='Count',
        text='Count',
        title='Combined Visual: Counts and Percentages for Six Comparisons'
    )

    # Add percentage labels on top of the bars
    fig.update_traces(
        texttemplate='%{text} ( %{customdata[1]:.2f} %)',
        customdata=combined_df[['Count', 'Percentage']],
        textposition='outside',
        marker_color='#4CAF50'
    )

    # Update layout for a clean look
    fig.update_layout(
        title={
            'text': 'Counts and Percentages for Six Comparisons',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#FF5733'}
        },
        xaxis_title=None,
        yaxis_title="Count",
        xaxis_tickangle=-45,
        plot_bgcolor='white',
        height=600,
        margin=dict(t=100, b=150)
    )

    return fig

# Streamlit app
def main():
    # Ensure session state to track if comparison has been run
    if 'comparison_run' not in st.session_state:
        st.session_state.comparison_run = False

    st.markdown("""
        <style>
        .fixed-title {
            background-color: #4CAF50;
            padding: 10px;
            color: white;
            font-size: 24px;
            text-align: center;
            position: -webkit-sticky;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0px 2px 5px gray;
        }
        .styled-buttons {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 20px;
        }
        .styled-buttons button {
            background-color: #FF5733;
            color: white;
            border: none;
            padding: 10px;
            font-size: 16px;
            cursor: pointer;
        }
        .styled-buttons button:hover {
            background-color: #E74C3C;
        }
        </style>
        <div class="fixed-title">📊 LN VS CLB DATES COMPARISON APP</div>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='color: #FF5733;'>🗂️ First File: Max Baseline Calculation</h2>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload your first file for max baseline calculation", type=['csv', 'xlsx'])
    first_df = None
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            
            st.write("Data preview:")
            st.dataframe(df, height=300)
            
            required_columns = [
                'Project', 'Project (child)', 'Project Status', 'Baseline', 'Baseline Status',
                'Activity', 'Activity (child)', 'Baseline Start Date', 'Baseline Finish Date'
            ]
            if all(column in df.columns for column in required_columns):
                first_df = calculate_max(df)
                
                st.markdown("<h3 style='color: #009688;'>Filtered Data (Baseline = Max Baseline)</h3>", unsafe_allow_html=True)
                st.dataframe(first_df, height=300)
                
                csv = first_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name='filtered_data_max_equal_baseline.csv',
                    mime='text/csv',
                )
            else:
                st.error(f"The file must contain the following columns: {required_columns}")
        except Exception as e:
            st.error(f"Error processing the file: {e}")
    
    st.markdown("<h2 style='color: #FF5733;'>🗂️ Second File: Pivoting Project Phases and Comparison</h2>", unsafe_allow_html=True)
    
    new_uploaded_file = st.file_uploader("Upload your new Excel file to read specific fields and pivot", type=['xlsx'])
    second_df = None
    
    if new_uploaded_file is not None:
        try:
            second_df = read_and_pivot_excel(new_uploaded_file)
            
            if isinstance(second_df, pd.DataFrame):
                st.markdown("<h3 style='color: #009688;'>Pivoted Data with Activity, CLB Start Date, and CLB Finish Date</h3>", unsafe_allow_html=True)
                st.dataframe(second_df, height=300)
                
                csv = second_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download pivoted data as CSV",
                    data=csv,
                    file_name='pivoted_data.csv',
                    mime='text/csv',
                )
            else:
                st.error(second_df)
        except Exception as e:
            st.error(f"Error processing the file: {e}")
    
    # Check if comparison button has been clicked previously
    if st.session_state.comparison_run or first_df is not None and second_df is not None:
        st.markdown("<h2 style='color: #4CAF50;'>📅 LN VS CLB Comparison</h2>", unsafe_allow_html=True)
        
        compare = st.button("🔍 Run Comparison")
        
        if compare or st.session_state.comparison_run:
            try:
                comparison_df = compare_dates(first_df, second_df)
                
                st.markdown("<h3 style='color: #009688;'>Comparison of Dates (with variance)</h3>", unsafe_allow_html=True)
                st.dataframe(comparison_df, height=300)

                # Generate the combined visual for counts and percentages
                fig_combined = plot_combined_chart_with_counts(comparison_df)
                st.markdown("<h3 style='color: #FF5733;'>Combined Visual with Counts and Percentages</h3>", unsafe_allow_html=True)
                st.plotly_chart(fig_combined)

                # Generate downloadable files for each case
                ln_blank_clb_not_df, clb_blank_ln_not_df, ln_start_blank_clb_not_df, ln_finish_blank_clb_not_df, clb_start_blank_ln_not_df, clb_finish_blank_ln_not_df = generate_case_files(comparison_df)

                # Display beautiful download buttons for each case
                st.markdown("<h3 style='color: #FF5733;'>Download Filtered Data for Each Case</h3>", unsafe_allow_html=True)
                st.markdown('<div class="styled-buttons">', unsafe_allow_html=True)

                st.download_button(
                    label="Download LN Start & Finish Blank, CLB Not Blank",
                    data=ln_blank_clb_not_df.to_csv(index=False).encode('utf-8'),
                    file_name='ln_blank_clb_not_blank.csv',
                    mime='text/csv',
                )
                st.download_button(
                    label="Download CLB Start & Finish Blank, LN Not Blank",
                    data=clb_blank_ln_not_df.to_csv(index=False).encode('utf-8'),
                    file_name='clb_blank_ln_not_blank.csv',
                    mime='text/csv',
                )
                st.download_button(
                    label="Download LN Start Blank, CLB Start Not Blank",
                    data=ln_start_blank_clb_not_df.to_csv(index=False).encode('utf-8'),
                    file_name='ln_start_blank_clb_start_not_blank.csv',
                    mime='text/csv',
                )
                st.download_button(
                    label="Download LN Finish Blank, CLB Finish Not Blank",
                    data=ln_finish_blank_clb_not_df.to_csv(index=False).encode('utf-8'),
                    file_name='ln_finish_blank_clb_finish_not_blank.csv',
                    mime='text/csv',
                )
                st.download_button(
                    label="Download CLB Start Blank, LN Start Not Blank",
                    data=clb_start_blank_ln_not_df.to_csv(index=False).encode('utf-8'),
                    file_name='clb_start_blank_ln_start_not_blank.csv',
                    mime='text/csv',
                )
                st.download_button(
                    label="Download CLB Finish Blank, LN Finish Not Blank",
                    data=clb_finish_blank_ln_not_df.to_csv(index=False).encode('utf-8'),
                    file_name='clb_finish_blank_ln_finish_not_blank.csv',
                    mime='text/csv',
                )

                # Mark comparison as run
                st.session_state.comparison_run = True

            except Exception as e:
                st.error(f"Error during comparison: {e}")

if __name__ == '__main__':
    main()
