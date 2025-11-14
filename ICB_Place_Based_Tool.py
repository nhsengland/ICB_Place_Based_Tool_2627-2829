# -------------------------------------------------------------------------
# Copyright (c) 2021 NHS England and NHS Improvement. All rights reserved.
# Licensed under the MIT License and the Open Government License v3. See
# license.txt in the project root for license information.
# -------------------------------------------------------------------------

"""
FILE:           ICB_Place_Based_Tool.py
DESCRIPTION:    Streamlit weighted capitation tool
CONTRIBUTORS:   Craig Shenton, Jonathan Pearson, Mattia Ficarelli, Samuel Leat, Jennifer Struthers
CONTACT:        england.revenue-allocations@nhs.net
CREATED:        2021-12-14
LAST UPDATED:   2025-10-27
VERSION:        3.0.1
"""
# Note that the above updated date refers only to the code for the tool, not source data

# Libraries
# -------------------------------------------------------------------------
# python
import json
import time
import base64
import io
import zipfile
import regex as re
from datetime import datetime
import os
from pathlib import Path

# local
import utils

# 3rd party:
import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import folium
import toml
import requests


# Page setup
# -------------------------------------------------------------------------
#Config file defined
config = toml.load('config.toml')

#Configure page's default Streamlit settings
st.set_page_config(
    page_title="ICB Place Based Allocation Tool",
    page_icon="https://www.england.nhs.uk/wp-content/themes/nhsengland/static/img/favicon.ico",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.england.nhs.uk/allocations/",
        "Report a bug": "https://github.com/nhsengland/AIF_Allocation_Tool",
        "About": "This tool is designed to support allocation at places by allowing places to be defined by aggregating GP Practices within an ICB. Please refer to the User Guide for instructions. For more information on the latest allocations, including contact details, please refer to: [https://www.england.nhs.uk/allocations/](https://www.england.nhs.uk/allocations/)",
    },
)
padding = 1
st.markdown(
    f""" <style>
    .reportview-container .main .block-container{{
        padding-top: {padding}rem;
    }} </style> """,
    unsafe_allow_html=True,
)


# Set default place in session
# -------------------------------------------------------------------------
if len(st.session_state) < 1:
    st.session_state["Default Place"] = {
        "gps": [
            "B85005: SHEPLEY PRIMARY CARE LIMITED",
            "B85022: HONLEY SURGERY",
            "B85061: SKELMANTHORPE FAMILY DOCTORS",
            "B85026: KIRKBURTON HEALTH CENTRE",
        ],
        "icb": "NHS West Yorkshire ICB"
    }
if "places" not in st.session_state:
    st.session_state.places = ["Default Place"]


# Functions & Calls
# -------------------------------------------------------------------------
# Render an svg image
def render_svg(svg):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
    st.write(html, unsafe_allow_html=True)

# Download functionality
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

# Create metric_calcs function
# Fetches the specified metric from the given dataframe, and rounds it using "excel_round", giving the place_metric output used in the tool
# When called below:
## "group_need_indices" are the df created by the "get_data_for_all_years" function
## "metric_index" the name of the column to be retrieved from the df
def metric_calcs(group_need_indices, metric_index):
    # Convert the value to float and round it using excel_round to 2 decimal places
    place_metric = utils.excel_round(group_need_indices[metric_index][0].astype(float), 0.01)
    return place_metric

# Create aggregations dictionary, used in get_data_for_all_years function; tells function how to aggregate each column
aggregations = {
    "GP pop": "sum",
    "Weighted G&A pop": "sum",
    "Weighted Community pop": "sum",
    "Weighted Mental Health pop": "sum",
    "Weighted Maternity pop": "sum",
    "Weighted Prescribing pop": "sum",
    "Overall Weighted pop": "sum",
    "Weighted Primary Care": "sum",
    "Weighted Primary Medical Care Need": "sum",
    "Weighted Health Inequalities pop": "sum",
}

#Create index_numerator list, used in get_data_for_all_years function; see utils file for full info
index_numerator = [
    "Weighted G&A pop",
    "Weighted Community pop",
    "Weighted Mental Health pop",
    "Weighted Maternity pop",
    "Weighted Prescribing pop",
    "Overall Weighted pop",
    "Weighted Primary Care",
    "Weighted Primary Medical Care Need",
    "Weighted Health Inequalities pop",
]

#Create index_names list, used in get_data_for_all_years function; see utils file for full info
index_names = [
    "G&A Index",
    "Community Index",
    "Mental Health Index",
    "Maternity Index",
    "Prescribing Index",
    "Overall Core Index",
    "Primary Medical Care Index",
    "Primary Medical Care Need Index",
    "Health Inequalities Index",  
]

# Uses the get_latest_commit_date function from utils to fetch the most recent commit date based on details from the config file and stores it in last_commit_date for use on page
last_commit_date = utils.get_latest_commit_date(config['owner'], config['repo'], config['branch'])

# Uses the get_latest_folder_update to find the last update to the data folder, based on details from the config file, and stores it in last_folder_update for use on page
last_folder_update = utils.get_latest_folder_update(config['owner'], config['repo'], config['folder_path'], config['branch'])


# Header section
# -------------------------------------------------------------------------
# Render the NHS logo from SVG data
svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 16">
            <path d="M0 0h40v16H0z" fill="#005EB8"></path>
            <path d="M3.9 1.5h4.4l2.6 9h.1l1.8-9h3.3l-2.8 13H9l-2.7-9h-.1l-1.8 9H1.1M17.3 1.5h3.6l-1 4.9h4L25 1.5h3.5l-2.7 13h-3.5l1.1-5.6h-4.1l-1.2 5.6h-3.4M37.7 4.4c-.7-.3-1.6-.6-2.9-.6-1.4 0-2.5.2-2.5 1.3 0 1.8 5.1 1.2 5.1 5.1 0 3.6-3.3 4.5-6.4 4.5-1.3 0-2.9-.3-4-.7l.8-2.7c.7.4 2.1.7 3.2.7s2.8-.2 2.8-1.5c0-2.1-5.1-1.3-5.1-5 0-3.4 2.9-4.4 5.8-4.4 1.6 0 3.1.2 4 .6" fill="white"></path>
          </svg>
"""
render_svg(svg)

# Page title, calling the defined year from the config file
st.title("ICB Place Based Allocation Tool " + config['allocations_year'])

# Message about pending 28/29 data
st.markdown("**<h3>Year 3 (2028/29) data to follow in due course.</h3>**", unsafe_allow_html=True)

# Draft status message
st.markdown("**<h3 style='color: red;'>This tool is currently under development.</h3>**", unsafe_allow_html=True)

# Writes date of last update to source data
st.write(f"""Data last updated: {last_folder_update}""")


# SIDEBAR Prologue
## This section of the sidebar code has to remain at this location in the tool code as it needs to be run before the data is imported.
# -------------------------------------------------------------------------
# Call the function to set sidebar width
utils.set_sidebar_width(min_width=500, max_width=500)

# Creates a list containing the filenames of files in the data folder
datasets = os.listdir('data/')

# Creates dropdown box for time-period selection and stores relevant filename with ".csv" removed in "selected_year"
selected_dataset = st.sidebar.selectbox("Time Period:", options = datasets, help="Select a time period", format_func=lambda x : x.replace('.csv','').replace('_','/'))
selected_year = selected_dataset.replace('.csv', '')

# Creates a horizontal separator, dividing the time-period selector from the Create New Place section of the sidebar
st.sidebar.write("-" * 34)


# Import Data
# -------------------------------------------------------------------------
# Creates empty dataset_dict dictionary used in next step of code
dataset_dict = {}

# Iterates through each dataset(year) in the data folder importing the data using the get_data function from utils.
# Imported data is stored in the library created above, as a dataframe for each year
for dataset in datasets:
    year = dataset.replace('.csv', '')
    dataset_dict[year] = utils.get_data('data/' + dataset)

# Uses get_sidebar function to store a list of ICBs from the dataframe for the selected time-period; see utils doc for more info on get_sidebar
icb = utils.get_sidebar(dataset_dict[selected_year])


# SIDEBAR Main
# -------------------------------------------------------------------------
# Sidebar subheader
st.sidebar.subheader("Create New Place")

# Place creation drop-down menus
# Creates expander box containing ICB selection
with st.sidebar.expander("Select an ICB", expanded=True):
    
    # Creates drop-down box with list of ICBs based on icb value created above
    icb_choice = st.selectbox("Select an ICB from the drop-down", icb, help="Select an ICB", label_visibility="hidden")

    # Generate the list of LADs by filtering the dataset for the selected time period based on the ICB selected above
    lad = dataset_dict[selected_year]["LA District name"].loc[
        dataset_dict[selected_year]["ICB name"] == icb_choice
    ].unique().tolist()

    # Create a DataFrame from the list of LADs
    lad_list_to_select = pd.DataFrame(lad, columns=['Local Authority District'])
    # Add a tick column to LAD dataframe
    lad_list_to_select['tick'] = False

    # Creates an expander box containing LAD selection
    with st.sidebar.expander('Select Local Authority District(s)', expanded=False):
        # Creates an interactive data editor to allow users to select LADs, using lad_list_to_select as an input
        lad_choice = st.data_editor(
            lad_list_to_select,
            # Creates a tickbox interface in the tool which updates the tick column
            column_config={
                "tick": st.column_config.CheckboxColumn("Select", default=False)
            },
            hide_index=True
        )
        # Outputs from above LAD tick-list saved to selected_lads list
        selected_lads = lad_choice[lad_choice['tick']]["Local Authority District"].tolist()

    # Filter practices based on selected ICB and LADs
    # Checks whether the selected_lads variable contains data to determine whether to filter on LAD and ICB, or just ICB
    # Outputs the practice_display field to filtered_practices variable as a list
    if not selected_lads:
        filtered_practices = dataset_dict[selected_year]["practice_display"].loc[
            dataset_dict[selected_year]["ICB name"] == icb_choice
        ].unique().tolist()
    else:
        filtered_practices = dataset_dict[selected_year]["practice_display"].loc[
            (dataset_dict[selected_year]["LA District name"].isin(selected_lads)) &
            (dataset_dict[selected_year]["ICB name"] == icb_choice)
        ].unique().tolist()

    # Creates a dataframe from the filtered_practices list
    practice_list_to_select = pd.DataFrame(filtered_practices, columns=['GP Practice'])
    # Adds a tick column to list of GP practices
    practice_list_to_select['tick'] = False

    # Creates an expander box to contain GP selection
    with st.sidebar.expander("Select GP Practice(s)", expanded=False):
        # Create three columns for the buttons; last column blank to maintain suitable width
        col1, col2, col3 = st.columns([1.1, 1.3, 2.2])

        with col1:
            # Creates a button labelled "Select all"
            if st.button("Select all"):
                # Sets the tick column of practice_list_to_select to True
                practice_list_to_select['tick'] = True
                # Stores the updated pratice selection in session_state.practice_list
                st.session_state.practice_list = practice_list_to_select.copy()

        with col2:
            # Creates a button labelled "Deselect all"
            if st.button("Deselect all"):
                # Sets the tick column of practice_list_to_select to False
                practice_list_to_select['tick'] = False
                # Stores the updated practice selection in session_state.practice_list
                st.session_state.practice_list = practice_list_to_select.copy()

        # Sets practice_list, last_icb_choice, and last_selected_lads to match practice_list_to_select, icb_choice, and selected_lads created above if any of them do not currently exist or match those values
        if 'practice_list' not in st.session_state or st.session_state.get('last_icb_choice') != icb_choice or st.session_state.get('last_selected_lads') != selected_lads:
            st.session_state.practice_list = practice_list_to_select.copy()
            st.session_state['last_icb_choice'] = icb_choice
            st.session_state['last_selected_lads'] = selected_lads

        # Creates interactive practice choice table using practice_list from the session state as an input, saved as the practice_choice dataframe
        practice_choice = st.data_editor(
            st.session_state.practice_list,
            # Creates a tickbox column which updates the tick column in the practice_list
            column_config={
                "tick": st.column_config.CheckboxColumn("Select", default=False)
            },
            hide_index=True
        )

    # Creates a list of "GP Practice" values by filtering the practice_choice dataframe created above for ticked records
    selected_practices = practice_choice[practice_choice['tick']]["GP Practice"].tolist()

# Creates a text input box for the user to name their place, storing the input text under place_name
place_name = st.sidebar.text_input(
    "Name your Place",
    "",
    # Text below is displayed if the user interacts with the ? help icon
    help="Give your defined place a name to identify it",
)

# Code below saves the selected place to the session state when save place is clicked
# Creates a sidebar button labelled "Save Place"
if st.sidebar.button("Save Place", help="Save place to session data"):
    # Checks whether no practices are selected or if the user has used the name "Default Place" and then prints a relevant error
    if selected_practices == [] or place_name == "Default Place":
        if selected_practices == []:
            st.sidebar.error("Please select one or more GP practices")
        if place_name == "Default Place":
            st.sidebar.error("Please rename your place to something other than 'Default Place'")
    # Checks whether the user has entered a place_name and print an error if not
    if place_name == "":
        st.sidebar.error("Please give your place a name")
    # If not the below code executes to save the place to session state
    else:
        # This code checks again that there are practices selected and the place_name isn't "Default Place" and stops running if so
        if selected_practices == [] or place_name == "Default Place":
            print("")
        # If not then below executes to save the place to session state
        else:
            # Checks whether the Default Place is the only place in the session state
            if (
                len(st.session_state.places) <= 1
                and st.session_state.places[0] == "Default Place"
            ):
                # If Default Place is found in session state it is deleted
                del [st.session_state["Default Place"]]
                del [st.session_state.places[0]]
                # Checks whether the place_name is in session state
                if [place_name] not in st.session_state:
                    # If place_name is not found it's added to the session state along with associated practices and ICB
                    st.session_state[place_name] = {
                        "gps": selected_practices,
                        "icb": icb_choice
                    }
                # Checks whether places list exists in the session state
                if "places" not in st.session_state:
                    # If not found it creates the places list and adds the place_name
                    st.session_state.places = [place_name]
                # Checks whether place_name is in places list in session state
                if place_name not in st.session_state.places:
                    # If place_name not in places list it is added to the end
                    st.session_state.places = st.session_state.places + [place_name]
            # If Default Place is not in the session state then the below runs
            else:
                # Checks whether the place_name is in session state
                if [place_name] not in st.session_state:
                    # If place_name is not found it's added to the session as a dictionary state along with associated practices and ICB
                    st.session_state[place_name] = {
                        "gps": selected_practices,
                        "icb": icb_choice
                    }
                # Checks whether places list exists in the session state
                if "places" not in st.session_state:
                    # If not found it creates the places list and adds the place_name
                    st.session_state.places = [place_name]
                # Checks whether place_name is in places list in session state
                if place_name not in st.session_state.places:
                    # If place_name not in places list it is added to the end
                    st.session_state.places = st.session_state.places + [place_name]

# Horizontal separator for the sidebar
st.sidebar.write("-" * 34)

# Creates a dictionary (session_state_dict) where each place from the places list is added with an empty list
session_state_dict = dict.fromkeys(st.session_state.places, [])

# Each place in the session_state_dict is updated with the gps and icb selection saved for it in session state
for key, value in session_state_dict.items():
    session_state_dict[key] = st.session_state[key]
# Adds a new key to the session_state_dict named places and adds the list of places from session_state as the associated value
session_state_dict["places"] = st.session_state.places

# Dumps the contents of the session_state_dict into a json string named session_state_dump used to download session data
session_state_dump = json.dumps(session_state_dict, indent=4, sort_keys=False)

# Create the Advanced Options tick-box in the sidebar which toggles the download and upload features on and off
advanced_options = st.sidebar.checkbox("Advanced Options")
if advanced_options:
    # Creates a button which downloads the session_state_dump json string as a json file
    st.sidebar.download_button(
        label="Download session data as JSON",
        data=session_state_dump,
        file_name="session.json",
        mime="text/json",
    )
    # Creates a form in the sidebar with key "my-form" (a container that groups multiple input widgets to be submitted together)
    form = st.sidebar.form(key="my-form")
    # Adds a file-uploader to the form restricted to json files, stored under group_file
    group_file = form.file_uploader(
        "Upload previous session data as JSON", type=["json"]
    )
    # Adds a submit button to the form
    submit = form.form_submit_button("Submit")
    # Following code processes form submissions
    if submit:
        # Checks whether file was uploaded
        if group_file is not None:
            # Stores loaded file under variable "d"
            d = json.load(group_file)
            # Overwrites the list of places in session_state with the list from the uploaded file
            st.session_state.places = d["places"]
            # Stores the individual place data in the session_state from the uploaded file
            for place in d["places"]:
                st.session_state[place] = d[place]
            # Displays a progress bar increasing 1% per 0.01 seconds
            my_bar = st.sidebar.progress(0)
            for percent_complete in range(100):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1)
            my_bar.empty()

# Creates a tickbox to toggle the display of session data (used later in the main body)
see_session_data = st.sidebar.checkbox("Show Session Data")


# BODY
# -------------------------------------------------------------------------
# Sets select_index to be the length of the list of places -1, which is the index of the last item in the list (due to Python indexing)
select_index = len(st.session_state.places) - 1  # find n-1 index
# Creates an empty placeholder
placeholder = st.empty()
# Creates a drop-down menu to let users choose from items in the places list in session_state, defaulting to the last-created place identified above
# selectbox has unique key "before"
option = placeholder.selectbox(
    "Select Place", (st.session_state.places), index=select_index, key="before"
)


# DELETE PLACE
# -------------------------------------------------------------------------
# Code note: The use of before and after in the code above and below avoids issues like selectboxes trying to show deleted places, etc... Before is essentially the place selected before the deletion, and after is the place selected after
# Checks whether after exists in the session_state, and if not sets it to the value of before from session_state
if "after" not in st.session_state:
    st.session_state.after = st.session_state.before
# Creates a "Delete Current Selection" button; sets delete_place to true when clicked
label = "Delete Current Selection"
delete_place = st.button(label, help=label)
# Creates an empty placeholder for the delete progress bar
my_bar_delete = st.empty()
# Code below runs if button is clicked
if delete_place:
    # Confirms there is only one place in the list (i.e. the default place needs to be reinstated)
    if len(st.session_state.places) <= 1:
        del [st.session_state[st.session_state.after]]
        if "Default Group" not in st.session_state:
            st.session_state["Default Place"] = {
                "gps": [
                    "B85005: SHEPLEY PRIMARY CARE LIMITED",
                    "B85022: HONLEY SURGERY",
                    "B85061: SKELMANTHORPE FAMILY DOCTORS",
                    "B85026: KIRKBURTON HEALTH CENTRE",
                ],
                "icb": "NHS West Yorkshire ICB"
            }
        if "places" not in st.session_state:
            st.session_state.places = ["Default Place"]
        else:
            st.session_state["Default Place"] = {
                "gps": [
                    "B85005: SHEPLEY PRIMARY CARE LIMITED",
                    "B85022: HONLEY SURGERY",
                    "B85061: SKELMANTHORPE FAMILY DOCTORS",
                    "B85026: KIRKBURTON HEALTH CENTRE",
                ],
                "icb": "NHS West Yorkshire ICB"
            }
        st.session_state.places = ["Default Place"]
        st.session_state.after = "Default Place"
        st.warning(
            "All places deleted. 'Default Place' reset to default. Please create a new place."
        )
        my_bar_delete.progress(0)
        for percent_complete in range(100):
            time.sleep(0.01)
            my_bar_delete.progress(percent_complete + 1)
        my_bar_delete.empty()
    # If there is more than once place in the list then the below executes
    else:
        # Deletes from the session_state the currently selected place (stored in session_state.after)
        del [st.session_state[st.session_state.after]]
        # Deletes the currently selected place from the list of places (stores in session_state.after)
        del [
            st.session_state.places[
                st.session_state.places.index(st.session_state.after)
            ]
        ]
        # Displays a progress bar, increasing 1% every 0.01 seconds
        my_bar_delete.progress(0)
        for percent_complete in range(100):
            time.sleep(0.01)
            my_bar_delete.progress(percent_complete + 1)
        my_bar_delete.empty()

# Recreates the drop-down menu selectbox to reflect the updated list
# Sets select_index to be the length of the list of places -1, which is the index of the last item in the list (due to Python indexing)
select_index = len(st.session_state.places) - 1
# Creates the places drop-down menu, defaulting to the last-created place identified above
# selectbox has unique key "after"
option = placeholder.selectbox(
    "Select Place", (st.session_state.places), index=select_index, key="after"
)
# icb_name populated from the place selected in the drop-down menu
icb_name = st.session_state[st.session_state.after]["icb"]
# group_gp_list, used to generate the map, populated from the place selected in the drop-down menu
group_gp_list = st.session_state[st.session_state.after]["gps"]


# MAP
# -------------------------------------------------------------------------
# Initialises the map
map = folium.Map(location=[52, 0], zoom_start=10, tiles="openstreetmap")
# Initialises the list of latitudes
lat = []
# Initialises the list of longitudes
long = []

# Populates the map with the coordinates of the practices in the group_gp_list created above
# Cycles through each gp practice in the list, performing the below
for gp in group_gp_list:
    # Uses the escape function to avoid special characters in gp names breaking code
    escaped_gp = re.escape(gp)
    # If the practice name isn't found in the list of practice names in the dataset an error is printed and the loop moves to the next practice
    if ~dataset_dict[selected_year]["practice_display"].str.contains(escaped_gp).any():
        st.write(f"{gp} is not available in this time period")
        continue
    # Retrieves the practice's latitude and longitude from the values in the dataset
    latitude = dataset_dict[selected_year]["Latitude"].loc[dataset_dict[selected_year]["practice_display"] == gp].item()
    longitude = dataset_dict[selected_year]["Longitude"].loc[dataset_dict[selected_year]["practice_display"] == gp].item()
    # Append the retrieved longitude and latitude to the lists
    lat.append(latitude)
    long.append(longitude)
    # Adds a marker to the map with a popup label matching the gp entry in the group_gp_list
    folium.Marker(
        [latitude, longitude],
        popup=str(gp),
        icon=folium.Icon(color="darkblue", icon="fa-user-md", prefix="fa"),
    ).add_to(map)

# If the latitude list is empty, print an error message to say there are no practices from the place available
if not lat:
    st.write("No GP Practices in this Place are available in this time period")
    st.stop()

# bounds method https://stackoverflow.com/a/58185815
# Sets the bounds of the map; ensures all markers are visible with a margin added to the latitude
map.fit_bounds(
    [[min(lat) - 0.02, min(long)], [max(lat) + 0.02, max(long)]]
)

# Renders the map in Streamlit
folium_static(map, width=700, height=300)

# Creates info boxes showing the relevant year and practices displayed
# Cleans the list of group_gp_list practices, removing colons, single quotes, and square brackets
list_of_gps = re.sub(
    "\w+:",
    "",
    str(group_gp_list).replace("'", "").replace("[", "").replace("]", ""),
)
# Displays the selected_year defined above in a string for user info
st.info(f"This information pertains to the **{selected_year.replace("_","/")}** time period")
# Displays the selected practices from list_of_gps in a string for user info
st.info("**Selected GP Practices:**" + list_of_gps)

# The below query strings are used in the get_data_for_all_years function to filter the dataset to the selected place and ICB before aggregating
# Prepares a query string to filter the practice_display field by value in place_state (see utils)
gp_query = "practice_display == @place_state"
# Prepares a query string to filter the "ICB name" field by the value in icb_state (see utils)
# Escape column names with backticks https://stackoverflow.com/a/56157729
icb_query = "`ICB name` == @icb_state"


# Metrics
# -------------------------------------------------------------------------
# Aggregates data and calculates indices for all places and ICBs in session_state, stored in a library
data_all_years = utils.get_data_for_all_years(dataset_dict, st.session_state, aggregations, index_numerator, index_names, gp_query, icb_query)
# Filters the data_all_years dataframe to only records for the selected year and where the "Place / ICB" matches to the selection from the drop-down menu
df = data_all_years[selected_year].loc[data_all_years[selected_year]["Place / ICB"] == st.session_state.after]
# Resets the index of the data frame to account for records filtered out above records
df = df.reset_index(drop=True)

# Creates lists for the metric columns and metric names
# columns and names lists must be in the same order to be fetched correctly below
# Split into two groups to enable multiple rows layout in tool
metric_cols = [
    "G&A Index",
    "Community Index",
    "Mental Health Index",
    "Maternity Index",
]

metric_names = [
    "Gen & Acute",
    "Community*",
    "Mental Health",
    "Maternity",
]

metric_cols2 = [
    "Prescribing Index",
    "Primary Medical Care Need Index",
    "Health Inequalities Index",
]

metric_names2 = [
    "Prescribing",
    "Primary Medical in Core**",
    "Health Inequals",
]

# Uses metric_calcs to retrieve the "Overall Core Index" and formats it to 2dp
place_metric = metric_calcs(df, "Overall Core Index")
place_metric = "{:.2f}".format(place_metric)
# Prints the "Overall Core Index" along with label as a header
st.header("Core Index: " + str(place_metric))

# Creates expander box to contain the core sub-indices
with st.expander("Core Sub Indices", expanded  = True):

    # Creates a number of columns equal to the length of the metric_cols list
    cols = st.columns(len(metric_cols))
    # Loops through each pairing in metric_cols and metric_names
    for metric, name in zip(metric_cols, metric_names):
        # Uses metric_calcs to fetch the value for the index from metric_cols from the df, stored in place_metric
        place_metric = metric_calcs(
            df,
            metric,
        )
        # Formats place_metric to 2dp
        place_metric = "{:.2f}".format(place_metric)
        # Finds the column number relating to the location of the metric in the "metric_cols" list.
        # Uses the metric method to display the data, with the name from "metric_names" as the label and the index fetched above as the value.
        cols[metric_cols.index(metric)].metric(
            name,
            place_metric
        )

    # Repeats the process above using the "metric_cols2" and "metric_names2" lists, to produce the 2nd row of data.
    cols = st.columns(len(metric_cols2)+1)
    for metric, name in zip(metric_cols2, metric_names2):
        place_metric = metric_calcs(
            df,
            metric,
        )
        place_metric = "{:.2f}".format(place_metric)
        cols[metric_cols2.index(metric)].metric(
            name,
            place_metric
        )

# Drop-down text box with supporting notes
with st.expander("Relative Weighting of Components"):
    st.markdown(
        """The relative weighting applied to each of these components are provided in Workbook J.  These weightings are based on modelled estimated expenditure in 2028/29.
        \n\nThese relative weightings are based on national modelled expenditure, and do not take into consideration variation of weights at the local level.  It is not appropriate to apply these weights to place-level indices that are relative to the ICB, not England.
        """)

# As with core indexes above, lists of indexes and names to be displayed
metric_cols = [
    "Primary Medical Care Need Index",
    "Health Inequalities Index",
]

metric_names = [
    "Primary Medical Care Need****",
    "Health Inequals",
]

# Uses metric_calcs to retrieve the "Primary Medical Care Index" and formats it to 2dp
place_metric = metric_calcs(df, "Primary Medical Care Index")
place_metric = "{:.2f}".format(place_metric)
# Prints the "Primary Medical Care Index" along with label as a header, and a supporting note
st.header("Primary Medical Care Index: " + str(place_metric))
st.caption("Based on weighted populations from the formula for ICB allocations, not the global sum weighted populations***")

# Expander box to contain primary care sub-indices.
with st.expander("Primary Medical Care Sub Indices", expanded  = True):

    # Loops through the index and names lists, as with the core sub-indices above.
    cols = st.columns(3)
    for metric, name in zip(metric_cols, metric_names):
        place_metric = metric_calcs(
            df,
            metric,
        )
        place_metric = "{:.2f}".format(place_metric)
        cols[metric_cols.index(metric)].metric(
            name,
            place_metric
        )


# Downloads
# -------------------------------------------------------------------------
# Gets the current date and time and stores it as a string formatted YYYY-MM-DD
current_date = datetime.now().strftime("%Y-%m-%d")

st.subheader("Download Data")

# Creates a checkbox labelled "Preview data download", which is ticked by default
print_table = st.checkbox("Preview data download", value=True)
# If the print_table checkbox is ticked, uses the write_table function to display the data loaded using the "get_data_for_all_years" function, filtered for the currently selected year
if print_table:
    with st.container():
        utils.write_table(data_all_years[selected_year])

# Content that is added to the first four lines of the downloaded Excel file.
csv_header1 = f"""PLEASE READ: Below you can find the results for the places you created, and for the ICB they belong to, for the year you selected. This data was last updated: {last_folder_update}"""
csv_header2 = "Note that the need indices for the places are relative to the ICB (where the ICBs need index = 1.00), while the need index for the ICB is relative to national need (where the national need index = 1.00)."
csv_header3 = "This means that the need indices of the individual places cannot be compared to the need index of the ICB. For more information, see the FAQ tab available in the tool."
csv_header4 = ""

# Create a BytesIO buffer to store the Excel file while it's being populated
excel_buffer = io.BytesIO()

# Writes to the excel_buffer file
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    
    # Loops through each key/value pair in the data_all_years dictionary
    for year, df in data_all_years.items():
        # Sets the name for each tab in the workbook, appending the year to the end (32 characters max)
        worksheet_name = f"Allocations for {year}"
        # Adds a worksheet with the set name, replacing "/" with "_"
        worksheet = writer.book.add_worksheet(worksheet_name.replace("/", "_"))
        # Uses the write_headers function to add the headers to the sheet and return the correct row to load the data from, start_row
        start_row = utils.write_headers(worksheet, csv_header1, csv_header2, csv_header3, csv_header4)
        # Uses write_row from xlsxwriter to write the column names from the df at the start_row
        worksheet.write_row(start_row, 0, df.columns)
        # 
        for r, row in enumerate(df.values, start=start_row+1):
            worksheet.write_row(r,0,row)
    # Save the Excel file
    writer.close()

# Move the pointer of the buffer to the beginning (by default sits at the end of the data written to the buffer)
excel_buffer.seek(0)

# Open the text documentation file
with open("docs/ICB allocation tool documentation.txt", "rb") as fh:
    readme_text = io.BytesIO(fh.read())

# Create JSON dump of the session state (example)
session_state_dict = dict.fromkeys(st.session_state.places, [])
for key, value in session_state_dict.items():
    session_state_dict[key] = st.session_state[key]
session_state_dict["places"] = st.session_state.places
session_state_dump = json.dumps(session_state_dict, indent=4, sort_keys=False)

# Create a ZIP file containing the Excel file, documentation, and configuration
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
    zip_file.writestr(f"ICB allocation calculations.xlsx", excel_buffer.getvalue())
    zip_file.writestr("ICB allocation tool documentation.txt", readme_text.getvalue())
    zip_file.writestr("ICB allocation tool configuration file.json", session_state_dump)

# Ensure the ZIP file buffer's pointer is at the start
zip_buffer.seek(0)

# Streamlit download button
btn = st.download_button(
    label="Download ZIP",
    data=zip_buffer.getvalue(),
    file_name=f"ICB allocation tool {current_date}.zip",
    mime="application/zip",
)

# Expander box with notes text
with st.expander("Notes", expanded = True):
    st.markdown(
        "*The Community Services index relates to the half of Community Services that are similarly distributed to district nursing. The published Community Services target allocation is calculated using the Community Services model. This covers 50% of Community Services. The other 50% is distributed through the General & Acute model."
    )
    st.markdown("")
    st.markdown(
        "**The Primary Medical Care in Core element covers Other primary care services (not relating to pharmaceutical, ophthalmic, and dental services), NHS 111, and out of hours services."
        )
    st.markdown("")
    st.markdown(
        "***The global sum weighted populations are calculated using the Carr-Hill formula. The global sum weighted populations are a key component of payments to GP practices under the GMS contract. Funding GP practices is part of ICB’s commissioning responsibilities."
        )
    st.markdown("")
    st.markdown(
        "****The Primary Medical Care Need Indices will not include the dispensing doctors adjustment – this is applied at ICB level."
        )

with st.expander("About the ICB Place Based Tool", expanded = True):
    st.markdown(
        "This tool is designed to support allocation at places by allowing places to be defined by aggregating GP Practices within an ICB. Please refer to the User Guide for instructions."
    )
    st.markdown("The tool estimates the relative need for places within the ICB.")
    st.markdown(
        "The Relative Need Index for ICB (i) and Defined Place (p) is given by the formula:"
    )
    st.latex(r""" (WP_p/GP_p)\over (WP_i/GP_i)""")
    st.markdown(
        "Where *WP* is the weighted population for a given need and *GP* is the GP practice population."
    )
    st.markdown(
        f"This tool is based on estimated need for 2023/24 and 2024/25 by utilising weighted populations projected from the November 2021 to October 2022 GP Registered practice populations."
    )
    st.markdown(
        "More information on the latest allocations, including contact details, can be found [here](https://www.england.nhs.uk/allocations/)."
    )

# Footer with info on Allocations inbox and update date for app
st.info(f"""App last updated: {last_commit_date}
        \nFor support with using the AIF Allocation tool please email: [england.revenue-allocations@nhs.net](mailto:england.revenue-allocations@nhs.net)"""
)

# Displays session data if see_session_data is TRUE
# Show Session Data
# -------------------------------------------------------------------------
if see_session_data:
    st.subheader("Session Data")
    st.session_state