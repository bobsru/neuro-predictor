import pandas as pd
from pandas.tseries.offsets import BDay
import numpy as np
import datetime as dt
from pandas_datareader import data, wb
from keras.models import load_model
import os
import yfinance as yf
import time
import sys
import scipy.misc
import subprocess
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import cv2
from collections import defaultdict
from alpha_vantage.foreignexchange import ForeignExchange
from mpl_finance import candlestick2_ochl, volume_overlay

def dataset(base_dir, n):
    # print("base_dir : {}, n : {}".format(base_dir, n))
    d = defaultdict (list)
    for root, subdirs, files in os.walk (base_dir):
        for filename in files:
            file_path = os.path.join (root, filename)
            assert file_path.startswith (base_dir)
            suffix = file_path[len (base_dir):]
            suffix = suffix.lstrip ("\\")
            label = suffix.split ("\\")[0]
            d[label].append (file_path)

    tags = sorted (d.keys ())
    processed_image_count = 0
    useful_image_count = 0

    X = []
    y = []

    for class_index, class_name in enumerate (tags):
        filenames = d[class_name]
        for filename in filenames:
            processed_image_count += 1
            img = cv2.imread (filename)
            height, width, chan = img.shape
            assert chan == 3
            X.append (img)
            y.append (class_index)
            useful_image_count += 1

    # print("processed {}, used {}".format(processed_image_count,useful_image_count))

    X = np.array (X).astype (np.float32)
    y = np.array (y)

    return X, y, tags

def build_dataset(data_directory, img_width):
    X, y, tags = dataset (data_directory, int (img_width))
    feature = X
    return feature

def fetch_AV_data(ticker, fname, max_attempt, period, check_exist):
    if (os.path.exists (fname) == True) and check_exist:
        print ("file exist")
    else:
        # remove exist file
        if os.path.exists (fname):
            os.remove (fname)
        for attempt in range (max_attempt):
            time.sleep (2)
            try:
                cc = ForeignExchange (key='06VFCKNZ709V6XFG')
                # There is no metadata in this call
                data, _ = cc.get_currency_exchange_daily (from_symbol=ticker[:3], to_symbol=ticker[3:])
                df = pd.DataFrame.from_dict (data).transpose ().sort_index ().tail (period)
                df.to_csv (fname)
                print ("success: {}".format (fname))

            except Exception as e:
                if attempt < max_attempt - 1:
                    print ('Attempt {}: {}'.format (attempt + 1, str (e)))
                else:
                    raise
            else:
                break

def ohlc2cs(fname, dimension):
    print ("Converting olhc to candlestick")
    inout = fname
    df = pd.read_csv (fname, parse_dates=True, index_col=0)
    df.fillna (0)
    plt.style.use ('dark_background')
    df.reset_index (inplace=True)
    df['Date'] = df.index
    fig, ax1 = plt.subplots ()
    candlestick2_ochl (ax1, df['1. open'], df['4. close'], df['2. high'], df['3. low'], width=.6, colorup='#53c156',
                       colordown='#ff1717')
    ax1.grid (False)
    ax1.set_xticklabels ([])
    ax1.set_yticklabels ([])
    ax1.xaxis.set_visible (False)
    ax1.yaxis.set_visible (False)
    ax1.axis ('off')
    pngfile = "{}.png".format (inout)
    fig.savefig (pngfile, pad_inches=0, transparent=False)
    plt.close (fig)

    img = cv2.imread (pngfile)
    newimg = cv2.resize (img, (int (dimension), int (dimension)))
    cv2.imwrite (pngfile, newimg)
    print ("Converting olhc to candlestik finished.")

def make_prediction(ticker, model):
    dimension = 128
    period = 20

    fileparam = "today"

    # get historical data
    fetch_AV_data (ticker, "{}_{}.csv".format (ticker, fileparam), 5, period, False)
    passed = True
    try:
        # convert to candlestickchart
        ohlc2cs ("{}_{}.csv".format (ticker, fileparam), int (dimension))
        pass
    except Exception as e:
        os.remove ("{}_{}.csv".format (ticker, fileparam))
        print ("Error when download historical data, please re-run.")
        passed = False
        pass
    if passed:
        # prepare dataset
        img = [cv2.imread ("{}_{}.csv.png".format (ticker, fileparam))]
        X_test = np.array (img).astype (np.float32)

        predicted = model.predict(X_test)
        print (predicted)
        y_pred = np.argmax (predicted, axis=1)
        if y_pred[0] == 0:
            pred = "DOWN"
        else:
            pred = "UP"
        print (pred)

        # cleaning
        os.remove ("{}_{}.csv".format (ticker, fileparam))
        os.remove ("{}_{}.csv.png".format (ticker, fileparam))

        return pred


if __name__ == '__main__':
    pass
