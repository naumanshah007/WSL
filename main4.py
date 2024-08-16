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
        how='left'  # Perform a left join
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
    
    # Rename the columns just before showing the comparison
    final_df.rename(columns={
        'Baseline Start Date': 'LN Baseline Start Date',
        'Baseline Finish Date': 'LN Baseline Finish Date',
        'CLB Start Date': 'CLB Start Date',
        'CLB Finish Date': 'CLB Finish Date'
    }, inplace=True)
    
    # Sort the final DataFrame by 'Project ID'
    final_df.sort_values(by=['Project ID'], inplace=True)
    final_df = final_df.reset_index(drop=True)
    return final_df

# Function to categorize severity
def categorize_severity(row):
    if row['Start Date Variance (days)'] > 365 or row['Finish Date Variance (days)'] > 365:
        return 'High Severity'
    elif (90 <= row['Start Date Variance (days)'] <= 365) or (90 <= row['Finish Date Variance (days)'] <= 365):
        return 'Medium Severity'
    elif (0 <= row['Start Date Variance (days)'] < 90) or (0 <= row['Finish Date Variance (days)'] < 90):
        return 'Low Severity'
    elif row['Start Date Variance (days)'] < 0 or row['Finish Date Variance (days)'] < 0:
        return 'Negative Variance'
    else:
        return 'No Variance'

# Function to create a pie chart for variance summary
def plot_variance_summary(df):
    total_rows = len(df)
    positive_variance = len(df[(df['Start Date Variance (days)'] > 0) | (df['Finish Date Variance (days)'] > 0)])
    negative_variance = len(df[(df['Start Date Variance (days)'] < 0) | (df['Finish Date Variance (days)'] < 0)])
    
    summary_data = {
        'Category': ['Total Records', 'Positive Variance', 'Negative Variance'],
        'Count': [total_rows, positive_variance, negative_variance]
    }

    summary_df = pd.DataFrame(summary_data)

    fig = px.pie(summary_df, values='Count', names='Category', title='Summary of Variance')

    fig.update_traces(textinfo='label+percent+value')
    fig.update_layout(height=600, width=800)

    return fig

# Function to create a pie chart for severity summary
def plot_summary_pie(df):
    severity_counts = df['Severity'].value_counts()
    summary_df = pd.DataFrame({'Severity': severity_counts.index, 'Count': severity_counts.values})
    
    fig = px.pie(summary_df, values='Count', names='Severity', title='Severity-Wise Summary')
    
    fig.update_traces(textinfo='label+percent+value')
    fig.update_layout(height=600, width=800)

    return fig

# Streamlit app
def main():
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
    
    # Comparison Button
    if first_df is not None and second_df is not None:
        st.markdown("<h2 style='color: #4CAF50;'>📅 LN VS CLB Comparison</h2>", unsafe_allow_html=True)
        
        compare = st.button("🔍 Run Comparison")
        
        if compare:
            try:
                comparison_df = compare_dates(first_df, second_df)
                
                st.markdown("<h3 style='color: #009688;'>Comparison of Dates (with variance)</h3>", unsafe_allow_html=True)
                st.dataframe(comparison_df, height=300)
                
                # Plot Summary Pie Chart for Variance (Total, Positive, Negative)
                st.markdown("<h3 style='color: #FF5733;'>Summary of Variance</h3>", unsafe_allow_html=True)
                fig_variance = plot_variance_summary(comparison_df)
                st.plotly_chart(fig_variance)

                # Categorize severity based on variance
                comparison_df['Severity'] = comparison_df.apply(categorize_severity, axis=1)

                # Display categorized data
                st.markdown("<h3 style='color: #FF5733;'>Categorized Data Based on Severity</h3>", unsafe_allow_html=True)
                st.dataframe(comparison_df, height=300)

                # Download button for the categorized dataframe
                csv_categorized = comparison_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download categorized data as CSV",
                    data=csv_categorized,
                    file_name='categorized_data.csv',
                    mime='text/csv',
                )

                # Severity explanation
                st.markdown("""
                    <h3 style='color: #FF5733;'>Severity Definitions</h3>
                    <ul>
                        <li><b>High Severity:</b> Variance greater than 365 days</li>
                        <li><b>Medium Severity:</b> Variance between 90 and 365 days</li>
                        <li><b>Low Severity:</b> Variance less than 90 days</li>
                        <li><b>Negative Variance:</b> Negative variance indicating early completion</li>
                        <li><b>No Variance:</b> No variance between planned and actual dates</li>
                    </ul>
                """, unsafe_allow_html=True)

                # Plot Summary Pie Chart for the Severity
                st.markdown("<h3 style='color: #FF5733;'>Severity Summary</h3>", unsafe_allow_html=True)
                fig_severity = plot_summary_pie(comparison_df)
                st.plotly_chart(fig_severity)
                
            except Exception as e:
                st.error(f"Error during comparison: {e}")

if __name__ == '__main__':
    main()
