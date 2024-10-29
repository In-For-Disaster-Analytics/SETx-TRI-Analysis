# %% [markdown]
# # Toxics Release Inventory (TRI) Overview

# %% [markdown]
# The U.S. Environmental Protection Agency (EPA) TRI Program (https://www.epa.gov/toxics-release-inventory-tri-program) was created through the 1986 Emergency Planning and Community Right-to-Act (EPCRA) to provide information about air, land, and water releases of toxic chemicals from industrial and federal facilities. The current ***TRI toxic chemicals list contains 794 individually listed chemicals and 33 chemical categories***. 
# 
# Refer to EPA guidance (https://guideme.epa.gov/ords/guideme_ext/f?p=guideme:home) for detailed information regarding reporting requirements. If a facility meets all of three criteria, it must report for each chemical for which the reporting requirement is triggered. These include that it is (1) within a covered industy sector (as identified by six-digit North American Classification System or NAICS codes); (2) employs 10 or more full-time equivalent employees; and (3) manufactures, processes, or otherwise uses a TRI-listed chemical in the quantities above threshold levels in a given year. It should be noted that other air emissions from a facility that do not meet the reporting requirements in a given year would not be represented in the TRI. Data are reported annually. 

# %% [markdown]
# ## Objectives of this Platform

# %% [markdown]
# 
# This interactive platform was developed to provide information about TRI air emissions (stack + fugitive) from faciltiies in SETx counties (Jefferson, Orange, Hardin, Jasper, Newton) for a user-selected year beginning in 1987. TRI data are obtained directly from the EPA through the TRI Basic Data Files: https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-present. 
# 
# The platform was designed to enable DOE SETx-UIFL project team members to: 
# 1. easily ingest annual TRI air data
# 2. conduct analyses relevant to air quality and cross-theme research 
# 3. provide supporting information for interactions with stakeholders in SETx.
# 

# %% [markdown]
# #### Using the platform, you can determine:
# 1. Air emissions in total and by individual counties in Texas
# 2. TRI-listed chemicals and their quantitites emitted in SETx
# 3. Industrial sectors and facilities that contribute to emissions of all or selected chemicals in SETx
# 4. Chemical profiles of emissions from industrial sectors in SETx
# 5. Chemical profiles of emissions from indiviudal facilities in SETx 

# %%
import pandas as pd
import geopandas as gpd
from itables import init_notebook_mode
import ipywidgets as widgets
from ipywidgets import interact,fixed
pd.set_option('display.max_colwidth', 10)
init_notebook_mode(all_interactive=True)
import folium
import matplotlib.pyplot as plt
import re
from plotly.offline import init_notebook_mode, iplot
from plotly.graph_objs import *
from ipywidgets import  Dropdown, Layout
from IPython.display import display
import plotly.express as px
import plotly.graph_objects as go
from ipywidgets import Layout
init_notebook_mode(connected=True)         # initiate notebook for offline plot
def remove_numbers_and_hyphen_with_space(text):
     return re.sub(r'\d+\. ', '', text)

# %% [markdown]
# ## Read Files
# 
# ### Select a TRI Year of Interest (1987 - Most Recent Available Release)

# %%
year = slider = widgets.IntSlider(
    value=2022,
    min=1987,
    max=2022,
    step=1,
    description='Year of Emissions:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d',
        layout=Layout(width='75%'),
    style={'description_width': 'initial'}
)

region = widgets.Dropdown(
    options=["TX", 'US'],
    value='TX',
    description='Region of Interest',
    disabled=False,
        layout=Layout(width='75%'),
    style={'description_width': 'initial'}
)
display(year)
display(region)


def download():
    try:
        df = pd.read_csv(f'https://data.epa.gov/efservice/downloads/tri/mv_tri_basic_download/{year.value}_{region.value}/csv')
        return df
    except Exception as e:
        return f"Error downloading data: {str(e)}"

# Create the download button
download_button = widgets.Button(
    description='Download Data',
    disabled=False,
    button_style='', # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Click to download data',
    icon='download', # (FontAwesome names without the `fa-` prefix)
    layout=Layout(width='75%'),
    style={'description_width': 'initial'}
)

output = widgets.Output()
# Define what happens when the button is clicked
@output.capture()
def on_button_clicked(b):
    with output:
        print("Downloading data... This may take a while.")
        result = download()
        if isinstance(result, pd.DataFrame):
            print(f"Download complete. Shape of data: {result.shape}")
        else:
            print(result)

# Attach the function to the button
download_button.on_click(on_button_clicked)

# Display the button and output
# display(download_button, output)

# %% [markdown]
# ### TRI BASICS DOWNLOAD
# *Note the most recent emission inventory data can be subject to updates by EPA.*

# %%

if len(output.outputs)==0:
    TRI=download()
else: 
    TRI = output

NAICS = pd.read_excel("2022_NAICS_Descriptions.xlsx")
counties = gpd.read_file('Texas_County_Boundaries_Detailed_-8523147194422581030.geojson')
TRI.columns= [remove_numbers_and_hyphen_with_space(c) for c in TRI.columns]
TRI['NAICS 6-digit']= TRI['PRIMARY NAICS']


# %% [markdown]
# ### Join Tables, Adjust Size of columns

# %%
TRI = TRI.join(NAICS.set_index("Code"), on="PRIMARY NAICS")
TRI['NAICS Description']= TRI['Title']
TRI['CHEMICAL']= TRI.apply(lambda x: x['CHEMICAL'][:100], axis=1)
counties['Counties']=(counties.CNTY_NM.str.upper())


# %% [markdown]
# ## Calculate Total Air Emissions (Stack + Fugitive) by Chemical for Each Texas Facility 

# %%
def calculate_Total_Air(x):
    if x['UNIT OF MEASURE']=='Pounds':
        return x['5.1 - FUGITIVE AIR']+x['5.2 - STACK AIR']
    else:
        return (x['5.1 - FUGITIVE AIR']+x['5.2 - STACK AIR'])/453.592 #Note dioxin converted from grams to pounds
TRI['Total Air (lbs)']= TRI.apply(lambda x: calculate_Total_Air(x), axis=1)
TRI['Total Air (Tons)']=TRI['Total Air (lbs)']/2000


# %% [markdown]
# ## Calculate Total Air Emissions in Texas
# Sum of stack and fugitive emissions (pounds; tons) from all Texas facilities for selected year

# %%
print(f"Texas Total (lbs) = {TRI['Total Air (lbs)'].sum() :,} ")
print(f"Texas Total (Tons)= {TRI['Total Air (Tons)'].sum() :,} ")

# %%
county_df = pd.DataFrame()
county_df['County'] = TRI['COUNTY'].unique()
for g in TRI.groupby('COUNTY'):
    county_df.loc[county_df['County']==g[0], 'TRI 2022 Air Total (pounds)']=g[1]['Total Air (lbs)'].sum()
county_df['TRI 2022 Air Total (Tons)']=county_df['TRI 2022 Air Total (pounds)']/2000
county_df['TRI Air Release Total (County Rank)']=county_df['TRI 2022 Air Total (Tons)'].rank(ascending=False)
tri_counties = counties.join(county_df.set_index('County'), on = 'Counties').reset_index()
tri_counties.fillna(0, inplace = True)

# %% [markdown]
# ## Total Air Emissions by Texas County
# Ranking of Total Air Emissions (lbs; Tons) for Texas Counties TRI. 
# #### Select column to order ascending/descending

# %%
def display_county_df():
    display(county_df)

# Create the download button
download_button = widgets.Button(
    description='Refresh',
    disabled=False,
    button_style='', # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Click to download data',
    icon='download', # (FontAwesome names without the `fa-` prefix)
    layout=Layout(width='75%'),
    style={'description_width': 'initial'}
)

output = widgets.Output()
# Define what happens when the button is clicked
@output.capture()
def on_button_clicked(b):
    with output:
        
        result = display_county_df()
        

# Attach the function to the button
download_button.on_click(on_button_clicked)
display_county_df()
# Display the button and output
# display(download_button)

# %% [markdown]
# ## Map TRI Emissions (Tons) by Texas County 

# %%
from branca.colormap import LinearColormap

# Create a map centered on Texas
m = folium.Map(location=[31, -100], zoom_start=6)
breaks = [0, 100, 200, 500, 1000, 2500, 5000]
colors = ['#00FF00', '#66FF00', '#CCFF00', '#FFFF00', '#FFCC00', '#FF6600', '#FF0000']
# Create a color map with custom breaks
# colormap = LinearColormap(colors=colors, vmin=0, vmax=5000)
# colormap.index = breaks
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

# Display the map
display(m)

# %% [markdown]
# ## Air Emissions and Ranking by Chemical, Industrial Sector, or Facility for SETx Counties 

# %%
setx_counties = ['JASPER', 'JEFFERSON', 'ORANGE', 'HARDIN', 'NEWTON' ]
dropdown = widgets.Dropdown(
    options=[ 'CHEMICAL','NAICS Description', "FACILITY NAME"],
    value='CHEMICAL',
    description='Group by:',
    disabled=False,
)
slider = widgets.IntSlider(
    value=20,
    min=0,
    max=252,
    step=5,
    description='Top Emissions:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d'
)


box = widgets.Box([dropdown, slider])


# %% [markdown]
# #### Select Emissions Ranking by Chemical, North American Industry Classification System (NAICS) Description, or Facility

# %%
setx_counties = ['JASPER', 'JEFFERSON', 'ORANGE', 'HARDIN', 'NEWTON' ]


# %%


# Assuming TRI and setx_counties are defined elsewhere in your code

dropdown = widgets.Dropdown(
    options=['CHEMICAL', 'NAICS Description', "FACILITY NAME"],
    value='CHEMICAL',
    description='Group by:',
    disabled=False,
    layout=Layout(width='75%'),
    style={'description_width': 'initial'}
)

# slider = widgets.IntSlider(
#     value=20,
#     min=0,
#     max=252,
#     step=5,
#     description='Top Emissions:',
#     disabled=False,
#     continuous_update=False,
#     orientation='horizontal',
#     readout=True,
#     readout_format='d',
#     layout=Layout(width='75%'),
#     style={'description_width': 'initial'}
# )

box = widgets.Box([dropdown])
out = widgets.Output()

@out.capture()
def create_chart_plotly(group, setx=True):
    # Use inputs to format chart data
    if setx:
        chemical = TRI.loc[TRI['COUNTY'].isin(setx_counties)].groupby(group)['Total Air (Tons)'].sum()
    else:
        chemical = TRI.groupby(group)['Total Air (Tons)'].sum()
    
    length = len(chemical)
    slider.max = length
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



    # Clear previous output and display the new chart
    out.clear_output(wait=True)
    fig = go.FigureWidget(bar_plot)
    display(fig)

# Create the interactive widget
interactive_plot = widgets.interactive(create_chart_plotly, group=dropdown,  setx=True)

# # Display the widget and output
display(box, out)
# interactive_plot


# %% [markdown]
# ## Industrial Sector Chemical Profiles in SETx-UIFL

# %%

geo = {'CHEMICAL':['NAICS Description', "FACILITY NAME"],
       'NAICS Description':['CHEMICAL'],
         'FACILITY NAME':['CHEMICAL']}
row = Dropdown(options = geo.keys(),
                description='Select what you want to profile ',
                align_items='stretch',
                layout=Layout(width='75%'),
                 style= {'description_width': 'initial'} )
init = row.value
columns = Dropdown(options=geo[init],
                    description='Select how you want it profiled (Columns) ',
                    align_items='stretch',
                   layout=Layout(width='75%'),
                     style= {'description_width': 'initial'} )

selection  = widgets.SelectMultiple(
                        options=TRI.loc[(TRI['COUNTY'].isin(setx_counties)),'NAICS Description'].unique(),
                        value=['Paperboard Mills', 'Petrochemical Manufacturing'],
                        layout=Layout(width='75%', height='80px'), 
                        style= {'description_width': 'initial'},
                        description="Select columns you want to view:"
                    )


def display_NAICS_profile( row, column, NAICS  ):
    display(f'Select which {row} to profile by {column} sector.',)
    columns.options = geo[row] 
    selection.options = TRI.loc[(TRI['COUNTY'].isin(setx_counties)),columns.value].unique()
    if len(selection.value)==0:
        selection.value= TRI.loc[(TRI['COUNTY'].isin(setx_counties)),columns.value].unique().tolist()[:3]
    try:
        return TRI.loc[(TRI['COUNTY'].isin(setx_counties)) & (TRI[columns.value].isin(NAICS))& (TRI['CHEMICAL'])].pivot_table(index=row, 
                    columns=column, values='Total Air (Tons)', aggfunc='sum', fill_value=0)
    except Exception:
        pass





# %%

interact(display_NAICS_profile, NAICS=selection, row=row,  column=columns)



# %%



