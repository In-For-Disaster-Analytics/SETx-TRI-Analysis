import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import folium
st.set_page_config(layout="wide")
st.header('Point Source Emissions Reports for SETx')
st.write("This cookbook provides emissions data for point sources in Southeast Texas (SETx) counties\
          (Jefferson, Orange, Hardin, Newton, and Jasper) that met the Texas Commission on\
          Environmental Quality (TCEQ) reporting requirements as stated in 30 Texas Administrative \
         Code, Section 101.10 during 2022. Figure 1 shows emissions thresholds for required reporting \
         of regulated pollutants and hazardous air pollutants (HAPs) in 2022. Note that thresholds vary\
          with location, status of attainment with the National Ambient Air Quality Standard (NAAQS) \
         for ozone, and special inventory requests by the TCEQ. ")
st.write(" Year 2022 data are the most recent available at the time of development of this cookbook.\
          Data were obtained from the State of Texas Air Reporting System (STARS) on October 10, 2024\
        by Mark Muldoon of the TCEQ Emissions Assessment Division and provided to Elena McDonald-Buller.\
           Note that the data may be subject to revisions and corrections and is a snapshot of the data\
           pulled on the date specified.")
st.write("""The cookbook includes the following 2022 site-wide emissions by contaminant:
- Annual emissions (routine + permitted maintenance/startup/shutdown activities), tons/year
- Ozone season, pounds/day (May 1- September 30)
- Scheduled maintenance/startup/shutdown activities that were not authorized by a new source review permit, tons/year
- Emission events, tons/year
""")
st.write("Emission events are defined in 30 TAC 101.1 (28) as any upset event or unscheduled\
          maintenance, startup, or shutdown activity, from a common cause that results in\
          unauthorized emissions of air contaminants from one or more emissions points at\
          a regulated entity.")
st.write('The cookbook was developed by Will Mobley and Elena McDonald-Buller for internal project\
          use only to easily access reported emissions for a given site during the specified year.\
         Emissions may vary over time and do not represent ambient concentrations. ')
st.write("For further information see: [TCEQ's point source inventory](%s)" % "https://www.tceq.texas.gov/airquality/point-source-ei/psei.html")


st.header('List of Point Sources in SETx')
st.write("This list is designed to aid users in identifying point sources of interest\
          in SETx including their geographic location and industry sector")

df = pd.read_csv("TCEQ_Stars.csv")
NAICS = pd.read_csv("./NAICS.csv")
NAICS=NAICS[['TCEQ Air Account Number', 'Industry Description']].drop_duplicates()
df = df.join(NAICS.set_index( 'TCEQ Air Account Number'), on='TCEQ Air Account Number', how='left')
df['LATITUDE']= df['Latitude (Decimal)']
df['LONGITUDE']=-df['Longitude (Decimal)']
iris = pd.read_csv("./iris.csv")
iris['CASRN'] = iris['CASRN'].apply(lambda x: str(x).replace("-", ""))
df = df.join(iris.set_index( 'CASRN'), on='CAS Number', how='left')
with st.form("NaicsvsIndustry"):
  select_industry = st.selectbox("Select to use either Industry code or Facility Name",['Industry Description', 'Organization'] )
  submitted_ind = st.form_submit_button("Submit")
 
st.write("Select a either the industry or facility name above to view emissions data")


with st.form("table"):
  select = st.selectbox("Select Code", df[select_industry].sort_values().unique())
  submitted = st.form_submit_button("Submit")
  # if submitted:
  #   columns = ['Organization', 'Site',  'TCEQ Contaminant Name', 'Annual Emissions (tpy)', 'Ozone Season Emissions (ppd) ', 'Emissions From SSMS (tpy)', 'Emission Events (tpy)']
  #   st.dataframe(df.loc[(df['Year']==2022) & (df[select_industry]==select), columns])

  #   st.map(df.loc[(df['Year']==2022) & (df[select_industry]==select) ])
  if submitted:
    columns = ['Organization', 'Site', 'TCEQ Contaminant Name', 'Annual Emissions (tpy)', 
               'Ozone Season Emissions (ppd) ', 'Emissions From SSMS (tpy)', 'Emission Events (tpy)','Toxicity Value Type'	,'Toxicity Value']
    st.dataframe(df.loc[(df['Year']==2022) & (df[select_industry]==select), columns])
    
    filtered_df = df.loc[(df['Year']==2022) & (df[select_industry]==select)]
    m = folium.Map(location=[filtered_df['LATITUDE'].mean(), filtered_df['LONGITUDE'].mean()], 
                  zoom_start=10)
    
    for idx, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row['LATITUDE'], row['LONGITUDE']],
            popup=row['Organization'],
            tooltip=row['Site'],
            radius=8,
            color='red',
            fill=True
        ).add_to(m)
    
    st_folium(m, width=800)