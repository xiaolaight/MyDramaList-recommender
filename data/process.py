import ast
import pandas as pd
import mysql.connector
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import os

load_dotenv()
sql_pass = os.getenv("sql_pass")

def cleanse(x):
    try:
        return ast.literal_eval(x)
    except:
        return []

def stringify(x):
    return [str.lower(i.replace(" ", "")) for i in x]

def soupify(x):
    return ' '.join(x["Genres"]) + " " + ' '.join(x["Tags"]) + " " + ' '.join(x["Director"]) + " " + ' '.join(x["Screenwriter"]) + " " + ' '.join(x["Actors"])

data_path = os.getenv("data_path")
df = pd.read_csv(data_path)
feat = df.columns
print(feat)

for x in feat:
    if x == "Title":
        continue
    df[x] = df[x].apply(cleanse)
    df[x] = df[x].apply(stringify)

df["soup"] = df.apply(soupify, axis=1)

count = CountVectorizer(stop_words='english')
count_matrix = count.fit_transform(df['soup'])
sim = cosine_similarity(count_matrix, count_matrix)

db = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = sql_pass,
    database = "sim_mat"
)

cursor = db.cursor()
sql = "INSERT INTO cos_sim (row_index, col_index, sim_val) VALUES (%s, %s, %s)"

bsz = 25000
batch = []

for i in range(5000):
    for j in range(5000):
        val = float(sim[i, j])

        batch.append((i, j, val))

        if len(batch) == bsz:
            cursor.executemany(sql, batch)
            db.commit()
            batch.clear()

print("done")
