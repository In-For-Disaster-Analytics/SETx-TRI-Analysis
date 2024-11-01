import streamlit as st
import pandas as pd
from branca.colormap import LinearColormap
import re
import folium

import pandas as pd
import geopandas as gpd
import streamlit_folium as st_folium
import plotly.express as px
import plotly.graph_objects as go         # initiate notebook for offline plot


def remove_numbers_and_hyphen_with_space(text):
     return re.sub(r'\d+\. ', '', text)
# @st.cache_data
def download(year, region):
    try:
        TRI = pd.read_csv(f'https://data.epa.gov/efservice/downloads/tri/mv_tri_basic_download/{year}_{region}/csv')

   
        NAICS = pd.read_excel("../2022_NAICS_Descriptions.xlsx")
        counties = gpd.read_file('../Texas_County_Boundaries_Detailed_-8523147194422581030.geojson')
        TRI.columns= [remove_numbers_and_hyphen_with_space(c) for c in TRI.columns]
        TRI['NAICS 6-digit']= TRI['PRIMARY NAICS']
        TRI = TRI.join(NAICS.set_index("Code"), on="PRIMARY NAICS")
        TRI['NAICS Description']= TRI['Title']
        TRI['CHEMICAL']= TRI.apply(lambda x: x['CHEMICAL'][:100], axis=1)
        counties['Counties']=(counties.CNTY_NM.str.upper())
        TRI['Total Air (lbs)'] = TRI.apply(lambda x: calculate_Total_Air(x), axis=1)
        TRI['Total Air (Tons)']= TRI['Total Air (lbs)']/2000
        if isinstance(TRI, pd.DataFrame):
            st.write("Data downloaded successfully.")
            st.dataframe(TRI)
        return NAICS, counties, TRI

    except Exception as e:
        return f"Error downloading data: {str(e)}", None, None

def calculate_Total_Air(x):
    if x['UNIT OF MEASURE']=='Pounds':
        return x['5.1 - FUGITIVE AIR']+x['5.2 - STACK AIR']
    else:
        return (x['5.1 - FUGITIVE AIR']+x['5.2 - STACK AIR'])/453.592 #Note dioxin converted from grams to pounds

def map(tri_counties):
    st.write('## Map TRI Emissions (Tons) by Texas County')
    # Create a map centered on Texas
    m = folium.Map(location=[31, -100], zoom_start=6)
    breaks = [0, 100, 200, 500, 1000, 2500, 5000]
    colors = ['#00FF00', '#66FF00', '#CCFF00', '#FFFF00', '#FFCC00', '#FF6600', '#FF0000']
    # Create a color map with custom breaks
    colormap = LinearColormap(colors=colors, vmin=0, vmax=5000, index=breaks)
    tri_counties['TRI 2022 Air Total (Tons)']=tri_counties['TRI 2022 Air Total (Tons)'].astype(int)
    # Add the counties to the map
    folium.GeoJson(
        tri_counties,
        style_function=lambda feature: {
            'fillColor': colormap(int(min(feature['properties']['TRI 2022 Air Total (Tons)'], 50000))),
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.7,
        },
        tooltip=folium.GeoJsonTooltip(fields=['CNTY_NM', 'TRI 2022 Air Total (Tons)'])
    ).add_to(m)



    # Create a custom legend with responsive sizing
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; width: 220px; height: 180px;
    border:2px solid grey; z-index:9999; font-size:14px; background-color:white;
    ">&nbsp; TRI 2022 Air Total (Tons)<br>
    &nbsp; <i style="background:#00FF00; display:inline-block; width:10px; height:10px;"></i>&nbsp;0 - 100<br>
    &nbsp; <i style="background:#66FF00; display:inline-block; width:10px; height:10px;"></i>&nbsp;100 - 200<br>
    &nbsp; <i style="background:#CCFF00; display:inline-block; width:10px; height:10px;"></i>&nbsp;200 - 500<br>
    &nbsp; <i style="background:#FFFF00; display:inline-block; width:10px; height:10px;"></i>&nbsp;500 - 1,000<br>
    &nbsp; <i style="background:#FFCC00; display:inline-block; width:10px; height:10px;"></i>&nbsp;1,000 - 2,500<br>
    &nbsp; <i style="background:#FF6600; display:inline-block; width:10px; height:10px;"></i>&nbsp;2,500 - 5,000<br>
    &nbsp; <i style="background:#FF0000; display:inline-block; width:10px; height:10px;"></i>&nbsp;5,000+
    </div>
    '''


    # Add the custom legend to the map
    m.get_root().html.add_child(folium.Element(legend_html))

        # Display the map in Streamlit
    st_folium.folium_static(m)


def Texas_Total_Air(TRI):
    st.write('## Calculate Total Air Emissions in Texas')
    st.write('Sum of stack and fugitive emissions (pounds; tons) from all Texas facilities for selected year.')
    st.write(f'#### **Texas Total (lbs) = {TRI['Total Air (lbs)'].sum() :,}**')
    st.write(f'#### **Texas Total (Tons)= {TRI['Total Air (Tons)'].sum() :,}**')
    county_df = pd.DataFrame()
    county_df['County'] = TRI['COUNTY'].unique()
    for g in TRI.groupby('COUNTY'):
        county_df.loc[county_df['County']==g[0], 'TRI 2022 Air Total (pounds)']=g[1]['Total Air (lbs)'].sum()
    county_df['TRI 2022 Air Total (Tons)']=county_df['TRI 2022 Air Total (pounds)']/2000
    county_df['TRI Air Release Total (County Rank)']=county_df['TRI 2022 Air Total (Tons)'].rank(ascending=False)
    tri_counties = counties.join(county_df.set_index('County'), on = 'Counties').reset_index()
    tri_counties.fillna(0, inplace = True)
    st.write('## Total Air Emissions by Texas County\n\
            Ranking of Total Air Emissions (lbs; Tons) for Texas Counties TRI.')
    st.write('#### Select column to order ascending/descending.')
    st.dataframe(county_df)
    map(tri_counties)

def create_chart_plotly(TRI, group, setx=True):
    # Use inputs to format chart data
    if setx:
        chemical = TRI.loc[TRI['COUNTY'].isin(setx_counties)].groupby(group)['Total Air (Tons)'].sum()
    else:
        chemical = TRI.groupby(group)['Total Air (Tons)'].sum()
    
    length = len(chemical)
    plot_data = chemical.loc[chemical > 0].sort_values(ascending=False)
    
    # Set chart title per inputs
    if setx:
        plot_title = f'2022 Annual Emissions of TRI-Listed Chemicals in SETx'
    else:
        plot_title = f'2022 Annual Emissions of TRI-Listed Chemicals in Texas'
    
    # Generate chart
    y_min = chemical[chemical > 0].min()

    truncated_index = [str(x)[:50] + '...' if len(str(x)) > 50 else str(x) for x in plot_data.index]

    bar_plot = px.bar(
        x=truncated_index,
        y=plot_data.values,
        labels={'x': group, 'y': 'Total Air (Tons)'},
        log_y=True,
        range_y=[y_min, chemical.max()],
        title=plot_title
    )
    bar_plot.update_traces(
        hovertemplate='<b>%{x}</b><br>Total Air: %{y:.2f} Tons<extra></extra>',
        text=plot_data.index,
        textposition='none'
    )

    # Update the layout of the chart including labeling, size, etc.
    bar_plot.update_layout(
        xaxis_tickangle=45,
        yaxis_title='Total Air Emissions(Tons)',
        width=1200,
        height=800,
        xaxis=dict(
            range=[-0.5, 19.5],  # Set initial x-axis range to show first 20 bars
            rangeslider=dict(visible=True),  # Add a range slider
            rangeselector=dict(
                buttons=list([
                    dict(count=20, label="20", step="all", stepmode="backward"),
                    dict(count=50, label="50", step="all", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            )
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Rockwell"
        )
    )

    st.plotly_chart(bar_plot)



def display_NAICS_profile( TRI ):
    st.write('## Industrial Sector Chemical Profiles in SETx-UIFL')
    geo = {'CHEMICAL':['NAICS Description', "FACILITY NAME"],
       'NAICS Description':['CHEMICAL'],
         'FACILITY NAME':['CHEMICAL']}
    with st.form(key='my_form'):
        row = st.selectbox(options = geo.keys(),
                        label='Select what you want to profile ',
        )
        st.session_state.init = st.session_state.row
        columns = st.selectbox(options=geo[st.session_state.init],
                            label='Select how you want it profiled (Columns) ',
                        )

        selection  = st.multiselect(
                                options=TRI.loc[(TRI['COUNTY'].isin(setx_counties)),'NAICS Description'].unique(),
                                default=['Paperboard Mills', 'Petrochemical Manufacturing'],
                            
                                label="Select columns you want to view:"
                            )
        submit_button = st.form_submit_button(label='Submit')

    st.write(f'Select which {row} to profile by {columns} sector.',)
    if len(selection)==0:
        selection= TRI.loc[(TRI['COUNTY'].isin(setx_counties)),columns].unique().tolist()[:3]

    st.dataframe( TRI.loc[(TRI['COUNTY'].isin(setx_counties)) & (TRI[columns].isin(selection))& \
                    (TRI['CHEMICAL'])].pivot_table(index=row, 
                columns=columns, values='Total Air (Tons)', aggfunc='sum', fill_value=0))


 
if __name__ == '__main__':
        
    st.write(" # Toxics Release Inventory (TRI) Overview")

    st.write(" The U.S. Environmental Protection Agency (EPA) TRI Program (https://www.epa.gov/toxics-release-inventory-tri-program) \
            was created through the 1986 Emergency Planning and Community Right-to-Act (EPCRA) to provide information about air, land, \
            and water releases of toxic chemicals from industrial and federal facilities. The current ***TRI toxic chemicals list contains\
            794 individually listed chemicals and 33 chemical categories***. ")
    st.write("Refer to EPA guidance (https://guideme.epa.gov/ords/guideme_ext/f?p=guideme:home) for detailed information regarding reporting \
            requirements. If a facility meets all of three criteria, it must report for each chemical for which the reporting requirement \
            is triggered. These include that it is (1) within a covered industy sector (as identified by six-digit North American \
            Classification System or NAICS codes); (2) employs 10 or more full-time equivalent employees; and (3) manufactures, processes,\
            or otherwise uses a TRI-listed chemical in the quantities above threshold levels in a given year. It should be noted that \
            other air emissions from a facility that do not meet the reporting requirements in a given year would not be represented in \
            the TRI. Data are reported annually. ")

    st.write(" ## Objectives of this Platform")

    st.write(" This interactive platform was developed to provide information about TRI air emissions (stack + fugitive) from faciltiies \
            in SETx counties (Jefferson, Orange, Hardin, Jasper, Newton) for a user-selected year beginning in 1987.\
            TRI data are obtained directly from the EPA through the TRI Basic Data Files:\
            https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-present. ")
    st.write("""  The platform was designed to enable DOE SETx-UIFL project team members to: 
    1. Easily ingest annual TRI air data
    2. Conduct analyses relevant to air quality and cross-theme research ")
    3. Provide supporting information for interactions with stakeholders in SETx.""")

    st.write(" #### Using the platform, you can determine:")
    st.write(""" 1. Air emissions in total and by individual counties in Texas
    2. TRI-listed chemicals and their quantitites emitted in SETx
    3. Industrial sectors and facilities that contribute to emissions of all or selected chemicals in SETx
    4. Chemical profiles of emissions from industrial sectors in SETx
    5. Chemical profiles of emissions from indiviudal facilities in SETx """)

    st.write("# TRI BASICS DOWNLOAD")
    st.write(" *Note the most recent emission inventory data can be subject to updates by EPA.*")
    st.write("### Select a TRI Year of Interest (1987 - Most Recent Available Release)")

    # # %%
    with st.form(key='download'):
        year = slider = st.slider(
        value=2022,
        min_value=1987,
        max_value=2022,
        step=1,
        label='Year of Emissions:')
        region =st.selectbox(
            options=["TX", 'US'],
            index=0,
            label='Region of Interest',
            disabled=False,    )
        submit = st.form_submit_button('Get Data')

    NAICS, counties, TRI = download(year, region)

    st.write('## Calculate Total Air Emissions (Stack + Fugitive) by Chemical for Each Texas Facility ')

    Texas_Total_Air(TRI)
    setx_counties = ['JASPER', 'JEFFERSON', 'ORANGE', 'HARDIN', 'NEWTON' ]
    st.session_state.dropdown = st.selectbox(
        options=[ 'CHEMICAL','NAICS Description', "FACILITY NAME"],
        index=0,
        label='Group by:')
    st.write('## Air Emissions and Ranking by Chemical, Industrial Sector, or Facility for SETx Counties')
    create_chart_plotly(TRI, st.session_state.dropdown, setx=True)
    display_NAICS_profile(TRI)






