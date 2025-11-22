assert df.index.is_unique
# check weekend/holiday pattern
missing = pd.bdate_range(df.index.min(), df.index.max()).difference(df.index)
len(missing), missing[:5]
