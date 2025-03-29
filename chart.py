import pandas as pd
import matplotlib.pyplot as plt

df = pandas.read_csv('ticket_prices.csv', delimiter=',', index_col=0)
df.index = pd.to_datetime(df.index)
plt.figure(figsize=(12, 6))
df.plot()
plt.xticks(rotation=45, ha='right')  # Drehe die Beschriftungen um 45 Grad
plt.locator_params(axis='x', nbins=10)  # Zeigt ca. 10 Ticks an
plt.tight_layout()
plt.savefig('sampledata.png')
