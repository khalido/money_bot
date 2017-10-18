"""
bunch of helper utilities
"""

import requests
import re
import os
import pandas as pd
import numpy as np

def deal_with_file(sender_id, file_url, file_name=None):
    """takes sender_id and a url to file, downloads to disk and returns filename"""
    
    # first, check if the file contains .csv to make sure we want to download it
    if not re.search(".csv", file_url):
        print("csv file not found")
        return file_name
    
    print(f"downloading file from {sender_id} and saving to data_dir")  
    r = requests.get(file_url, stream=True)
    
    if r.status_code == requests.codes.ok:
        file_name = "data/" + sender_id + "_" + str(np.random.randint(1000,9999)) + ".csv"
        with open(file_name, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
        print(f"{file_name} saved to disk")
    else:
        print("couldn't download file")
    
    return file_name

def new_csv(sender_id, file_name):
    """takes a newly downloaded csv file, parses it and appends it to a users existing csv if it exists"""
    
    # parse csv here to convert it into our default df format
    df_new = parse_df(pd.read_csv(file_name))
    
    # do_stuff to clean up this new df
    
    #open existing user exists
    df_old = open_user_csv(sender_id)

    if df_old:
        # https://pandas.pydata.org/pandas-docs/stable/merging.html
        df = df_new.append(df_old, ignore_index=True)
    else:
        df = df_new
        
    df.to_csv("data/" + sender_id + ".csv")


def parse_df(df):
    """takes in a a unparsed df and transforms it into our final version
    this function is only called for new csv files"""

    return df

def open_user_csv(sender_id, df=None):
    """takes a sender_id and returns that users dataframe if it exists"""
    
    file_name = "data/" + sender_id + ".csv"
    if os.path.isfile(file_name):
        print("file found")
        df = pd.read_csv(file_name)
        print(f"---users file found and opened---")
    else:
        print("----no existing csv file found-----")
    return df
