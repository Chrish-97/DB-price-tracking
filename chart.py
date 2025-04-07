import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


df = pd.read_csv('ticket_prices.csv', delimiter=',', index_col=0)
df.index = pd.to_datetime(df.index)

df = df.tail(300)
plt.figure(figsize=(20, 12))
df.plot()
plt.xticks(rotation=45, ha='right') 
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.tight_layout()
plt.savefig('sampledata.png')
