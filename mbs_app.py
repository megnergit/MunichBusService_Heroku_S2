from pathlib import Path
import pandas as pd
import config
# from importlib import reload
# https://qiita.com/Krypf/items/68c1f7c26efd084cf207
# dir(config)
# del config
from mbs.mbs import *
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yaml
import pdb
# ====================================
# Authentication
# ====================================

LOG_FILE = Path(config.LOG_FILE)
LOG_FILE_COLOR = Path(config.LOG_FILE_COLOR)
NOTE_FILE = Path(config.NOTE_FILE)
DATA_DIR = Path(config.DATA_DIR)
DATA_DIR_INNEN = Path(config.DATA_DIR_INNEN)
ST_KEY = config.ST_KEY

size = config.size
n_last = config.n_last
radius_innen_str = f'{config.radius_innen:.0f}'+' km'
radius_str = f'{config.radius:.0f}'+' km'

# freq = '12H' # '120S' '2H' '1D'
# # center = (11.57540, 48.13714)
# ============================================
# streamlit
# --------------------------------------------
df_agg = pd.read_csv(DATA_DIR / 'mbs_agg.csv',
                     parse_dates=['created_at_tz'],
                     index_col='created_at_tz')

df_agg.index.freq = df_agg.index.inferred_freq

df_pn = pd.read_csv(DATA_DIR / 'mbs_pn.csv')
df_pn['created_at'] = pd.to_datetime(df_pn['created_at'])
df_pn['created_at_tz'] = pd.to_datetime(df_pn['created_at_tz'])

df_kex = pd.read_csv(DATA_DIR / 'mbs_kex.csv')
# --------------------------------------------
# innenstadt < 4km
# --------------------------------------------
# df = pd.read_csv(DATA_DIR_INNEN / 'mbs_kex.csv')
df_pn_innen = pd.read_csv(DATA_DIR_INNEN / 'mbs_pn.csv')
df_pn_innen['created_at'] = pd.to_datetime(df_pn_innen['created_at'])
df_pn_innen['created_at_tz'] = pd.to_datetime(df_pn_innen['created_at_tz'])
df_pn_aussen = df_pn.loc[~df_pn['id'].isin(df_pn_innen['id'].to_list()), :]

# --------------------------------------------
# innen / aussen
# --------------------------------------------

fig_pie_innen = visualize_pie(
    df_pn_innen, size, 'Inner City < '+radius_innen_str)
fig_pie_aussen = visualize_pie(
    df_pn_aussen, size, 'Outer City > '+radius_innen_str)
# --------------------------------------------
# calculate daily aggregate
# --------------------------------------------
fig_agg = visualize_agg(df_agg, size)
fig_count = visualize_count(df_agg, size)
# --------------------------------------------
fig_pn = visualize_pn(df_pn, size, vertical=True)
# --------------------------------------------
# wordcloud
# --------------------------------------------
wc = create_wordcloud(df_kex, size)
fig_wc = visualize_wc(wc)
# --------------------------------------------
# folium
# --------------------------------------------
m_1 = plot_sentiment(df_kex)
# --------------------------------------------
# logfile
# --------------------------------------------
i = 0
with open(LOG_FILE, 'r') as f:
    log_text = f.readlines()
    print(i+1)

log_text = [s.replace('\n', '') for s in log_text]

with open(LOG_FILE_COLOR, 'r') as f:
    log_text_color = f.readlines()

log_text_color = [s.replace('\n', '<br />') for s in log_text_color]

# --------------------------------------------
# read YAML markdown text
with open(NOTE_FILE, 'r') as s:
    try:
        note = yaml.safe_load(s)
    except yaml.YAMLError as e:
        print(e)
# =====================================================================
# streamlit building
# =====================================================================
st.set_page_config(layout='wide')
# autoreload
count = st_autorefresh(interval=1000 * 1200, limit=16, key=ST_KEY)

# --------------------------------------------
# 1. row : cautions
# --------------------------------------------
col1, col2, col3 = st.columns((0.9, 0.9, 0.9))
with col1:
    st.markdown(note['note1'], unsafe_allow_html=True)

with col2:
    st.markdown(note['note2'], unsafe_allow_html=True)

with col3:
    st.markdown(note['note3'], unsafe_allow_html=True)

st.markdown("""___""")
# --------------------------------------------
# 2. row questions and conclusions
# --------------------------------------------
col1, col2, col3, col4, col5 = st.columns([1.0, 0.04, 0.4, 0.04, 0.4])
with col1:
    st.title('How People like Munich Bus Service')
    st.markdown(note['questions'], unsafe_allow_html=True)
    st.markdown(note['conclusions'], unsafe_allow_html=True)

with col3:
    st.plotly_chart(fig_pie_innen, use_container_width=True)

with col5:
    st.plotly_chart(fig_pie_aussen, use_container_width=True)
    caption = note['pie_chart_caption']
    caption = caption.replace('RADIUS_INNEN', radius_innen_str)
    caption = caption.replace('RADIUS', radius_str)
    st.markdown(caption, unsafe_allow_html=True)

# --------------------------------------------
# 3. row
# --------------------------------------------
st.markdown('### Overall Sentiment')
st.plotly_chart(fig_agg, use_container_width=True)
st.markdown('### How many Tweets about Bus?')
st.plotly_chart(fig_count, use_container_width=True)

# --------------------------------------------
# 5. row : report and polling log
# --------------------------------------------
col1, col2 = st.columns((1, 0.9))
log = '\n'.join(log_text)
log_color = ' '.join(log_text_color[-4:])
with col1:
    st.markdown(note['map_caption'])

with col2:
    st.markdown('### Polling log')
    st.markdown(log_color, unsafe_allow_html=True)

# --------------------------------------------
# 4. row
# --------------------------------------------
df_words = pd.DataFrame(dict(word=wc.words_.keys(), frac=wc.words_.values()))
df_words.sort_values(['frac'], ascending=False, inplace=True)

col1, col2, col3 = st.columns((2, 0.9, 0.9))
with col1:
    st.markdown('### Where people are satisfied/dissatisfied?')
    m_1.to_streamlit(height=size*1)

with col2:
    text = f'### Last {n_last} Tweets'
    st.markdown(text)
    st.plotly_chart(fig_pn, use_container_width=True)

with col3:
    st.markdown('### Satisfied/dissatisfied with...')
    st.image(wc.to_image())
    st.dataframe(df_words)

# --------------------------------------------
#  6. row
# --------------------------------------------
st.markdown('### All Data')
st.dataframe(df_kex.drop(
    ['name', 'screen_name'],
    axis=1, errors='ignore').sort_values(['id'], axis=0, ascending=False),
    height=size)

# --------------------------------------------
# END
# --------------------------------------------
