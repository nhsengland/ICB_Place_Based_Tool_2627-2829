# Libraries
# -------------------------------------------------------------------------
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
import os
import requests
from datetime import datetime
import toml

#Config file defined
config = toml.load('config.toml')


# Load data and cache
# Uses the Streamlit cache decorator to cache this operation so the data doesn't have to be read in everytime script is re-run
@st.cache_data()
# Defines the get_data function
def get_data(path):
    """
    Loads data from a csv at the provided location and stores it in a dataframe.
    Specified columns are renamed as below and nulls are replaced with zeroes.
    Prints 'cache miss' to the terminal before loading, to identify that this function is actually running, vs just pulling from cache.
    
    Parameters:
    path: The location of the CSV to be loaded.
    
    Returns:
    df: The data frame containing the CSV data, with columns renamed
    """
    print('cache miss')
    # Creates a dataframe using the csv found at the location the function is called on
    df = pd.read_csv(path)
    # Renames the columns as below
    df = df.rename(
        columns={
            "Practice_Code": "GP Practice code",
            "GP_Practice_Name": "GP Practice name",
            "Practice_Postcode": "GP Practice postcode",
            "ICB": "ICB code",
            "ICBname": "ICB name",
            "RCode": "Region code",
            "Region": "Region name",
            "LAD": "LA District code",
            "LADname": "LA District name",
            "Registered Patients": "GP pop",
            "G&A WP": "Weighted G&A pop",
            "CS WP": "Weighted Community pop",
            "MH WP": "Weighted Mental Health pop",
            "Mat WP": "Weighted Maternity pop",
            "Health Ineq WP": "Weighted Health Inequalities pop",
            "Prescr WP": "Weighted Prescribing pop",
            "Core WP": "Overall Weighted pop",
            "Primary Medical Care WP": "Weighted Primary Medical Care Need",
            "Final PMC WP": "Weighted Primary Care",
        }
    )
    # Replaces any NA values with zeroes
    df = df.fillna(0)
    # Creates a 'practice_display' column by combining the practice code and name into a single field.
    df["practice_display"] = df["GP Practice code"] + ": " + df["GP Practice name"]
    return df


# Sidebar dropdown list
@st.cache_data
def get_sidebar(data):
    icb = data["ICB name"].unique().tolist()
    icb.sort()
    return icb


# Function to render a table with AgGrid options
def write_table(data):
    """
    Renders a table with the first column frozen and no bottom-bar.

    Parameters:
    data: The dataframe to be displayed in a table.

    Returns:
    AgGrid: The information from the dataframe plus the selected AgGrid options.
    """
    # Create grid options to pin the first column
    gb = GridOptionsBuilder.from_dataframe(data)
    # Freeze the first column (index 0)
    gb.configure_column(list(data.columns)[0], pinned='left')
    # Build the gridOptions dictionary
    gridOptions = gb.build()
    # Display the table with AgGrid
    return AgGrid(data, gridOptions=gridOptions)


def write_headers(sheet, *csv_headers):
    """
    Function takes an unlimited amount of headers and writes them to the top of an excel sheet

    Parameters:
    sheet (str): name of the sheet
    *csv_headers (str): individual strings with the header information

    Returns:
    The integer number of the row where the data should be placed (leaving a space after the headers)
    """
    # Loop through the csv_headers and write each header to the sheet
    for index, header in enumerate(csv_headers):
        sheet.write(index, 0, header)
    
    header_row_count = len(csv_headers)
    
    return header_row_count + 1  # Return the starting row for data


# Creates the aggregate function
def aggregate(df, name, on, aggregations):
    """
    Function aggregates a data frame.  How the data is grouped and which aggregations are performed depends on given inputs.
    Also checks that the df includes the specified "on" column and, if not, creates it, populating it with the name value, before aggregating.
    Used exclusively in the get_data_all_years function.  When called there, the inputs are as below.
    
    Parameters:
    df: The pre-filtered (using a query string) data from the dataset_dict, containing only a single place or ICB before aggregation.
    name: The place taken from the session_state.places list, used to populate the "on" field, if it's not already in the data.
    on: Either the string "Place Name" or "ICB name", telling the function what to group on.  Both variations are called in the get_data_all_years function to create aggregations at both place-level and ICB-level.
    aggregations: The library of column names and the aggregation functions to be performed on them, defined in the ICB_Place_Based_Tool.py file

    Returns:
    df: The same df as initially loaded
    df_group: The aggregated and grouped df
    """
    if on not in df.columns:
        df.insert(loc=0, column=on, value=name)

    df_group = df.groupby(on).agg(aggregations)

    return df, df_group


# Creates a function to calculate the index of weighted populations.
def get_index(place_indices, icb_indices, index_names, index_numerator):
    """
    Calculates the index of weighted populations.
    Intended to take the df_group output from the aggregate function and divide it by the GP population, for ICB and place.
    The place index is then divided by the icb index to create a relative number.
    The overall index is created by final_wp divided by [GP pop].
    
    Parameters:
    place_indices: A df with place-level data
    icb_indices: A df with ICB-level data
    index_names: List of the indexes to be created.  Defined in ICB_Place_Based_Tool.py
    index_numerator: List of column names that contain the numerator values for the index calculation.  Defined in ICB_Place_Based_Tool.py

    Returns:
    place_indices: Input place_indices df with new index_names column
    icb_indices: Input icb_indices df with new index_names column
    """
    # Creates a new column in icb_indices called "index_names", containing [index_numerator] / [GP pop]
    icb_indices[index_names] = icb_indices[index_numerator].div(
        icb_indices["GP pop"].values, axis=0
    )
    # Creates a new column in place_indices called "index_names", containing ([index_numerator] / [GP pop]) / ICB index
    place_indices[index_names] = (
        place_indices[index_numerator]
        .div(place_indices["GP pop"].values, axis=0)
        .div(icb_indices[index_names].values, axis=0)
    )
    return place_indices, icb_indices


def get_data_for_all_years(dataset_dict, session_state, aggregations, index_numerator, index_names, gp_query, icb_query):
    """
    Processes and aggregates data for all datasets across multiple years.

    This function iterates over all datasets in the given `dataset_dict`, aggregates data for each place
    and Integrated Care Board (ICB) specified in the `session_state`, and calculates indices based on the 
    provided aggregation functions and queries. The aggregated and indexed data is then stored back in 
    the `dataset_dict` for each dataset.

    Parameters:
    ----------
    dataset_dict : dict
        A dictionary where the keys are filenames and the values are corresponding datasets (DataFrames). When called in the tool this is the imported data with a dataframe for each year.
        
    session_state : object
        An object that contains the session state, including a list of places and corresponding 
        geographical and ICB information for each place.
        
    aggregations : dict
        A dictionary specifying the aggregation functions to apply to the data. The keys are column names
        and the values are aggregation functions (e.g., 'sum', 'mean').

    index_numerator : str
        The column name to use as the numerator for index calculations.

    index_names : list
        A list of column names to use as the denominator for index calculations.

    gp_query : str
        A query string to filter the data for place-level aggregations.

    icb_query : str
        A query string to filter the data for ICB-level aggregations.

    Returns:
    -------
    dict
        The updated `dataset_dict` where each dataset (DataFrame) has been aggregated, indexed, and rounded 
        to three decimal places. Each dataset is a DataFrame with data aggregated at the ICB and place level.

    """

    # Loop through all datasets
    # This has potential to take time but I think with the size of data it's neglible.
    for filename, data in dataset_dict.items():
        # dict to store all dfs sorted by ICB
        dict_obj = {}
        df_list = []

        #FOR EACH PLACE in the SESSION STATE aggregate the data at the ICB and Place level, calculate indices 
        #adds them to a dictionary object
        for place in session_state.places:
            place_state = session_state[place]["gps"]
            icb_state = session_state[place]["icb"]

            # get place aggregations
            df = data.query(gp_query)
            place_data, place_groupby = aggregate(
                df, place, "Place Name", aggregations
            )

            # get ICB aggregations
            df = data.query(icb_query)
            icb_data, icb_groupby = aggregate(
                df, icb_state, "ICB name", aggregations
            )

            # index calcs
            place_indices, icb_indices = get_index(
                place_groupby, icb_groupby, index_names, index_numerator
            )

            icb_indices.insert(loc=0, column="Place / ICB", value=icb_state)
            place_indices.insert(loc=0, column="Place / ICB", value=place)

            if icb_state not in dict_obj:
                dict_obj[icb_state] = [icb_indices, place_indices]
            else:
                dict_obj[icb_state].append(place_indices)

        # add dict values to list
        for obj in dict_obj:
            df_list.append(dict_obj[obj])

        # flatten list for concatenation
        flat_list = [item for sublist in df_list for item in sublist]
        large_df = pd.concat(flat_list, ignore_index=True)

        # Rounding the data here, after calculations are done to maintain accuracy - numerators and indices are rounded differently
        large_df[index_numerator + ["GP pop"]] = large_df[index_numerator + ["GP pop"]].map(lambda x: excel_round(x, 1))
        large_df[index_names] = large_df[index_names].map(lambda x: excel_round(x, 0.001))

        dataset_dict[filename] = large_df

    return dataset_dict



def excel_round(number, precision=0.01) -> float:
    """
    Rounds a number to a specified precision using the "round half up" method, similar to Excel.

    Parameters:
    number (float/int): The number to be rounded.
    precision (float/int): The precision to round to (e.g., 0.1, 0.01, 100, etc.).

    Returns:
    float: The rounded number, or the original value if it's not numeric.
    """
    try:
        if isinstance(number, (int, float)):  # Ensure the number is numeric
            if precision > 1:  # For rounding to nearest ten, hundreds, etc.
                rounded_num = round(number / precision) * precision
            else:  # For decimal precision
                number = Decimal(str(number))
                precision = Decimal(str(precision))
                rounded_num = number.quantize(precision, rounding=ROUND_HALF_UP)
            return float(rounded_num)
        else:
            return number  # Return the value unchanged if it's not numeric
    except (ValueError, InvalidOperation):
        return number  # Return the value unchanged if there's an error during conversion

# Helper function to inject CSS for sidebar width
def set_sidebar_width(min_width=300, max_width=300):
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] {{
            min-width: {min_width}px;
            max-width: {max_width}px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

#Fetch latest date of commit to main GitHub repo main branch and format it for display in tool
def get_latest_commit_date(owner, repo, branch):
    """
    Uses the requests library to pull the latest commit date for the repo from GitHub API.

    Parameters:
    owner (string): The username of the owner of the repo
    repo (string): The repo to fetch the latest commit date from
    branch (string): The branch to fetch the latest commit date from

    Note: In the tool, the parameters are populated from the config file, to make future updates easier.

    Returns:
    formatted_date (string): The date of the last commit to the specified repo and branch in the format "DD month YYYY"
    """
    # Constructs the GitHub API URL to find commits
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    # Adds query parameters for the branch and limits it to 1 return (the most recent)
    params = {
        "sha": branch,
        "per_page": 1
    }
    response = requests.get(url, params=params)
    # Checks if the API call was successful (200 = OK)
    if response.status_code == 200:
        # Parses the API response from JSON
        commits = response.json()
        # Confirms the response is not empty
        if commits:
            try:
                # Extracts the commit date string
                date_str = commits[0]["commit"]["committer"]["date"]
                # Converts to Python datetime
                date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                # Formats to DD Month YYYY
                formatted_date = date_obj.strftime("%d %B %Y")
                return formatted_date
            # If the returned response doesn't meet the above parameters prints an error message
            except Exception as e:
                return f"Error parsing date {e}"
        # If the API response is empty, prints an error
        else:
            return "No commits found."
    # If the API call fails prints the error code
    else:
        return config['data_update']
    
#Fetch latest date of commit to main GitHub repo main branch and format it for display in tool
def get_latest_folder_update(owner, repo, folder_path, branch):
    """
    Uses the requests library to pull the latest update date for a specific folder in the repo from GitHub API.

    Parameters:
    owner (string): The username of the owner of the repo
    repo (string): The repo to fetch the latest commit date from
    folder path (string): The folder path to check for changes
    branch (string): The branch to fetch the latest commit date from

    Note: In the tool, the parameters are populated from the config file, to make future updates easier.

    Returns:
    formatted_date (string): The date of the last update to the specified folder, repo, and branch in the format "DD month YYYY"
    """
    # Constructs the GitHub API URL to find commits
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    # Adds query parameters for the folder path and branch and limits it to 1 return (the most recent)
    params = {
        "path": folder_path,
        "sha": branch,
        "per_page": 1
    }
    # Sends the request to GitHub using above details
    response = requests.get(url, params=params)
    # Checks if the API call was successful (200 = OK)
    if response.status_code == 200:
        try:
            # Parses the response from json
            commit_data = response.json()[0]
            # Extracts the commit date string
            date_str = commit_data["commit"]["committer"]["date"]
            # Converts to Python datetime
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            # Formats to DD Month YYYY
            formatted_date = date_obj.strftime("%d %B %Y")
            return formatted_date
        # If the returned response doesn't meet the above parameters prints an error message
        except Exception as e:
            return f"Error parsing date: {e}"
    # If the API call fails prints the error code
    else:
        return config['app_update']