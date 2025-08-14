# -*- coding: utf-8 -*-
import sqlite3
import PySimpleGUI as sg
from modules.helpers import now_str

DB_FILE = 'hamlog.db'

def init_db():
    """初始化数据库，创建 qso 表"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS qso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call TEXT, mode TEXT, freq REAL, power REAL, datetime TEXT,
            qth_prov TEXT, qth_city TEXT, rst_sent TEXT, rst_recv TEXT,
            content TEXT, device TEXT, addtime TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_qso(values):
    """添加一条QSO记录"""
    if not values['call']:
        sg.popup('请填写对方呼号！')
        return False
    conn = sqlite3.connect(DB_FILE)
    sql = '''INSERT INTO qso(call, mode, freq, power, datetime,
                             qth_prov, qth_city, rst_sent, rst_recv,
                             content, device, addtime)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?)'''
    try:
        conn.execute(sql, (
            values['call'].upper(), values['mode'].upper(), values['freq'],
            values['power'], values['datetime'],
            values['qth_prov'].upper(), values['qth_city'].upper(),
            values['rst_sent'].upper(), values['rst_recv'].upper(),
            values['content'], values['device'].upper(), now_str()
        ))
        conn.commit()
        return True
    except Exception as e:
        sg.popup(f'保存失败: {e}')
        return False
    finally:
        conn.close()

def delete_qso(rowid):
    """根据ID删除一条QSO记录"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute('DELETE FROM qso WHERE id=?', (rowid,))
    conn.commit()
    conn.close()

def update_qso_cell(rowid, col, new_val):
    """更新QSO记录的单个字段"""
    conn = sqlite3.connect(DB_FILE)
    col_map = {
        '呼号': 'call', '模式': 'mode', '频率': 'freq', '功率': 'power',
        '时间': 'datetime', 'QTH（省）': 'qth_prov', 'QTH（市）': 'qth_city',
        'rst发': 'rst_sent', 'rst收': 'rst_recv', '设备': 'device', '内容': 'content'
    }
    db_col = col_map.get(col)
    if not db_col:
        sg.popup(f'无效的列名: {col}')
        return

    if db_col in ('call', 'mode', 'qth_prov', 'qth_city', 'rst_sent', 'rst_recv', 'device'):
        new_val = new_val.upper()
    
    conn.execute(f'UPDATE qso SET {db_col}=? WHERE id=?', (new_val, rowid))
    conn.commit()
    conn.close()

def query_qso(keyword="", by='call'):
    """
    查询QSO记录。
    如果 keyword 为空，则返回所有记录。
    """
    conn = sqlite3.connect(DB_FILE)
    by_map = {
        'call': 'call', 'freq': 'freq', 'power': 'power', 'time': 'datetime'
    }
    db_by = by_map.get(by, 'call')
    
    base_sql = "SELECT id, call, mode, freq, power, datetime, qth_prov, qth_city, rst_sent, rst_recv, device, content FROM qso"
    
    if keyword:
        sql = f"{base_sql} WHERE UPPER({db_by}) LIKE ? ORDER BY datetime DESC"
        params = (f'%{keyword.upper()}%',)
    else:
        sql = f"{base_sql} ORDER BY datetime DESC"
        params = ()
        
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def add_qso_batch(records):
    """
    批量插入QSO记录。
    records: 一个包含多个QSO元组的列表。
    返回成功插入的记录数。
    """
    if not records:
        return 0
    
    conn = sqlite3.connect(DB_FILE)
    sql = '''INSERT INTO qso(call, mode, freq, power, datetime,
                             qth_prov, qth_city, rst_sent, rst_recv,
                             content, device, addtime)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?)'''
    try:
        cur = conn.cursor()
        # 我们假设导入的数据都是可信的，不在此处做过多校验
        cur.executemany(sql, records)
        conn.commit()
        return cur.rowcount
    except sqlite3.Error as e:
        sg.popup_error(f"数据库批量插入失败: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()