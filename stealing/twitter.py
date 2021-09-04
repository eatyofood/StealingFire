
def show_tweets(TICKER,rm_rt=False):
    indi = []
    for i in range(len(tdf)):
        for t in tdf['hash'][i]:
            if t == TICKER.upper():
                
                indi.append(tdf.index[i])
    # Define Isolated Data Frame
    stdf = tdf.T[indi].T
    
    if (rm_rt == True) & ( len(stdf) > 0 ):
        badli = []
        for i in trange(len(stdf)):
            
            if "RT" in stdf['Text'][i].upper() :
                print(f'retweet in: {stdf.index[i]}')
                badli.append(stdf.index[i])
        stdf = stdf.drop(badli,axis=0)
    
    return stdf
