import pandas as pd

df = pd.read_parquet('combined/features_long.parquet', columns=['symbol'])
syms = pd.Series(df['symbol'].unique())
print('Total unique symbols found:', len(syms))
print('Sample symbols:', syms.head(20).tolist())
# check if symbols contain dot or underscore
dots = syms.str.contains('\.') .sum()
unders = syms.str.contains('_').sum()
print('Symbols containing dot:', dots)
print('Symbols containing underscore:', unders)
