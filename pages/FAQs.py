import streamlit as st
import base64
from pathlib import Path
import time
import toml
import utils

config = toml.load('config.toml')

st.set_page_config(
    page_title="ICB Place Based Allocation Tool FAQs",
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

def render_svg(svg):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
    st.write(html, unsafe_allow_html=True)

# Markdown
# -------------------------------------------------------------------------
# NHS Logo
svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 16">
            <path d="M0 0h40v16H0z" fill="#005EB8"></path>
            <path d="M3.9 1.5h4.4l2.6 9h.1l1.8-9h3.3l-2.8 13H9l-2.7-9h-.1l-1.8 9H1.1M17.3 1.5h3.6l-1 4.9h4L25 1.5h3.5l-2.7 13h-3.5l1.1-5.6h-4.1l-1.2 5.6h-3.4M37.7 4.4c-.7-.3-1.6-.6-2.9-.6-1.4 0-2.5.2-2.5 1.3 0 1.8 5.1 1.2 5.1 5.1 0 3.6-3.3 4.5-6.4 4.5-1.3 0-2.9-.3-4-.7l.8-2.7c.7.4 2.1.7 3.2.7s2.8-.2 2.8-1.5c0-2.1-5.1-1.3-5.1-5 0-3.4 2.9-4.4 5.8-4.4 1.6 0 3.1.2 4 .6" fill="white"></path>
          </svg>
"""
render_svg(svg)

st.title("ICB Place Based Allocation Tool " + config['allocations_year'] + " FAQs")

#Code below uses the date of last modification for the file to create a last updated date.
script_path = Path(__file__)
last_modified_time = script_path.stat().st_mtime
last_modified_date = time.localtime(last_modified_time)
formatted_date = time.strftime('%d %B %Y', last_modified_date)
st.write(f"Last updated: {formatted_date}")

with st.expander("What does the tool do?"):
    st.markdown("""
        This tool was built to provide insight into smaller area (place) level variation underlying Integrated Care Boards (ICBs) resource allocation. The
        intention of the tool is to provide insights that may help inform ICB-level allocations and contribute to evidence-based resource decisions.
        \n\nThe tool presents <b>weighted populations</b> and <b>need indices</b> calculated by the <b>allocation model</b> for each of its <b>service components</b>, 
        by user-created <b>place</b>
        \n\n<b>Weighted populations</b> are GP practice populations (projected forward) multiplied by the need weight for a specific service as produced by the allocation 
        model.
        \n\n<b>Need indices</b> are standardised figures, which makes them more suited for comparison between areas. Need indices are calculated as follows:
    """, unsafe_allow_html=True)
    st.latex(r""" (WP_p/GP_p)\over (WP_i/GP_i)""")
    st.markdown("""
        Where <i>WP</i> is the weighted population for a given need, <i>GP</i> is the GP practice population, <i>i</i> is the ICB, and <i>p</i> is the Defined Place.
        \n\nThe need indices for these places are relative to their ICB, meaning that a value of 1.00 for a component in a defined place equals the level of need of 
        the ICB as a whole. If a place has a need index with a value below 1.00, it has a lower level of need compared to the ICB. A value above 1.00 means there is 
        a higher need in that place compared to the ICB.
        \n\nThe resource allocation model is based on anonymised NHS person-level data on their individual and area demographics, and use of NHS health services. With 
        exception of health inequalities<sup>1</sup>, this historic need together with population projections is then used to predict need for specific healthcare services 
        (different components) at the GP practice level. More information on the method can be find in the Technical Guide and Methodological papers on 
        https://www.england.nhs.uk/allocations/
        \n\nThese <b>service components</b> are as follows:
    """, unsafe_allow_html=True)
    st.markdown("""
        - Core Services:
            - General and Acute
            - Community services
            - Mental health services
            - Maternity
            - Prescribing
            - Primary Medical Care in Core Services
        - Primary Medical Care:
            - Primary Medicare Care need
        - Cross-cutting components:
            - Health inequalities
    """)
    st.markdown("""
        <b>Places</b> are user-defined areas that are created by selecting GP practices and assigning them to a place. 
    """, unsafe_allow_html=True)
    st.caption("""
        (1)The measure used to calculate the health inequalities need index is Avoidable mortality. This avoidable mortality need index is used to implement 
        the Health inequalities and unmet need adjustment, but we use Health inequalities, or HI, as a shorthand. Avoidable mortality only includes deaths 
        that could have been avoided through public health measures and timely and effective health care intervention. Furthermore, the definition of the 
        measure of avoidable mortality used here generally includes these avoidable deaths for people aged under 75, except for some specific causes of death 
        where it includes deaths of people of all ages, where these causes are deemed to be avoidable at all ages.
    """)
    
with st.expander("How do I create a place?"):
    st.markdown("""
        Input is required on the left-hand side of the tool to create a place. The default place that is shown when first accessing the app is for illustration only. 
        It will not be included in downloaded results (see <i>How do I download my saved places data?</i> below). If you do want to keep this place in the download, 
        please rename it.
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.image("images/PBTFAQ1.png", caption="Figure 1: A screenshot of the left-hand menu of the Place Based Tool showing the drop-downs and inputs used to create a place."
            #, width=292
            #, width=300
        )

    with col2:
        st.markdown("""
            **1a)** We regularly update the tool with the latest weighted populations and need indices. Sometimes, this data covers a single year. In this case, step 1a does not 
            apply. When it covers more than one year, select here which year you would like the tool to show by selecting this in the dropdown indicated in page element 1a.
            \n\n**1b)** Select the ICB of interest. You can select only one ICB at a time. This will filter the options available to you in the two drop-down menus below 
            (Local Authority District(s) and Select GP Practice(s)).
            \n\n**1c)** If you want to select GP practices from one or more specific Local Authority District(s), select these in this dropdown. You can select multiple Local 
            Authority Districts at once.
            \n\n**1d)** You can select all GP practices for the ICB and Local Authority Districts (if selected) selected under the above steps by ticking “Select all” under this step.
            Alternatively, select the specific GP practices you want to include in your defined place by ticking the boxes next to the practice name.            
        """, unsafe_allow_html=True)
    
    st.markdown("""
        The dropdown under this filter will only show GP practices that are both in the ICBs and Local Authority Districts you selected from the previous drop-down menus. For 
        example, it will not include GP practices that are in a selected Local Authority but are not part of the selected ICB.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.image("images/PBTFAQ1.2.png", caption="Figure 1.2: A screenshot showing the drop-down menu to select GP practices and highlighting the Search and Fullscreen buttons."
            #, width=345
        )

    with col2:
        st.markdown("""
            To search for a specific GP practice, hold your mouse cursor over the list and select the Search (magnifying glass) button that appears above the list.
            \n\nSelecting the Fullscreen icon will expand the list of practices to allow for easier scrolling and selection.
        """, unsafe_allow_html=True)
    
    st.markdown("""
        **1e)** Give your place a name by typing the name into the text box.
        \n\n**1f)** Clicking the “Save Place” button will then add each selected GP practice to the place you named and displayed visually on the dashboard.
        \n\nPlease note that:
    """)
    
    st.markdown("""
        - If you want to make changes to a place you already defined you can add more GP practices in 1d and press “Save Place” again to update.
        - Once you have saved a place, you can then create a new place in the same way. You will not overwrite the place you created previously as long as you have saved 
        it under a new name.
        - If you want to delete a place and start again, please refer to the second step under *How do I view my saved places?* below.
        - You can select the same GP practice to be in different places (e.g. if you create place A and B, both can include GP practice X).
    """)
    st.markdown("""
        **Warning:** Refreshing the web page will reset all your inputs including your saved places. Only refresh the page if you do not want to keep your saved places. Alternatively, download your work first (under Step 3 of *How do I download my saved places data?* below) which will download a save file for the tool from which you can return to your saved places.
    """)

with st.expander("How do I view my saved places?"):
    st.markdown("""
        To view the places you created and their relative need indices, some user input is required in the main body of the tool, on the right-hand side. This functionality allows you to check the places you created, change them, and view their relative need indices.
        \n\nPlease note that the section of the tool shown in Figure 3 below will only display data for the selected place (see step 2a below) and for the year selected in the sidebar (step 1a above).  If the version of the tool you are using contains multiple years of data, you can switch between them for the selected place by changing the year selected in the sidebar.
    """)
    st.image("images/PBTFAQ2.png", caption="Figure 2: A screenshot showing the main area of the Place Based Tool and identifying the various components of the page.", width=533)
    st.markdown("""
        **2a)** Once you have created a new place, the place name will become available in the main page dropdown menu. If you create multiple places, you can switch between them here. The place you select in this dropdown is the active place, and while it is active (i.e. you have it selected) the page elements 2b, 2c, 2d, and 2e will all refer to the active place.
        \n\n**2b)** If you want to remove the active place completely, click the button “Delete current selection”. If you delete all of your saved places, the app will return to the default place shown in Figure 1.
        \n\n**2c)** The map feature provides a helpful check on the geography and relative locations of the selected GP practices. This is useful to check that you included those GP practices in your defined place that you intended.
        \n\n**2d)** This box identifies the time period for the data being displayed.
        \n\n**2e)** This box lists the GP practices that make up the active year and place you selected in steps 1a and 3a. This information is here to also help you check whether you have the desired GP practices in your defined place.
        \n\n**2f)** The dashboard provides the relative need indices for the active year and place you selected under steps 1a and 3a. These are the combined need indices for the GP practices that make up the active place selected.
    """)
    
with st.expander("How do I download my saved places data?"):
    st.markdown("""
        You can download the results for the places you created. This requires some user input in the main body of the tool, on the right-hand side.
    """)
    st.image("images/PBTFAQ3.png", caption="Figure 3: A screenshot of the Download Data and preview sections of the Place Based Tool.")
    st.markdown("""
        **3a)** Scroll down below the “Relative Need Index” to “Download Data”. Here you can preview the data download by ensuring the box “Preview data download” is ticked (this is ticked by default).
        \n\n**3b)** This section provides a preview of the data download. It includes the GP practices populations, weighted populations and need indices for all components, for the created places. It also includes this data for the ICB in which the places are located.
        \n\n***Please Note:** The ICB need indices are not comparable with the need indices of the created places. The former is relative to national need, while the place need indices are relative to ICB need.*
        \n\n**3c)** To download the data, click “Download ZIP”. A date-stamped ZIP file will then be downloaded into your default download folder and contains the following items:
    """)
    st.markdown("""
        - 'ICB allocation calculations.csv': The data you previewed under step 3b in a Comma Separated Value (.csv) file which can be opened as a table in Microsoft Excel.  If there are multiple years of data available in the tool, this download file will include each year in a separate tab.
        - 'ICB allocation tool configuration file.json': A JavaScript Object Notation (JSON) file which can be used to re-upload your saved places into the tool at another time and return to the session you just downloaded. This is useful if you have defined many different places and want to come back to these places without having to redefine them. More information on this can be found in *How do I save and return to my session?*, below.
        - 'ICB allocation tool documentation.txt': A plain text file with reference information on the AIF Place Based Tool, including a link to NHS England’s GitHub<sup>1</sup> repository from which the tool runs on the Streamlit<sup>2</sup> app. The GitHub repository provides further technical information on the tool.
    """, unsafe_allow_html=True)
    st.caption("""
        (1) For more information on GitHub, please refer to https://github.com/security
        \n\n(2) For more information on how Streamlit works, including information about security, please refer to https://docs.streamlit.io/streamlit-cloud/trust-and-security
    """)

with st.expander("How do I save and return to my session?"):
    st.markdown("""
        To be able to return to your session you will need the .json file described under step 3c of the “How do I download my saved places data?” section above. Alternatively, you are also able to download the .json file without downloading the full .zip, as detailed in step 4b below.
        \n\nYou can return to a previous session for which you downloaded result using the .json file in the .zip you downloaded, as follows:
    """)
    col1, col2 = st.columns(2)

    with col1:
        st.image("images/PBTFAQ4.png", caption="Figure 4: A screenshot showing the advanced options and session data download options in the Place Based Tool's sidebar.")

    with col2:
        st.markdown("""
            **4a)** On the left-hand side of the tool, below the “Save Place” button, tick “Advanced Options”.
            \n\n**4b)** The new menu that appears and has a button called “Download session data as JSON”. Click this to download just the .json save file to return to later, if you don’t want to download the full .zip file.
            \n\n**4c)** From the menu that appears, click “Browse files” and use the new window to find the file location of the .json file from a previous session that you would like to reload in the tool. Alternatively, simply drag and drop the .json save file where the tool indicates “Drag and drop file here”.
            """)
    
    st.markdown("""
            Click “Submit” to reload the session. You should now see the saved places in the selection box at the top of the page. You can now add or delete any of your saved places if you wish.
            \n\n**4d)** You can also see the current session data (that will be downloaded in step 4b by clicking the “Show Session Data” button under the Advanced Options. This session data will then be printed out at the bottom of the main page as long as this check box is ticked.
            """)

with st.expander("How do I interpret the weighted populations and need indices in the csv I downloaded?"):
    st.markdown("""
        The csv includes weighted populations and need indices for all the places you created, as well as weighted populations and need indices for the ICBs those places are in. The ICB or ICBs you created places for will be in the top rows in the csv, and the places will be below that.
        \n\nWeighted populations are calculated by taking the size of the GP practice registered population (for a GP practice, place, or ICB), and then adjusting this population based on computed need for health care services related to age and sex. More information on the models computing the need for health care services can be found on our website: https://www.england.nhs.uk/allocations/
        \n\nNeed indices are standardised figures that may be easier to use as weighted populations can look very different due to differences in population size. A figure lower than 1.00 means the place has a lower need compared to the ICB average, while a figure greater than 1.00 means the place has a higher need compared to the ICB average.
    """)

with st.expander("Why does the GP practice level need index in the Place-based tool differ from those in the Annexes on https://www.england.nhs.uk/allocations/ ?"):
    st.markdown("""
        While both the Place-based tool and the Annexes on our NHS England website use the same GP practice-level weighted population, the calculation of need indices is different. As a result, the need indices can differ. The difference has to do with the population the index is standardised to. For the Place-based tool, this is the ICB population. For the Annexes, this is the total GP practice registered population in England.
        \n\nThe calculation of a need index for a given service element for a GP practice in the Place-based tool is:
        \n\n***<center>(weighted population for GP practice / GP practice registered population for GP practice) / (weighted population for ICB / GP practice registered population for ICB).</center>***
        <br>The calculation of a need index for a given service element for a GP practice in the Annexes is:
        \n\n***<center>(weighted population for GP practice / GP practice registered population for GP practice) / (weighted population for England / GP practice registered population for England).</center>***
        <br>The implication is that the ICB-level and place-level need indices in the downloaded csv from the Place-based tool are not comparable.
    """, unsafe_allow_html=True)

with st.expander("How do individual components relate to the overall Core and Primary Medical Care indices?"):
    st.markdown("""
        For relative weighting of components, please see Annex J (Overall weighted populations) and K (Primary care) available from our website https://www.england.nhs.uk/allocations/.
        \n\nPlease note that the weighted populations and need indices for the individual, or sub-components, that make up the Core index are based on our models that predict need for these specific services and do not include cost adjustments. The Primary Medical Care in Core component is based on the same model as the Primary medical care need component in Primary Medical Care. The Primary Medical Care in Core element covers Other primary care services (not relating to pharmaceutical, ophthalmic, and dental services), NHS 111, and out of hours services.
        \n\nThe weighted populations and need indices for the overall Core and Primary Medical Care indices do include some cost adjustments. Overall Core is adjusted for MFF, an adjustment for unavoidable costs of remoteness, and an adjustment for excess finance cost of the private finance initiative (PFI).
    """, unsafe_allow_html=True)
    st.markdown("""
        More information on these adjustments can be found in our Technical Guide, also available from our website https://www.england.nhs.uk/allocations/.
    """, unsafe_allow_html=True)

with st.expander("Are there any important caveats to be aware of if I want to use the Place-based tool?"):
    st.markdown("""
        The Place-based tool presents results based on thorough analysis undertaken by a team of analysts at NHS England and is overseen by an independent external group, the Advisory Committee on Resource Allocation (ACRA), which provides advice to the Secretary of State for Health and Social Care and the Chief Executive of NHS England. The data used in the analysis represents millions of patients, their use of healthcare services, the cost of that use, as well as their demographics.
        \n\nWhile this presents a strong quantitative evidence-base, it is important to note that the analysis and the results presented in the Place-Based tool do not capture insights that are not covered in the data it draws on. This concerns insights into unmet need, populations with characteristics that are not captured in the demographics covered in the data (such as religion, sexuality), and local developments that might affect local need such as large housing developments. We advise users to validate the results from the Place-based tool with local information to contextualise the insights you draw from the Place-based tool.
        \n\nIn addition, the Place-based tool presents information on targets, and only includes information that is held at the GP practice level. It does not include information on other steps in the allocation approach that are applied to calculate final allocations to ICBs in £s, such as convergence and additional funding. It does not include the Emergency Ambulance Cost Adjustment (EACA) because this is calculated at the middle super output areas (MSOA) and applied directly to the ICB level instead of GP practice level. Finally, while the Place-based tool covers the Core and Primary Care budget streams, it currently does not include the Specialised Commissioning budget stream.
    """, unsafe_allow_html=True)

with st.expander("Can I use just use the weighted populations and need indices at the GP practice level?"):
    st.markdown("""
        The analysis presented in the Place-based tool is developed to support the fair share allocation of resources at the ICB level. At the ICB-level, the results are accurate. At smaller area levels, however, results will lose accuracy. At the GP practice level, the most granular level, results are less stable, and it becomes more important to use local insights to validate the results.
    """, unsafe_allow_html=True)

with st.expander("Where can I learn more about the data and methodology underpinning the Place-based tool?"):
    st.markdown("""
        Our website provides a wealth of information on the data used and analysis conducted. Our main website (https://www.england.nhs.uk/allocations/) always refers to the latest allocations, although links to historical allocations are provided. The site is structured as follows. Links are not provided as updates might cause the links to break, while the structure will remain in place:
    """, unsafe_allow_html=True)
    st.markdown("""
        - The site starts by providing the allocation of resources in £s (header: Allocation of resources).
        - It then covers our technical guide to the allocations, which described the methodology (header: Technical guide to ICB allocations).
        - The guide is followed by the Annexes (header: Supporting spreadsheets for allocations). The Place-based tool uses the data in these Annexes (but applies a different calculation to derive need indices).
        - The Annexes are followed by supporting tools (header: Supporting tools for allocations), including the Place-based tool, but also an Infographics guide.
        - The tools are followed by a list of background materials (header: Background materials) that also cover in-depth reports on the methodologies for the different service elements, by the year that those methodologies were last updated.
        - Finally, the site covers some ACRA papers that provide insights into how the Committee steers the development of methodologies, ACRA recommendation letters, and further reading of external papers that pertain to the resource allocation methodology (headers: ACRA recommendation letters and papers; Further reading).
    """, unsafe_allow_html=True)

with st.expander("My colleague cannot access the Place-based tool. Why is that and how can this be resolved?"):
    st.markdown("""
        The Place-based tool is hosted on Streamlit, and this service is sometimes blocked by your organisation’s firewall settings. To access from within your organisation, your IT department would need to change some rules in their firewall.
        \n\nWhere the organisation has a web proxy or firewall proxy, a rule needs to be added to bypass/allow the URL.
        \n\nMore information can be found on Streamlit’s website: https://streamlit.io/.
    """, unsafe_allow_html=True)

with st.expander("I have another question. How can I contact you?"):
    st.markdown("""
        For any other questions, please contact us at england.revenue-allocations@nhs.net.
    """, unsafe_allow_html=True)

with st.expander("Further information"):
    st.markdown("""
        Further information in support of the tool can be found in the NHS England GitHub repository docs folder: 
        \n\n""" + config['repo_url'] +
        """\n\nThis includes this user guide and a readme file with other useful information regarding this tool 
        \n\n""" + config['readme_url'])