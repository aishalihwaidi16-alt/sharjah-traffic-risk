from pathlib import Path
from datetime import date
import html
import io
import pandas as pd
import streamlit as st

ROOT=Path(__file__).parent
st.set_page_config(page_title="Sharjah Police | Risk Intelligence",page_icon="🛡️",layout="wide",initial_sidebar_state="expanded")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
.stApp{background:radial-gradient(ellipse at 95% -5%,#2b343c 0%,#161c23 42%,#10161c 100%);color:#f1ece4;font-family:'DM Sans',sans-serif}
section[data-testid='stSidebar']{background:#1b232b;border-right:1px solid #35404a}
.block-container{max-width:1580px;padding-top:1.35rem;padding-bottom:4rem}
h1,h2,h3{font-family:'Manrope',sans-serif!important;letter-spacing:-.035em!important;color:#f4eee6!important}
h1{font-size:2.15rem!important}h3{font-size:1.2rem!important}
[data-testid='stMetric']{background:linear-gradient(145deg,#29343d,#202932);border:1px solid #3e4a53;border-radius:16px;padding:18px 20px}
[data-testid='stMetricLabel']{color:#c6c4bd!important}[data-testid='stMetricValue']{color:#f7ead9!important}
[data-testid='stDataFrame']{border:1px solid #45515a;border-radius:12px;overflow:hidden}
[data-testid='stAlert']{border-radius:11px}
div.stButton>button[kind='primary']{background:#d5b58a!important;color:#17212a!important;font-weight:800;border:0;border-radius:10px}
div.stButton>button,div.stDownloadButton>button{border-radius:10px}
.header{border:1px solid #45515a;border-radius:20px;padding:23px 28px;background:linear-gradient(110deg,#29343e,#1c242d);margin-bottom:22px}
.eyebrow{font-size:11px;letter-spacing:.16em;color:#d7b98f;font-weight:800}
.brand{font-family:Manrope,sans-serif;font-weight:800;font-size:25px;letter-spacing:.055em;color:#f5ece0;margin-top:6px}
.subtitle{color:#b7c0c5;font-size:13px;margin-top:4px}
.panel{border:1px solid #414e58;background:#222c35;border-radius:15px;padding:21px;margin:8px 0 15px}
.pill{display:inline-block;background:#38424a;border:1px solid #68737a;border-radius:100px;padding:5px 12px;color:#ecd0aa;font-size:11px;font-weight:800;letter-spacing:.07em}
.muted{color:#b9c0c5;font-size:13px;line-height:1.65}
.action{background:#27343b;border-left:3px solid #d3b184;border-radius:8px;padding:15px;margin:8px 0;color:#f0e7da}
</style>""",unsafe_allow_html=True)

@st.cache_data
def load_roads():
    df=pd.read_csv(ROOT/'data'/'road_segments.csv',encoding='utf-8-sig')
    df.columns=df.columns.str.strip()
    df['Road_Segment_ID']=df['Road_Segment_ID'].astype(str).str.strip()
    for c in ['Latitude','Longitude','Road_Speed_Limit','Number_of_Lanes']:
        if c in df:df[c]=pd.to_numeric(df[c],errors='coerce')
    return df.drop_duplicates('Road_Segment_ID')

@st.cache_data
def load_sample():
    return pd.read_csv(ROOT/'data'/'hannah_risk_ranking.csv',encoding='utf-8-sig')

def check_ranking(df):
    df.columns=df.columns.str.strip()
    required={'Risk_Rank','Road_Segment_ID','Road_Name','Risk_Level','Times_Riskier_Than_Usual','Suggested_Action'}
    missing=required-set(df.columns)
    if missing:raise ValueError('Missing columns: '+', '.join(sorted(missing)))
    df=df[list(required)].copy()
    df['Risk_Rank']=pd.to_numeric(df['Risk_Rank'],errors='coerce')
    df['Times_Riskier_Than_Usual']=pd.to_numeric(df['Times_Riskier_Than_Usual'],errors='coerce')
    df['Road_Segment_ID']=df['Road_Segment_ID'].astype(str).str.strip()
    return df.sort_values('Risk_Rank').reset_index(drop=True)

roads=load_roads()
st.markdown("""<div class="header"><div class="eyebrow">PUBLIC SAFETY / DATA INTELLIGENCE / ACADEMIC PROTOTYPE</div><div class="brand">◈ SHARJAH POLICE</div><div class="subtitle">Severe Accident Risk Intelligence · Road Segment Prioritization</div></div>""",unsafe_allow_html=True)

with st.sidebar:
    st.markdown('### ◈ Scenario control center')
    st.caption('Hannah’s Alteryx scenario parameters. Live inference is not connected yet.')
    scenario_date=st.date_input('Scenario date',value=date(2026,11,5))
    scenario_hour=st.selectbox('Scenario hour',[f'{i:02d}:00' for i in range(24)],index=23)
    scenario_congestion=st.selectbox('Congestion', ['Low','Medium','High'])
    scenario_weather=st.selectbox('Weather',['Clear','Rain','Fog','Haze','Cloudy'])
    scenario_temp=st.number_input('Temperature (°C)',min_value=-10.0,max_value=65.0,value=30.0)
    scenario_visibility=st.number_input('Visibility (m)',min_value=0,max_value=50000,value=10000,step=500)
    st.button('Run new scenario',type='primary',use_container_width=True,disabled=True,help='Requires Hannah’s executable trained model or Alteryx execution service.')
    st.info('Scenario inputs are not applied to the displayed rankings. Those rankings are from Hannah’s saved output.')
    st.divider()
    st.markdown('**Replace the sample ranking**')
    uploaded=st.file_uploader('Upload an Alteryx ranking export',type=['xlsx','csv'],help='Requires the same six output columns as Hannah’s Roads_Risk_Ranking.xlsx.')
    st.caption('Only tabular ranking exports are accepted. No pickle uploads or model execution.')

try:
    if uploaded:
        incoming=pd.read_excel(uploaded) if uploaded.name.lower().endswith('.xlsx') else pd.read_csv(uploaded)
        ranked=check_ranking(incoming)
        source_name='UPLOADED ALTERYX EXPORT'
    else:
        ranked=check_ranking(load_sample())
        source_name='HANNAH’S SAVED SAMPLE OUTPUT'
except Exception as e:
    st.error(f'Could not read ranking: {e}');st.stop()

merged=ranked.merge(roads,on='Road_Segment_ID',how='left',suffixes=('','_Reference'))
if 'Road_Name_Reference' in merged: merged=merged.drop(columns=['Road_Name_Reference'])

st.title('Road Risk Overview')
st.caption('Ranked severe-accident risk and preventive actions · Results reproduced from the supplied Alteryx output')
st.markdown(f'<span class="pill">{html.escape(source_name)}</span> &nbsp; <span class="pill">NOT LIVE INFERENCE</span>',unsafe_allow_html=True)
st.write('')
areas=sorted(merged['Area_District'].dropna().astype(str).unique()) if 'Area_District' in merged else []
a,b,c=st.columns([1.2,1,1.2])
with a: area_filter=st.multiselect('Area / district',areas,placeholder='All areas')
with b: level_filter=st.multiselect('Risk level', ['High','Medium','Low'],placeholder='All levels')
with c: search=st.text_input('Search road or segment',placeholder='e.g. Maliha or SHJ-RD-009')
view=merged.copy()
if area_filter:view=view[view['Area_District'].isin(area_filter)]
if level_filter:view=view[view['Risk_Level'].isin(level_filter)]
if search:view=view[view['Road_Name'].astype(str).str.contains(search,case=False,regex=False)|view['Road_Segment_ID'].astype(str).str.contains(search,case=False,regex=False)]

k1,k2,k3,k4=st.columns(4)
with k1:st.metric('Road segments ranked',f'{len(view):,}')
with k2:st.metric('High risk',str((view['Risk_Level']=='High').sum()))
with k3:st.metric('Medium risk',str((view['Risk_Level']=='Medium').sum()))
with k4:st.metric('Highest relative risk',f"{view['Times_Riskier_Than_Usual'].max():.1f}×" if len(view) else '—')

st.markdown('### Geographic risk overview')
left,right=st.columns([1.7,1],gap='large')
with left:
    coords=view.dropna(subset=['Latitude','Longitude']).copy() if {'Latitude','Longitude'}.issubset(view.columns) else pd.DataFrame()
    if len(coords):
        coords=coords[coords['Latitude'].between(20,30)&coords['Longitude'].between(50,60)].copy()
    if len(coords):
        try:
            import pydeck as pdk
            palette={'High':[220,100,87,210],'Medium':[217,177,120,210],'Low':[89,166,143,210]}
            coords['color']=coords['Risk_Level'].map(palette).apply(lambda x:x if isinstance(x,list) else [170,177,181,210])
            coords['radius']=coords['Times_Riskier_Than_Usual'].clip(lower=.5,upper=6).fillna(1).mul(70).add(90)
            layer=pdk.Layer('ScatterplotLayer',data=coords,get_position='[Longitude, Latitude]',get_fill_color='color',get_radius='radius',pickable=True,stroked=True,get_line_color=[255,255,255,160],line_width_min_pixels=1)
            deck=pdk.Deck(map_style='https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',initial_view_state=pdk.ViewState(latitude=float(coords.Latitude.mean()),longitude=float(coords.Longitude.mean()),zoom=10.2,pitch=0),layers=[layer],tooltip={'html':'<b>{Road_Name}</b><br/>Rank: {Risk_Rank}<br/>Level: {Risk_Level}<br/>Relative risk: {Times_Riskier_Than_Usual}×','style':{'backgroundColor':'#202a32','color':'#f5eadb'}})
            st.pydeck_chart(deck,use_container_width=True,height=390)
        except Exception:
            st.map(coords,latitude='Latitude',longitude='Longitude',zoom=10)
        st.caption('Map pins use supplied road-segment reference coordinates. They are not exact road geometries. Gold = medium, red = high, green = low.')
    else:st.info('No matching road coordinates are available for the selected results.')
with right:
    st.markdown('**Model performance reported by Hannah**')
    st.markdown("""<div class="panel"><div class="eyebrow">TEST-SAMPLE RANKING</div><h2 style="font-size:2.3rem;margin:8px 0">84.6%</h2><div class="muted">of severe accident observations in the top 10% of ranked test samples</div><hr><h2 style="font-size:2.3rem;margin:8px 0">100%</h2><div class="muted">of severe accident observations in the top 20% of ranked test samples</div></div>""",unsafe_allow_html=True)
    st.caption('Figures are Hannah’s reported test results; not validated real-world forecasting guarantees.')
    st.markdown('**What does relative risk mean?**')
    st.caption('“2.5×” means the model score was 2.5 times the workflow’s normal reference score. It is not a 250% accident probability.')

st.markdown('### Prioritized road segments')
cols=['Risk_Rank','Road_Name','Road_Segment_ID','Area_District','Risk_Level','Times_Riskier_Than_Usual','Suggested_Action']
show=view[[c for c in cols if c in view]].copy()
show=show.rename(columns={'Risk_Rank':'Rank','Road_Name':'Road','Road_Segment_ID':'Segment ID','Area_District':'Area','Risk_Level':'Risk level','Times_Riskier_Than_Usual':'Relative risk (×)','Suggested_Action':'Recommended action'})
st.dataframe(show,hide_index=True,use_container_width=True,height=390,column_config={'Relative risk (×)':st.column_config.NumberColumn(format='%.1f×'),'Risk level':st.column_config.TextColumn()})
st.download_button('↓ Export filtered rankings (CSV)',data=show.to_csv(index=False).encode('utf-8-sig'),file_name='Sharjah_Risk_Ranking.csv',mime='text/csv')

st.markdown('### Road intelligence & preventive action')
if len(view):
    options=view['Road_Segment_ID'].tolist()
    chosen=st.selectbox('Select a road segment',options,format_func=lambda s:next((f"#{int(r.Risk_Rank)}  {r.Road_Name}  ({s})" for r in view.itertuples() if r.Road_Segment_ID==s),s))
    r=view[view['Road_Segment_ID']==chosen].iloc[0]
    a,b=st.columns([1,1.3],gap='large')
    with a:
        st.markdown(f'<div class="panel"><div class="eyebrow">RANK #{int(r.Risk_Rank)} · {html.escape(str(r.Risk_Level).upper())} RISK</div><h3>{html.escape(str(r.Road_Name))}</h3><div class="muted">Segment: {html.escape(str(r.Road_Segment_ID))}<br>Area: {html.escape(str(r.get("Area_District","—")))}<br>Relative risk: <b>{float(r.Times_Riskier_Than_Usual):.1f}×</b></div></div>',unsafe_allow_html=True)
    with b:
        st.markdown('**Suggested preventive action**')
        st.markdown(f'<div class="action">{html.escape(str(r.Suggested_Action))}</div>',unsafe_allow_html=True)
        st.caption('Suggested by Hannah’s Alteryx risk-action matching logic; not a dispatch instruction.')
else:st.info('No roads match the current filters.')

with st.expander('How Hannah’s ranking is generated'):
    st.markdown("""1. Hannah’s Alteryx boosted model scores road/direction combinations for a scenario.
2. The workflow retains the maximum score across directions for each road segment.
3. It divides that score by the model’s normal reference score to obtain relative risk.
4. It labels risk **High** at ≥3×, **Medium** at ≥1× and **Low** otherwise.
5. It attaches a preventive action from the cleaned risk-action library.
6. It sorts the road segments and exports `Roads_Risk_Ranking.xlsx`.

The dashboard reads that **saved** output. The scenario controls cannot generate a new export without an executable model or Alteryx service.""")
st.divider()
st.caption('Capstone research prototype · Actual rankings from Hannah’s sample export · Not an operational decision or dispatch system.')
