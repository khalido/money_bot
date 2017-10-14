import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# raw csv file from pocketbook for testing
data = pd.read_csv("data/pocketbook-export.csv")

def cost_of(what, when=None):
    # ignoring the date for now
    if what in data.category.values:
        plt.plot(data[data.category.values == "Amazon"]["amount"])
        plt.title("Spending on Amazon")
        plt.savefig("images/test.png")
        
        return -data[data.category.values == what]["amount"].sum()
