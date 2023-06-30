'''
to run the app, open a terminal and type:
streamlit run Main_View.py

'''
import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
from prepare_data import Transformation
from Fourth_Analyser import FourthData
from UI import UInterface as UI
from tests import get_data, data_rota

if __name__ == '__main__':
    ui = UI(data_rota)