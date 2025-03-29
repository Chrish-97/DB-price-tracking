import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('ticket_prices.csv', delimiter=',', index_col=0)
df.index = pd.to_datetime(df.index)
plt.figure(figsize=(20, 12))
df.plot()
plt.xticks(rotation=45, ha='right')  
plt.locator_params(axis='x', nbins=15)  
plt.tight_layout()
plt.savefig('sampledata.png')
