import mne
import numpy as np
import pyedflib


file_name = r'C:\Users\ProSomno\Explore_CA4C_10Aug2022_1126_ExG.edf'
f = pyedflib.EdfReader(file_name)
hdr = f.getHeader()
print(hdr)
n = f.signals_in_file
signal_labels = f.getSignalLabels()
sigbufs = np.zeros((n, f.getNSamples()[0]))
for i in np.arange(n):
    sigbufs[i, :] = f.readSignal(i)

# data = mne.io.read_raw_edf(file_name)
# raw_data = data.get_data()
# # you can get the metadata included in the file and a list of all channels:
# info = data.info
# print(info)
# channels = data.ch_names

