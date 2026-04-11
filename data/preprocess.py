import ast
import os
from pathlib import Path

import mysql.connector
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
sql_pass = os.getenv("sql_pass")
data_path = os.getenv("data_path")

if not sql_pass:
    raise SystemExit("Missing sql_pass in project .env")
if not data_path or not Path(data_path).is_file():
    raise SystemExit(f"Missing or invalid data_path in .env: {data_path!r}")


def cleanse(x):
    if pd.isna(x):
        return []
    if isinstance(x, (list, tuple)):
        return list(x)
    if not isinstance(x, str):
        return []
    s = x.strip()
    if not s:
        return []
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return []


def stringify(x):
    return [str.lower(i.replace(" ", "")) for i in x]


def soupify(x):
    return (
        " ".join(x["Genres"])
        + " "
        + " ".join(x["Tags"])
        + " "
        + " ".join(x["Director"])
        + " "
        + " ".join(x["Screenwriter"])
        + " "
        + " ".join(x["Actors"])
    )


df = pd.read_csv(data_path)
n = len(df)
if n == 0:
    raise SystemExit("CSV has no rows")

feat = df.columns
print(feat)

for col in feat:
    if col == "Title":
        continue
    df[col] = df[col].apply(cleanse)
    if col == "url":
        continue
    df[col] = df[col].apply(stringify)

df["soup"] = df.apply(soupify, axis=1)

count = CountVectorizer(stop_words="english")
count_matrix = count.fit_transform(df["soup"])
sim = cosine_similarity(count_matrix, count_matrix)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=sql_pass,
    database="sim_mat",
)

cursor = db.cursor()
sql_cos = (
    "INSERT INTO cos_sim (id, `rank`, sim_val, rank_id) VALUES (%s, %s, %s, %s)"
)
ins_drama = "INSERT INTO drama (id, title, pic_url) VALUES (%s, %s, %s)"

# drama rows: id 1..n aligned with dataframe row order
full_push = []
for i in range(n):
    urls = df["url"].iloc[i]
    pic = urls[0] if isinstance(urls, list) and len(urls) > 0 else ""
    if not pic:
        raise SystemExit(f"Row {i}: missing url after parsing")
    title = df["Title"].iloc[i]
    if pd.isna(title):
        title = ""
    full_push.append((i + 1, str(title), str(pic)))

cursor.executemany(ins_drama, full_push)
db.commit()

# Top-50 neighbors per drama (exclude self). argpartition avoids full sort per row.
bsz = 5000
batch = []

for i in range(n):
    k_nei = 50
    row = np.asarray(sim[i], dtype=np.float64).copy()
    # Mask self so it never appears among top-k (cosine is in [-1, 1])
    row[i] = -2.0
    top_idx = np.argpartition(-row, k_nei - 1)[:k_nei]
    top_idx = top_idx[np.argsort(-row[top_idx])]
    for rank, j in enumerate(top_idx, start=1):
        batch.append((i + 1, rank, float(sim[i, j]), int(j) + 1))
    if len(batch) >= bsz:
        cursor.executemany(sql_cos, batch)
        db.commit()
        batch.clear()

if batch:
    cursor.executemany(sql_cos, batch)
    db.commit()

cursor.close()
db.close()
print("done")
