import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
sql_pass = os.getenv("sql_pass")

db = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = sql_pass,
    database = "sim_mat"
)

cursor = db.cursor()

def search_drama(srch):
    sql = "SELECT title, id FROM drama WHERE title LIKE %s"
    pattern = f"%{srch}%"
    arg = (pattern,)
    cursor.execute(sql, arg)
    res = cursor.fetchall()
    if (len(res) < 5):
        return res
    return res[:5]

def upd_rec(uid, show):
    sim = "SELECT `rank`, sim_val, rank_id FROM cos_sim WHERE id=%s AND `rank`<=50"
    arg = (show,)
    cursor.execute(sim, arg)
    new_rec = cursor.fetchall()
    new_rec.sort()
    oldr = "SELECT `rank`, sim, id, tag FROM rec_list WHERE google_sub=%s"
    arg = (uid,)
    cursor.execute(oldr, arg)
    old_rec = cursor.fetchall()
    old_rec.sort()

    # Merge by similarity (higher first). Safe when new_rec or old_rec is empty
    # (old code indexed new_rec[pt_new] with pt_new < 50 even when new_rec was empty → IndexError → HTTP 500).
    opt_rec = []
    pt_old, pt_new = 0, 0
    while len(opt_rec) < 50 and (pt_old < len(old_rec) or pt_new < len(new_rec)):
        if pt_new >= len(new_rec):
            opt_rec.append(
                (len(opt_rec) + 1, old_rec[pt_old][1], old_rec[pt_old][2], old_rec[pt_old][3])
            )
            pt_old += 1
        elif pt_old >= len(old_rec):
            opt_rec.append((len(opt_rec) + 1, new_rec[pt_new][1], new_rec[pt_new][2], show))
            pt_new += 1
        elif old_rec[pt_old][1] >= new_rec[pt_new][1]:
            opt_rec.append(
                (len(opt_rec) + 1, old_rec[pt_old][1], old_rec[pt_old][2], old_rec[pt_old][3])
            )
            pt_old += 1
        else:
            opt_rec.append((len(opt_rec) + 1, new_rec[pt_new][1], new_rec[pt_new][2], show))
            pt_new += 1

    rem = "DELETE FROM rec_list WHERE google_sub=%s"
    cursor.execute(rem, arg)
    db.commit()
    ins = "INSERT INTO rec_list (`rank`, google_sub, sim, id, tag) VALUES (%s, %s, %s, %s, %s)"
    full_push = []
    for x in opt_rec:
        full_push.append((x[0], uid, x[1], x[2], x[3]))
    cursor.executemany(ins, full_push)
    db.commit()

def rem_watch(uid, show):
    qry = "DELETE FROM rec_list WHERE google_sub=%s AND tag=%s"
    arg = (uid, show)
    cursor.execute(qry, arg)
    db.commit()
    qry = "DELETE FROM watch_list WHERE google_sub=%s AND id=%s"
    cursor.execute(qry, arg)
    db.commit()
    return display(uid)

def _dramas_for_ids(id_list):
    if not id_list:
        return []
    placeholders = ",".join(["%s"] * len(id_list))
    cursor.execute(
        f"SELECT id, title, pic_url FROM drama WHERE id IN ({placeholders})",
        tuple(id_list),
    )
    rows = {r[0]: r for r in cursor.fetchall()}
    return [rows[i] for i in id_list if i in rows]


def display(uid):
    watch_items = "SELECT id FROM watch_list WHERE google_sub=%s"
    arg = (uid,)
    cursor.execute(watch_items, arg)
    res1 = cursor.fetchall()
    if len(res1) == 0:
        qry = "DELETE FROM rec_list"
        cursor.execute(qry)
    rec_items = (
        "SELECT id FROM rec_list WHERE google_sub=%s AND `rank`<=1000 ORDER BY `rank`"
    )
    cursor.execute(rec_items, arg)
    res2 = cursor.fetchall()
    watch_ids = [x[0] for x in res1]
    search_watch = set(watch_ids)
    rec_ids = [x[0] for x in res2]
    good_rec = []
    seen_rec = set()
    for rid in rec_ids:
        if rid in search_watch or rid in seen_rec:
            continue
        seen_rec.add(rid)
        good_rec.append(rid)
        if len(good_rec) >= 50:
            break
    comp_one = _dramas_for_ids(watch_ids)
    comp_two = _dramas_for_ids(good_rec)
    return [comp_one, comp_two]

def add_watch(uid, show):
    sql = "INSERT INTO watch_list (google_sub, id) VALUES (%s, %s)"
    val = (uid, show)
    cursor.execute(sql, val)
    db.commit()
    upd_rec(uid, show)
    return display(uid)


def make_user(uid, avt):
    sql = "INSERT INTO app_user (google_sub, avatar_url, wl_sz) VALUES (%s, %s, %s)"
    arg = (uid, avt, 0)
    cursor.execute(sql, arg)
    db.commit()


def user_exists(uid):
    cursor.execute("SELECT 1 FROM app_user WHERE google_sub=%s LIMIT 1", (uid,))
    return cursor.fetchone() is not None
