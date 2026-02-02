import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Life Strategy", page_icon="⚔️")

# --- CONNECT TO GOOGLE SHEETS (CLOUD NATIVE) ---
def get_db_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Retrieve secrets from Streamlit Cloud environment
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # OPEN THE SHEET
        # Ensure your Google Sheet is named EXACTLY 'LifeStrategy_App'
        sheet = client.open("LifeStrategy_App") 
        return sheet
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        st.stop()

try:
    sh = get_db_connection()
    library_worksheet = sh.worksheet("Library")
    log_worksheet = sh.worksheet("Log")
except Exception as e:
    st.error("Could not find the worksheets. Make sure your Google Sheet has tabs named 'Library' and 'Log'.")
    st.stop()

# --- APP UI ---
st.title("Life Strategy Command ⚔️")

# Sidebar: The Deck
st.sidebar.header("Your Inventory")

try:
    library_data = library_worksheet.get_all_records()
    df_lib = pd.DataFrame(library_data)
except:
    df_lib = pd.DataFrame()

if not df_lib.empty:
    selected_card_name = st.sidebar.selectbox("Select Action", df_lib['Card_Name'])
    
    # Get details
    card_details = df_lib[df_lib['Card_Name'] == selected_card_name].iloc[0]
    
    # Display Card Stats
    st.sidebar.markdown(f"""
    **Type:** {card_details['Type']}  
    **Cost:** ⏳ {card_details['Cost_Time']} min  
    **Value:** 💎 {card_details['Value_Score']}
    """)
else:
    st.sidebar.warning("Library is empty. Add rows to Google Sheets!")

# Main Area: The Board
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Operations: {datetime.now().strftime('%A, %d %b')}")
    
    with st.form("play_card_form"):
        # Time slider 05:00 to 23:00
        time_slots = [f"{h:02d}:00" for h in range(5, 24)] 
        selected_time = st.select_slider("Time Slot", options=time_slots)
        submitted = st.form_submit_button(f"Commit '{selected_card_name}'")
        
        if submitted:
            new_row = [
                str(datetime.now().date()), 
                selected_time,              
                selected_card_name,         
                int(card_details['Value_Score']), 
                str(datetime.now())         
            ]
            
            with st.spinner("Syncing to Database..."):
                log_worksheet.append_row(new_row)
            st.success(f"Action Logged: {selected_card_name} at {selected_time}")

with col2:
    st.subheader("Daily Log")
    log_data = log_worksheet.get_all_records()
    df_log = pd.DataFrame(log_data)
    
    if not df_log.empty:
        # Show recent actions
        st.dataframe(df_log[['Time_Slot', 'Card_Name']].tail(10), hide_index=True)
        
        # Calculate Daily Total
        if 'Value_Gained' in df_log.columns:
             # Force numeric conversion to avoid errors
            numeric_values = pd.to_numeric(df_log['Value_Gained'], errors='coerce').fillna(0)
            st.metric("Total Value", int(numeric_values.sum()))
