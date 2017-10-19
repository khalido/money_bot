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

def new_csv(sender_id, file_name, file_url, bank=None):
    """takes a newly downloaded csv file, parses it and appends it to a users existing csv if it exists
    """
    
    # check what kind of csv file this is
    if re.search("pocketbook-export", file_url):
        bank = "pocketbook"

    # parse csv here to convert it into our default df format
    df_new = parse_df(pd.read_csv(file_name), bank)
    # later on, delete this new csv file after dealing with it
    
    #open existing user exists
    df_old = open_user_csv(sender_id)

    if isinstance(df_old, pd.DataFrame):
        # https://pandas.pydata.org/pandas-docs/stable/merging.html
        df = df_new.append(df_old, ignore_index=True)
        msg = f"Parsed {df_new.shape[0]} transactions and added to to the existing {df_old.shape[0]} transactions"
    else:
        df = df_new
        msg = f"Parsed {df.shape[0]} transactions from your uploaded csv"

    # save to disk  
    df.to_pickle("data/" + sender_id + ".pkl")
    
    return msg


def parse_df(df, bank=None):
    """takes in a a unparsed df and transforms it into our final version
    this function is only called for new csv files"""

    if bank == "pocketbook":
        data = df.join(df.category.str.split(" - ", expand=True))
        data.rename(columns={0: "Category", 1: "Subcategory"}, inplace=True)
        drop_cols = ["notes", "tags", "bank", "accountname", "accountnumber", "category"]
        data.drop(drop_cols, inplace=True, axis=1)
        data['date'] = data['date'].apply(pd.to_datetime)
        data["Category"] = data["Category"].astype(str).str.lower()
        data["Subcategory"] = data["Subcategory"].astype(str).str.lower()
    elif bank="bendigo":
        col_names = ["date", "amount", "description"]
        data = pd.read_csv("data/transactions.csv", header=None, names=col_names)
    else:
        print("Don't have a parser for this kind of csv file")
        return df
    
    print(f"parsed file with {bank} parser")
    return data

def open_user_csv(sender_id, df=None):
    """takes a sender_id and returns that users dataframe if it exists"""
    
    file_name = "data/" + sender_id + ".pkl"
    if os.path.isfile(file_name):
        print("file found")
        df = pd.read_pickle(file_name)
        print(f"---users file found and opened, has shape {df.shape}---")
    else:
        print("----no existing csv file found-----")
    return df

def split_suburb(description):
    """takes in a discription and returns a string with
    `@@` seperator b/w merchant and suburb and deletes the bit after suburb. Run by:
    df['temp'] = df['description'].apply(suburb)
    after running split suburb, use a line like: 
    df[["merchant", "suburb"]] = pd.DataFrame(df.temp.str.split("@@", expand=True))
    to split your new temp column into two, then delete the temp col
    """
    wrds = description.split()
    if len(wrds) > 2 and not wrds[-3].isdigit():
        return " ".join(wrds[:-3])[:-1] + "@@" + wrds[-3]
    else:
        return [0, 0]