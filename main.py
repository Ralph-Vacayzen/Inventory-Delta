import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title='Inventory Delta',
    page_icon='⚖️'
)

st.caption('VACAYZEN')
st.title('Inventory Delta')
st.info('Get the changes in inventory, after looking at warehouse counts and what is in the field.')

with st.expander('Uploaded Files'):
    
    file_descriptions = [
        ['Availability.xlsx','Vacayzen_Production > Availability'],
        ['Inventory.xlsx','Vacayzen_Production > Vacayzen_Production > Inventory'],
        ['Vacayzen Inventory Count - Warehouse.csv','Google Sheet > Vacayzen Inventory Count > Warehouse'],
        ['Vacayzen Inventory Count - Seagrove.csv','Google Sheet > Vacayzen Inventory Count > Seagrove'],
        ['Vacayzen Inventory Count - Pointe.csv','Google Sheet > Vacayzen Inventory Count > Pointe'],
        ['Vacayzen Inventory Count - House Bikes.csv','Google Sheet > Vacayzen Inventory Count > House Bikes']
    ]

    files = {
        'Availability.xlsx': None,
        'Inventory.xlsx': None,
        'Vacayzen Inventory Count - Warehouse.csv': None,
        'Vacayzen Inventory Count - Seagrove.csv': None,
        'Vacayzen Inventory Count - Pointe.csv': None,
        'Vacayzen Inventory Count - House Bikes.csv': None
    }


    uploaded_files = st.file_uploader(
        label='Files (' + str(len(files)) + ')',
        accept_multiple_files=True
    )

    st.info('File names are **case sensitive** and **must be identical** to the file name below.')
    st.dataframe(pd.DataFrame(file_descriptions, columns=['Required File','Source Location']), hide_index=True, use_container_width=True)










if len(uploaded_files) > 0:
    for index, file in enumerate(uploaded_files):
        files[file.name] = index

    hasAllRequiredFiles = True
    missing = []

    for file in files:
        if files[file] == None:
            hasAllRequiredFiles = False
            missing.append(file)

if len(uploaded_files) > 0 and not hasAllRequiredFiles:
    for item in missing:
        st.warning('**' + item + '** is missing and required.')


elif len(uploaded_files) > 0 and hasAllRequiredFiles:

    date = st.date_input('Date of Warehouse Inventory Count:')

    print('reading in availability...')
    df          = pd.read_excel(uploaded_files[files['Availability.xlsx']])
    df.columns  = ['start','end','asset','quantity']

    print('converting dates...')
    df['start'] = pd.to_datetime(df['start']).dt.date
    df['end']   = pd.to_datetime(df['end']).dt.date

    print('grabbing lines that include provided date...')
    df = df[(df['start'] <= date) & (df['end'] > date)]

    print('pivoting...')
    rented = df.pivot_table(values=['quantity'], index=['asset'], aggfunc=np.sum)
    rented = rented.reset_index()



    print('reading in counts...')
    wh          = pd.read_csv(uploaded_files[files['Vacayzen Inventory Count - Warehouse.csv']])
    ss          = pd.read_csv(uploaded_files[files['Vacayzen Inventory Count - Seagrove.csv']])
    tp          = pd.read_csv(uploaded_files[files['Vacayzen Inventory Count - Pointe.csv']])
    hb          = pd.read_csv(uploaded_files[files['Vacayzen Inventory Count - House Bikes.csv']])

    print('merging counts...')
    wh.columns  = ['category','asset','warehouse']
    ss.columns  = ['category','asset','seagrove']
    tp.columns  = ['category','asset','pointe']
    hb.columns  = ['category','asset','house']

    df = pd.merge(wh, ss, how='outer')
    df = pd.merge(df, tp, how='outer')
    df = pd.merge(df, hb, how='outer')
    df = df.fillna(0)
    df['counted'] = df.warehouse + df.seagrove + df.pointe + df.house
    df = df[['category','asset','counted']]

    print('merging rented and counted...')
    total           = pd.merge(df, rented, how='left', on='asset')
    total.columns   = ['category','asset','counted','rented']

    print('determing total, buffer, and final quantities...')
    total           = total.fillna(0)
    total['total']  = total.counted + total.rented
    total['buffer'] = total.total * 0.05
    total           = total.round(0)
    total['final']  = total.total - total.buffer

    print('separating house and rental items...')
    rentals = total[total.category != 'House Bikes']
    house   = total[total.category == 'House Bikes']


    print('reading in inventory...')
    df          = pd.read_excel(uploaded_files[files['Inventory.xlsx']])
    df.columns  = ['category','asset','current']
    df          = df[['asset','current']]

    print('merging totals and inventory...')
    rental_delta          = pd.merge(rentals, df, how='left', on='asset')
    rental_delta['delta'] = rental_delta.final - rental_delta.current
    house_delta           = pd.merge(house, df, how='left', on='asset')
    house_delta['delta']  = house_delta.final - house_delta.current



    print('generating delta details...')
    l, r = st.columns(2)
    l.download_button(label='DOWNLOAD RENTAL DELTA DETAIL', data=rental_delta.to_csv(index=False), file_name='rental_delta_detail.csv', mime='csv', use_container_width=True, type='secondary')
    l.download_button(label='DOWNLOAD HOUSE DELTA DETAIL', data=house_delta.to_csv(index=False), file_name='house_delta_detail.csv', mime='csv', use_container_width=True, type='secondary')

    print('generating deltas...')
    rd = rental_delta[['asset','delta']]
    hd = house_delta[['asset','delta']]

    rd = rd[rd.delta != 0]
    hd = hd[hd.delta != 0]

    r.download_button(label='DOWNLOAD RENTAL DELTA', data=rd.to_csv(index=False), file_name='rental_delta.csv', mime='csv', use_container_width=True, type='primary')
    r.download_button(label='DOWNLOAD HOUSE DELTA', data=hd.to_csv(index=False), file_name='rental_delta.csv', mime='csv', use_container_width=True, type='primary')
