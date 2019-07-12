import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import mpl_finance as mpf
import numpy as np
from scipy import integrate
from scipy.stats import t

def heikin_ashi(df1):   
    df1.reset_index(inplace=True)
    df1['HA close']=(df1['Open']+df1['Close']+df1['High']+df1['Low'])/4
    df1['HA open']=float(0)
    df1['HA open'][0]=df1['Open'][0]
    for n in range(1,len(df1)): 
        df1.at[n,'HA open']=(df1['HA open'][n-1]+df1['HA close'][n-1])/2
    temp=pd.concat([df1['HA open'],df1['HA close'],df1['Low'],df1['High']],axis=1)
    df1['HA high']=temp.apply(max,axis=1)
    df1['HA low']=temp.apply(min,axis=1)
    del df1['Adj Close']
    del df1['Volume']
    return df1

def signal_generation(df, method, stls):
    df1=method(df)
    df1['signals']=0
    df1['cumsum']=0
    for n in range(1,len(df1)):
        if (df1['HA open'][n]>df1['HA close'][n] and df1['HA open'][n]==df1['HA high'][n] and
            np.abs(df1['HA open'][n]-df1['HA close'][n])>np.abs(df1['HA open'][n-1]-df1['HA close'][n-1]) and
            df1['HA open'][n-1]>df1['HA close'][n-1]):
            df1.at[n,'signals']=1
            df1['cumsum']=df1['signals'].cumsum()
            if df1['cumsum'][n]>stls:
                df1.at[n,'signals']=0
        elif (df1['HA open'][n]<df1['HA close'][n] and df1['HA open'][n]==df1['HA low'][n] and 
        df1['HA open'][n-1]<df1['HA close'][n-1]):
            df1.at[n,'signals']=-1
            df1['cumsum']=df1['signals'].cumsum()
            if df1['cumsum'][n]>0:
                df1.at[n,'signals']=-1*(df1['cumsum'][n-1])
            if df1['cumsum'][n]<0:
                df1.at[n,'signals']=0
    return df1

def plot(df1,ticker):
    df1.set_index(df1['Date'],inplace=True)
    ax1=plt.subplot2grid((200,1), (0,0), rowspan=120,ylabel='HA price')
    mpf.candlestick2_ochl(ax1, df1['HA open'], df1['HA close'], df1['HA high'], df1['HA low'], width=1, colorup='g', colordown='r')
    plt.grid(True)
    plt.xticks([])
    plt.title('Heikin-Ashi')
    ax2=plt.subplot2grid((200,1), (120,0), rowspan=80,ylabel='price',xlabel='')
    df1['Close'].plot(ax=ax2,label=ticker)
    ax2.plot(df1.loc[df1['signals']==1].index,df1['Close'][df1['signals']==1],marker='^',lw=0,c='g',label='long')
    ax2.plot(df1.loc[df1['signals']<0].index,df1['Close'][df1['signals']<0],marker='v',lw=0,c='r',label='short')
    plt.grid(True)
    plt.legend(loc='best')
    plt.show()

def portfolio(df1):
    capital0=10000
    positions=100
    df1['cumsum']=df1['signals'].cumsum()
    portfolio=pd.DataFrame()
    portfolio['holdings']=df1['cumsum']*df1['Close']*positions
    portfolio['cash']=capital0-(df1['signals']*df1['Close']*positions).cumsum()
    portfolio['total asset']=portfolio['holdings']+portfolio['cash']
    portfolio['return']=portfolio['total asset'].pct_change()
    portfolio['signals']=df1['signals']
    portfolio['date']=df1['Date']
    portfolio.set_index('date',inplace=True)
    return portfolio

def profit(portfolio):
    fig=plt.figure()
    bx=fig.add_subplot(111) 
    portfolio['total asset'].plot(label='Total Asset')
    bx.plot(portfolio['signals'].loc[portfolio['signals']==1].index,portfolio['total asset'][portfolio['signals']==1],lw=0,marker='^',c='g',label='long')
    bx.plot(portfolio['signals'].loc[portfolio['signals']<0].index,portfolio['total asset'][portfolio['signals']<0],lw=0,marker='v',c='r',label='short')
    plt.legend(loc='best')
    plt.grid(True)
    plt.xlabel('Date')
    plt.ylabel('Asset Value')
    plt.title('Total Asset')
    plt.show()

def omega(risk_free,degree_of_freedom,maximum,minimum):
    y=integrate.quad(lambda g:1-t.cdf(g,degree_of_freedom),risk_free,maximum)
    x=integrate.quad(lambda g:t.cdf(g,degree_of_freedom),minimum,risk_free)
    z=(y[0])/(x[0])
    return z

def sortino(risk_free,degree_of_freedom,growth_rate,minimum):
    v=np.sqrt(np.abs(integrate.quad(lambda g:((risk_free-g)**2)*t.pdf(g,degree_of_freedom),risk_free,minimum)))
    s=(growth_rate-risk_free)/v[0]
    return s

def mdd(series):
    temp=0
    for i in range(1,len(series)):
        if temp>(series[i]/max(series[:i])-1):
            temp=(series[i]/max(series[:i])-1)
    return temp

def stats(portfolio,df1,stdate,eddate):
    stats=pd.DataFrame([0])
    maximum=np.max(portfolio['return'])
    minimum=np.min(portfolio['return'])
    capital0=10000
    growth_rate=(float(portfolio['total asset'].iloc[-1]/capital0))**(1/len(df1))-1
    std=float(np.sqrt((((portfolio['return']-growth_rate)**2).sum())/len(df1)))
    benchmark=yf.download('^GSPC',start=stdate,end=eddate)
    rb=float(benchmark['Close'].iloc[-1]/benchmark['Open'].iloc[0]-1)
    rf=(rb+1)**(1/len(df1))-1
    del benchmark
    stats['CAGR']=stats['portfolio return']=float(0)
    stats['CAGR'][0]=growth_rate
    stats['portfolio return'][0]=portfolio['total asset'].iloc[-1]/capital0-1
    stats['benchmark return']=rb
    stats['sharpe ratio']=(growth_rate-rf)/std
    stats['maximum drawdown']=mdd(portfolio['total asset'])
    stats['calmar ratio']=growth_rate/stats['maximum drawdown']
    stats['omega ratio']=omega(rf,len(df1),maximum,minimum)
    stats['sortino ratio']=sortino(rf,len(df1),growth_rate,minimum)
    stats['numbers of longs']=df1['signals'].loc[df1['signals']==1].count()
    stats['numbers of shorts']=df1['signals'].loc[df1['signals']<0].count()
    stats['numbers of trades']=stats['numbers of shorts']+stats['numbers of longs']  
    stats['total length of trades']=df1['signals'].loc[df1['cumsum']!=0].count()
    stats['average length of trades']=stats['total length of trades']/stats['numbers of trades']
    stats['profit per trade']=float(0)
    stats['profit per trade'].iloc[0]=(portfolio['total asset'].iloc[-1]-capital0)/stats['numbers of trades'].iloc[0]
    del stats[0]
    print(stats)

def main():
    stls=3
    ticker='NVDA'
    stdate='2015-04-01'
    eddate='2018-02-15'
    slicer=700
    df=yf.download(ticker,start=stdate,end=eddate)
    df1=signal_generation(df,heikin_ashi, stls)
    new=df1[slicer:]
    plot(new,ticker)
    portfo=portfolio(new)
    profit(portfo)
    stats(portfo,df1,stdate,eddate)

if __name__ == '__main__':
    main()