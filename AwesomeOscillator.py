import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

def ewmacd(signals,ma1,ma2):
    signals['macd ma1']=signals['Close'].ewm(span=ma1).mean()    
    signals['macd ma2']=signals['Close'].ewm(span=ma2).mean()   
    return signals
    
def signal_generation(df,method,ma1,ma2):
    signals=method(df,ma1,ma2)
    signals['macd positions']=0
    signals['macd positions'][ma1:]=np.where(signals['macd ma1'][ma1:]>=signals['macd ma2'][ma1:],1,0)
    signals['macd signals']=signals['macd positions'].diff()
    signals['macd oscillator']=signals['macd ma1']-signals['macd ma2']
    return signals

def awesome_ma(signals):
    signals['awesome ma1'],signals['awesome ma2']=0,0
    signals['awesome ma1']=((signals['High']+signals['Low'])/2).rolling(window=5).mean()
    signals['awesome ma2']=((signals['High']+signals['Low'])/2).rolling(window=34).mean()
    return signals

def awesome_signal_generation(df,method):
    signals=method(df)
    signals.reset_index(inplace=True)
    signals['awesome signals']=0
    signals['awesome oscillator']=signals['awesome ma1']-signals['awesome ma2']  
    signals['cumsum']=0
    for i in range(2,len(signals)):
        if (signals['Open'][i]>signals['Close'][i] and 
        signals['Open'][i-1]<signals['Close'][i-1] and 
        signals['Open'][i-2]<signals['Close'][i-2] and
        signals['awesome oscillator'][i-1]>signals['awesome oscillator'][i-2] and
        signals['awesome oscillator'][i-1]<0 and 
        signals['awesome oscillator'][i]<0):
            signals.at[i,'awesome signals']=1
        if (signals['Open'][i]<signals['Close'][i] and 
        signals['Open'][i-1]>signals['Close'][i-1] and 
        signals['Open'][i-2]>signals['Close'][i-2] and
        signals['awesome oscillator'][i-1]<signals['awesome oscillator'][i-2] and
        signals['awesome oscillator'][i-1]>0 and
        signals['awesome oscillator'][i]>0):
            signals.at[i,'awesome signals']=-1
        if signals['awesome ma1'][i]>signals['awesome ma2'][i]:
            signals.at[i,'awesome signals']=1
            signals['cumsum']=signals['awesome signals'].cumsum()
            if signals['cumsum'][i]>1:
                signals.at[i,'awesome signals']=0 
        if signals['awesome ma1'][i]<signals['awesome ma2'][i]:
            signals.at[i,'awesome signals']=-1
            signals['cumsum']=signals['awesome signals'].cumsum()
            if signals['cumsum'][i]<0:
                signals.at[i,'awesome signals']=0
    signals['cumsum']=signals['awesome signals'].cumsum()
    return signals

def plot(new,ticker):
    fig=plt.figure()
    ax=fig.add_subplot(211)
    new['Close'].plot(label=ticker)
    ax.plot(new.loc[new['awesome signals']==1].index,new['Close'][new['awesome signals']==1],label='AWESOME LONG',lw=0,marker='^',c='g')
    ax.plot(new.loc[new['awesome signals']==-1].index,new['Close'][new['awesome signals']==-1],label='AWESOME SHORT',lw=0,marker='v',c='r')
    plt.legend(loc='best')
    plt.grid(True)
    plt.title('Positions')
    bx=fig.add_subplot(212,sharex=ax)
    new['Close'].plot(label=ticker)
    bx.plot(new.loc[new['macd signals']==1].index,new['Close'][new['macd signals']==1],label='MACD LONG',lw=0,marker='^',c='g')
    bx.plot(new.loc[new['macd signals']==-1].index,new['Close'][new['macd signals']==-1],label='MACD SHORT',lw=0,marker='v',c='r')
    plt.legend(loc='best')
    plt.grid(True)
    plt.show()
    fig=plt.figure()
    cx=fig.add_subplot(211)
    c=np.where(new['Open']>new['Close'],'r','g')
    cx.bar(range(len(new)),new['awesome oscillator'],color=c,label='awesome oscillator')
    plt.grid(True)
    plt.legend(loc='best')
    plt.title('Oscillator')
    dx=fig.add_subplot(212,sharex=cx)
    new['macd oscillator'].plot(kind='bar',label='macd oscillator')
    plt.grid(True)
    plt.legend(loc='best')
    plt.xlabel('')
    plt.xticks([])
    plt.show()
    fig=plt.figure()
    ex=fig.add_subplot(211)
    new['awesome ma1'].plot(label='awesome ma1')
    new['awesome ma2'].plot(label='awesome ma2',linestyle=':')
    plt.legend(loc='best')
    plt.grid(True)
    plt.xticks([])
    plt.xlabel('')
    plt.title('Moving Average')
    fig=plt.figure()
    fx=fig.add_subplot(212,sharex=bx)
    new['macd ma1'].plot(label='macd ma1')
    new['macd ma2'].plot(label='macd ma2',linestyle=':')
    plt.legend(loc='best')
    plt.grid(True)
    plt.show()

def portfolio(signals):  
    capital0=5000
    positions=100
    portfolio=pd.DataFrame()
    portfolio['Close']=signals['Close']
    portfolio['awesome holding']=signals['cumsum']*portfolio['Close']*positions
    portfolio['macd holding']=signals['macd positions']*portfolio['Close']*positions
    portfolio['awesome cash']=capital0-(signals['awesome signals']*portfolio['Close']*positions).cumsum()
    portfolio['macd cash']=capital0-(signals['macd signals']*portfolio['Close']*positions).cumsum()
    portfolio['awesome asset']=portfolio['awesome holding']+portfolio['awesome cash']
    portfolio['macd asset']=portfolio['macd holding']+portfolio['macd cash']
    portfolio['awesome return']=portfolio['awesome asset'].pct_change()
    portfolio['macd return']=portfolio['macd asset'].pct_change()
    return portfolio

def profit(portfolio):
    gx=plt.figure()
    gx.add_subplot(111)
    portfolio['awesome asset'].plot()
    portfolio['macd asset'].plot()
    plt.legend(loc='best')
    plt.grid(True)
    plt.title('Awesome VS MACD')
    plt.show()

def mdd(series):
    temp=0
    for i in range(1,len(series)):
        if temp>(series[i]/max(series[:i])-1):
            temp=(series[i]/max(series[:i])-1)
    return temp

def stats(portfolio): 
    stats=pd.DataFrame([0])
    stats['awesome sharpe']=(portfolio['awesome asset'].iloc[-1]/5000-1)/np.std(portfolio['awesome return'])
    stats['macd sharpe']=(portfolio['macd asset'].iloc[-1]/5000-1)/np.std(portfolio['macd return'])
    stats['awesome mdd']=mdd(portfolio['awesome asset'])
    stats['macd mdd']=mdd(portfolio['macd asset'])
    print(stats)

def main():
    ma1=5
    ma2=34
    stdate=input('start date in format yyyy-mm-dd:')
    eddate=input('end date in format yyyy-mm-dd:')
    ticker=input('ticker:')
    df=yf.download(ticker,start=stdate,end=eddate)
    slicer=int(input('slicing:'))
    signals=signal_generation(df,ewmacd,ma1,ma2)
    sig=awesome_signal_generation(signals,awesome_ma)
    new=sig[slicer:]
    plot(new,ticker)
    portfo=portfolio(sig)
    profit(portfo)
    stats(portfo)

if __name__ == '__main__':
    main()