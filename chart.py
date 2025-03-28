import pandas
import matplotlib.pyplot as plt

df = pandas.read_csv('ticket_prices.csv', delimiter=',', index_col=0)
df.plot()

plt.savefig('sampledata.png')