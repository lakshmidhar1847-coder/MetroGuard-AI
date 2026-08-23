import pandas as pd

df = pd.read_csv('data/processed/metropt3_features.csv', usecols=['timestamp', 'target'])
df['timestamp'] = pd.to_datetime(df['timestamp'])

n = len(df)
train_end_idx = int(n * 0.8)

train_df = df.iloc[:train_end_idx]
test_df = df.iloc[train_end_idx:]

print("=" * 75)
print("1. NAIVE 80/20 CHRONOLOGICAL SPLIT ANALYSIS")
print("=" * 75)
t_min_train = train_df['timestamp'].min()
t_max_train = train_df['timestamp'].max()
t_pos_train = int((train_df['target'] == 1).sum())
t_neg_train = int((train_df['target'] == 0).sum())

t_min_test = test_df['timestamp'].min()
t_max_test = test_df['timestamp'].max()
t_pos_test = int((test_df['target'] == 1).sum())
t_neg_test = int((test_df['target'] == 0).sum())

print(f"Train Span        : {t_min_train} to {t_max_train}")
print(f"Train Records     : {len(train_df):,} rows")
print(f"  - Positive (1)  : {t_pos_train:,} (100.0% of all positives)")
print(f"  - Negative (0)  : {t_neg_train:,}")
print(f"Test Span         : {t_min_test} to {t_max_test}")
print(f"Test Records      : {len(test_df):,} rows")
print(f"  - Positive (1)  : {t_pos_test:,} (0.0% of all positives - NO FAILURE IN TEST SET!)")
print(f"  - Negative (0)  : {t_neg_test:,}")

print("\n" + "=" * 75)
print("2. RECOMMENDED EVENT-ALIGNED CHRONOLOGICAL SPLIT")
print("=" * 75)
# Split point: July 1, 2020 (Event 1, 2, 3 in Train/Val, Event 4 in Test)
split_test_t = pd.Timestamp('2020-07-01 00:00:00')
train_val_df = df[df['timestamp'] < split_test_t]
test_rec = df[df['timestamp'] >= split_test_t]

# Inner Val Split: June 1, 2020 (Events 1 & 2 in Train, Event 3 in Val)
split_val_t = pd.Timestamp('2020-06-01 00:00:00')
train_sub = train_val_df[train_val_df['timestamp'] < split_val_t]
val_rec = train_val_df[train_val_df['timestamp'] >= split_val_t]

print(f"Training Set   ({train_sub['timestamp'].min().strftime('%Y-%m-%d')} to {train_sub['timestamp'].max().strftime('%Y-%m-%d')}):")
print(f"  - Total Rows    : {len(train_sub):,}")
print(f"  - Positives     : {int((train_sub['target']==1).sum()):,} (Events #1 & #2)")
print(f"  - Negatives     : {int((train_sub['target']==0).sum()):,}")

print(f"\nValidation Set ({val_rec['timestamp'].min().strftime('%Y-%m-%d')} to {val_rec['timestamp'].max().strftime('%Y-%m-%d')}):")
print(f"  - Total Rows    : {len(val_rec):,}")
print(f"  - Positives     : {int((val_rec['target']==1).sum()):,} (Event #3)")
print(f"  - Negatives     : {int((val_rec['target']==0).sum()):,}")

print(f"\nTest Set       ({test_rec['timestamp'].min().strftime('%Y-%m-%d')} to {test_rec['timestamp'].max().strftime('%Y-%m-%d')}):")
print(f"  - Total Rows    : {len(test_rec):,}")
print(f"  - Positives     : {int((test_rec['target']==1).sum()):,} (Event #4 + August holdout)")
print(f"  - Negatives     : {int((test_rec['target']==0).sum()):,}")
