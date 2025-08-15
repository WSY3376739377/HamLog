# -*- coding: utf-8 -*-
import sqlite3
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
    """添加一条QSO记录。成功返回True，失败则引发异常。"""
    if not values.get('call'):
        raise ValueError("对方呼号不能为空")
    conn = sqlite3.connect(DB_FILE)
    sql = '''INSERT INTO qso(call, mode, freq, power, datetime,
                             qth_prov, qth_city, rst_sent, rst_recv,
                             content, device, addtime)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?)'''
    try:
        conn.execute(sql, (
            values.get('call', '').upper(), values.get('mode', '').upper(), values.get('freq'),
            values.get('power'), values.get('datetime'),
            values.get('qth_prov', '').upper(), values.get('qth_city', '').upper(),
            values.get('rst_sent', '').upper(), values.get('rst_recv', '').upper(),
            values.get('content'), values.get('device', '').upper(), now_str()
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        raise e # 将异常传递给调用者
    finally:
        conn.close()

def delete_qso(rowid):
    """根据ID删除一条QSO记录"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute('DELETE FROM qso WHERE id=?', (rowid,))
    conn.commit()
    conn.close()

def update_qso_cell(rowid, col, new_val):
    """更新QSO记录的单个字段。成功返回True，失败则引发异常。"""
    conn = sqlite3.connect(DB_FILE)
    # 注意：这里的列名是UI传递过来的中文名，之后在UI层需要确保一致性
    col_map = {
        '呼号': 'call', '模式': 'mode', '频率': 'freq', '功率': 'power',
        '时间': 'datetime', 'QTH（省）': 'qth_prov', 'QTH（市）': 'qth_city',
        'rst发': 'rst_sent', 'rst收': 'rst_recv', '设备': 'device', '内容': 'content'
    }
    db_col = col_map.get(col)
    if not db_col:
        raise ValueError(f"无效的列名: {col}")

    if db_col in ('call', 'mode', 'qth_prov', 'qth_city', 'rst_sent', 'rst_recv', 'device'):
        new_val = new_val.upper()
    
    try:
        conn.execute(f'UPDATE qso SET {db_col}=? WHERE id=?', (new_val, rowid))
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
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
        cur.executemany(sql, records)
        conn.commit()
        return cur.rowcount
    except sqlite3.Error as e:
        conn.rollback()
        raise e # 将异常传递给调用者
    finally:
        conn.close()