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
    arg = (show, )
    cursor.execute(sim, arg)
    new_rec = cursor.fetchall()
    new_rec.sort()
    oldr = "SELECT `rank`, sim, id, tag FROM rec_list WHERE google_sub=%s"
    arg = (uid, )
    cursor.execute(oldr, arg)
    old_rec = cursor.fetchall()
    old_rec.sort()
    pt_new = 0
    pt_old = 0
    opt_rec = []
    t = 1
    while pt_old < len(old_rec) and pt_new < 50:
        if old_rec[pt_old][1] >= new_rec[pt_new][1]:
            opt_rec.append((t, old_rec[pt_old][1], old_rec[pt_old][2], old_rec[pt_old][3]))
            pt_old += 1
        else:
            opt_rec.append((t, new_rec[pt_new][1], new_rec[pt_new][2], show))
            pt_new += 1
        t += 1
    while pt_old < len(old_rec):
        opt_rec.append((t, old_rec[pt_old][1], old_rec[pt_old][2], old_rec[pt_old][3]))
        t += 1
    while pt_new < 50:
        opt_rec.append((t, new_rec[pt_new][1], new_rec[pt_new][2], show))
        t += 1
    rem = "DELETE FROM rec_list WHERE google_sub=%s"
    cursor.execute(rem, arg)
    db.commit()
    ins = "INSERT INTO rec_list (`rank`, google_sub, sim, id, tag) VALUES (%s, %s, %s, %s, %s)"
    full_push = []
    for x in opt_rec:
        full_push.append((x[0], uid, x[1], x[2], x[3]))
    cursor.executemany(ins, full_push)
    db.commit()

def rem_rec(uid, show):
    qry = "DELETE FROM rec_list WHERE google_sub=%s AND tag=%s"
    arg = (uid, show)
    cursor.execute(qry, arg)
    db.commit()

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
    rec_items = "SELECT id FROM rec_list WHERE google_sub=%s AND `rank`<=50 ORDER BY `rank`"
    cursor.execute(rec_items, arg)
    res2 = cursor.fetchall()
    watch_ids = [x[0] for x in res1]
    rec_ids = [x[0] for x in res2]
    comp_one = _dramas_for_ids(watch_ids)
    comp_two = _dramas_for_ids(rec_ids)
    return [comp_one, comp_two]

def add_watch(uid, show):
    sql = "INSERT INTO watch_list (google_sub, id) VALUES (%s, %s)"
    val = (uid, show)
    cursor.execute(sql, val)
    db.commit()
    upd_rec(uid, show)
    return display(uid)


def rem_watch(uid, show):
    sql = "DELETE FROM watch_list WHERE google_sub=%s AND id=%s"
    arg = (uid, show)
    cursor.execute(sql, arg)
    db.commit()
    rem_rec(uid, show)
    return display(uid)


def make_user(uid, avt):
    sql = "INSERT INTO app_user (google_sub, avatar_url, wl_sz) VALUES (%s, %s, %s)"
    arg = (uid, avt, 0)
    cursor.execute(sql, arg)
    db.commit()


def user_exists(uid):
    cursor.execute("SELECT 1 FROM app_user WHERE google_sub=%s LIMIT 1", (uid,))
    return cursor.fetchone() is not None
