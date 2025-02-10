import streamlit as st

from state_graph import graph
import pandas as pd


def get_user_inputs():

    """
    Displays a Streamlit interface to collect user inputs for financial performance analysis.

    Returns:
        tuple: A tuple containing the following elements:
            - task (str): The task description entered by the user.
            - competitors (list of str): A list of competitor names entered by the user.
            - max_revisions (int): The maximum number of revisions specified by the user.
            - uploaded_file (UploadedFile or None): The uploaded CSV file containing the company's financial data, or None if no file was uploaded.
    """
    st.set_page_config(page_title="Financial Agent")
    st.title("Financial Performance Analyzer")
    st.write("This tool helps you analyze the financial performance of your company compared to competitors.")

    task = st.text_input(
        "Enter the task:",
        "Analyze the financial performance of your company (Nvidia) compared to competitors",
        help="Describe the task you want to perform."
    )
    competitors = st.text_area(
        "Enter competitor names (one per line):",
        help="List the names of competitors, one per line."
    ).split("\n")
    max_revisions = st.number_input(
        "Max Revisions",
        min_value=1,
        value=2,
        help="Specify the maximum number of revisions to consider."
    )
    uploaded_file = st.file_uploader(
        "Upload a CSV file with the company's financial data",
        type=["csv"],
        help="Upload the CSV file containing the financial data of your company. The file should include columns for Year, Revenue, Cost of Goods Sold, Operating Expenses, and Net."
    )
    with open("./data/sample_financials.csv", "rb") as file:
        st.download_button(
            label="Download Sample CSV",
            data=file,
            file_name="sample_financials.csv",
            mime="text/csv",
            key="download_button",
            help="Download a sample financials CSV file to see the expected format."
        )
    return task, competitors, max_revisions, uploaded_file


def process_file(uploaded_file):
    """
    Processes the uploaded file by reading its content and decoding it to a UTF-8 string.

    Args:
        uploaded_file: The uploaded file object. It should have a `getvalue` method that returns the file content.

    Returns:
        str: The content of the uploaded file as a UTF-8 decoded string if the file is not None.
        None: If the uploaded file is None.
    """
    if uploaded_file is not None:
        return uploaded_file.getvalue().decode("utf-8")
    return None


def analyze_performance(task, competitors, csv_data, max_revisions):
    """
    Analyzes the performance of a given task against competitors using CSV data.

    Args:
        task (str): The task to be analyzed.
        competitors (list): A list of competitors to compare against.
        csv_data (str): The path to the CSV file containing performance data.
        max_revisions (int): The maximum number of revisions to consider.

    Returns:
        dict: The final state after processing the performance data.
    """
    initial_state = {
        "task": task,
        "competitors": [comp.strip() for comp in competitors],
        "csv_file": csv_data,
        "max_revisions": max_revisions,
        "revision_number": 1,
    }
    thread = {"configurable": {"thread_id": "1"}}
    final_state = None
    for s in graph.stream(initial_state, thread):
        st.write(s)
        final_state = s
    return final_state


def display_final_report(final_state):
    """
    Display the final report using Streamlit.

    Parameters:
    final_state (dict): A dictionary containing the final state of the application. 
                        It should have a key "report" with the report content to display.

    Returns:
    None
    """
    if final_state and "report" in final_state:
        st.subheader("Final Report")
        st.write(final_state["report"])


def main():
    task, competitors, max_revisions, uploaded_file = get_user_inputs()
    csv_data = process_file(uploaded_file)

    if csv_data:
        if st.button("Start Analysis", key="start_analysis_button", help="Click to start the analysis", use_container_width=True):
            final_state = analyze_performance(task, competitors, csv_data, max_revisions)
            display_final_report(final_state)

if __name__ == "__main__":
    main()
