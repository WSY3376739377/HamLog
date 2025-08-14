# -*- coding: utf-8 -*-
"""
HamLog – 业余无线电日志管理软件（无归属地查询）
作者：C盘研究所、𝕰𝖗𝖎𝖈
"""
import os
import datetime
import sqlite3
import threading
import time
import webbrowser
import PySimpleGUI as sg

VERSION = '1.0.0'
DB_FILE = 'hamlog.db'
CONFIG_FILE = 'config.txt'
GITHUB_REPO = 'https://github.com/WSY3376739377/HamLog'

# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS qso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call TEXT, mode TEXT, freq REAL, power REAL, datetime TEXT,
            qth_prov TEXT, qth_city TEXT, rst_sent TEXT, rst_recv TEXT,
            content TEXT, device TEXT, addtime TEXT
        )
    ''')
    conn.commit(); conn.close()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        import json
        with open(CONFIG_FILE, encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_config(cfg):
    import json
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def now_str():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

def get_beijing_time():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

def get_utc_time():
    return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

# ------------------------------------------------------------------
# 业务函数
# ------------------------------------------------------------------
def add_qso(values):
    if not values['call']:
        sg.popup('请填写对方呼号！'); return
    conn = sqlite3.connect(DB_FILE)
    sql = '''INSERT INTO qso(call, mode, freq, power, datetime,
                             qth_prov, qth_city, rst_sent, rst_recv,
                             content, device, addtime)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?)'''
    conn.execute(sql, (
        values['call'].upper(), values['mode'].upper(), values['freq'],
        values['power'], values['datetime'],
        values['qth_prov'].upper(), values['qth_city'].upper(),
        values['rst_sent'].upper(), values['rst_recv'].upper(),
        values['content'], values['device'].upper(), now_str()
    ))
    conn.commit(); conn.close(); sg.popup('已保存')

def delete_qso(rowid):
    conn = sqlite3.connect(DB_FILE)
    conn.execute('DELETE FROM qso WHERE id=?', (rowid,)); conn.commit(); conn.close()

def update_qso_cell(rowid, col, new_val):
    conn = sqlite3.connect(DB_FILE)
    if col in ('call', 'mode', 'qth_prov', 'qth_city', 'rst_sent', 'rst_recv', 'device'):
        new_val = new_val.upper()
    conn.execute(f'UPDATE qso SET {col}=? WHERE id=?', (new_val, rowid))
    conn.commit(); conn.close()

def query_qso(keyword, by='call'):
    conn = sqlite3.connect(DB_FILE)
    sql = f"SELECT * FROM qso WHERE UPPER({by}) LIKE ? ORDER BY datetime DESC"
    cur = conn.execute(sql, (f'%{keyword.upper()}%',))
    rows = cur.fetchall(); conn.close(); return rows

# ------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------
def main_window():
    init_db()
    cfg = load_config(); d = cfg.get('defaults', {})

    sg.theme('SystemDefaultForReal')

    add_tab = sg.Tab('增加日志', [
        [sg.Text('对方呼号*'), sg.Input(d.get('call', ''), key='call', size=15)],
        [sg.Text('模式'), sg.Combo(['SSB','CW','FT8','RTTY','AM','FM'],
                                   default_value=d.get('mode', ''), key='mode', readonly=False, size=12)],
        [sg.Text('频率(MHz)'), sg.Input(d.get('freq', ''), key='freq', size=12)],
        [sg.Text('功率(W)'), sg.Input(d.get('power', ''), key='power', size=12)],
        [sg.Button('当前时间'), sg.Input(now_str(), key='datetime', size=18)],
        [sg.Text('QTH 省'), sg.Input(d.get('qth_prov', ''), key='qth_prov', size=15)],
        [sg.Text('QTH 市'), sg.Input(d.get('qth_city', ''), key='qth_city', size=15)],
        [sg.Text('信号报告(发)'), sg.Input(d.get('rst_sent', ''), key='rst_sent', size=8)],
        [sg.Text('信号报告(收)'), sg.Input(d.get('rst_recv', ''), key='rst_recv', size=8)],
        [sg.Text('设备'), sg.Input(d.get('device', ''), key='device', size=20)],
        [sg.Text('内容')],
        [sg.Multiline(d.get('content', ''), key='content', size=(50, 5))],
        [sg.Button('保存'), sg.Button('清空')]
    ])

    query_tab = sg.Tab('查询日志', [
        [sg.Radio('呼号', 'by', True, key='by_call'), sg.Radio('频率', 'by', key='by_freq'),
         sg.Radio('功率', 'by', key='by_power'), sg.Radio('时间', 'by', key='by_time')],
        [sg.Input(key='keyword', size=20), sg.Button('查询')],
        [sg.Table([], ['id','呼号','模式','频率','功率','时间','省','市','发','收','设备','内容'],
                  key='table', auto_size_columns=False, col_widths=[4,8,6,8,6,16,8,8,4,4,8,20],
                  right_click_menu=['', ['删除','修改']], expand_x=True, expand_y=True)]
    ])

    settings_tab = sg.Tab('设置', [
        [sg.Frame('默认值', [
            [sg.Text('呼号'), sg.Input(d.get('call', ''), key='def_call', size=15)],
            [sg.Text('模式'), sg.Input(d.get('mode', ''), key='def_mode', size=15)],
            [sg.Text('频率'), sg.Input(d.get('freq', ''), key='def_freq', size=12)],
            [sg.Text('功率'), sg.Input(d.get('power', ''), key='def_power', size=12)],
            [sg.Text('省'), sg.Input(d.get('qth_prov', ''), key='def_qth_prov', size=12)],
            [sg.Text('市'), sg.Input(d.get('qth_city', ''), key='def_qth_city', size=12)],
            [sg.Text('设备'), sg.Input(d.get('device', ''), key='def_device', size=20)],
            [sg.Button('保存默认值')]
        ])],
        [sg.Frame('反馈/更新', [
            [sg.Button('邮箱'), sg.Button('GitHub'), sg.Button('QQ群'), sg.Button('检查更新')]
        ])]
    ])

    about_tab = sg.Tab('关于', [
        [sg.Text('HamLog 业余无线电日志管理软件', font=('Arial', 18))],
        [sg.Text(f'版本：{VERSION}')],
        [sg.Text('作者：C盘研究所、𝕰𝖗𝖎𝖈')]
    ])

    layout = [
        [sg.Text('HamLog 日志软件', font=('Arial', 18), text_color='blue'), sg.Push(),
         sg.Text('北京时间：'), sg.Text(get_beijing_time(), key='bj_time', size=20),
         sg.Text('UTC：'), sg.Text(get_utc_time(), key='utc_time', size=20)],
        [sg.Text('请确认系统时间准确', text_color='red')],
        [sg.TabGroup([[add_tab, query_tab, settings_tab, about_tab]], expand_x=True, expand_y=True)]
    ]

    window = sg.Window('HamLog', layout, resizable=True, size=(1000, 750), finalize=True)

    def time_update():
        while True:
            try:
                window.write_event_value('-TIME-', None)
                time.sleep(1)
            except Exception:
                break
    threading.Thread(target=time_update, daemon=True).start()

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        if event == '-TIME-':
            window['bj_time'].update(get_beijing_time())
            window['utc_time'].update(get_utc_time())
        if event == '当前时间':
            try:
                window['datetime'].update(now_str())
            except Exception as e:
                sg.popup(f'更新时间失败：{e}')
        if event == '保存':
            add_qso(values)
        if event == '清空':
            for k in ['call', 'freq', 'power', 'datetime', 'qth_prov', 'qth_city',
                      'rst_sent', 'rst_recv', 'content', 'device']:
                window[k].update('')
        if event == '查询':
            by = next(k for k in ['by_call', 'by_freq', 'by_power', 'by_time'] if values[k]).split('_')[1]
            rows = query_qso(values['keyword'], by)
            window['table'].update(values=rows)
        if event == '删除':
            idx = values['table']
            if idx:
                rowid = window['table'].Values[idx[0]][0]
                delete_qso(rowid)
                sg.popup('已删除')
                window.write_event_value('查询', None)
        if event == '修改':
            idx = values['table']
            if idx:
                rowid, *data = window['table'].Values[idx[0]]
                # 列名下拉
                col_list = ['呼号', '模式', '频率', '功率', '时间',
                            'QTH（省）', 'QTH（市）', 'rst发', 'rst收',
                            '设备', '内容']
                layout = [
                    [sg.Text('选择列'), sg.Combo(col_list, readonly=True, key='col')],
                    [sg.Text('新值'), sg.Multiline(key='val' , size=(15,10))],
                    [sg.Button('确定'), sg.Button('取消')]
                ]
                win = sg.Window('修改', layout, modal=True , size = (300,300))
                evt, vals = win.read(close=True)
                if evt == '确定' and vals['col']:
                    update_qso_cell(rowid, vals['col'], vals['val'])
                    sg.popup('已更新')
                    window.write_event_value('查询', None)
        if event == '保存默认值':
            cfg = load_config()
            cfg.setdefault('defaults', {}).update({
                'call': values['def_call'].upper(),
                'mode': values['def_mode'].upper(),
                'freq': values['def_freq'],
                'power': values['def_power'],
                'qth_prov': values['def_qth_prov'].upper(),
                'qth_city': values['def_qth_city'].upper(),
                'device': values['def_device'].upper()
            })
            save_config(cfg)
            sg.popup('已保存')
        if event == '邮箱':
            webbrowser.open('3376739377@qq.com')
        if event == 'GitHub':
            webbrowser.open(GITHUB_REPO)
        if event == 'QQ群':
            sg.popup('QQ群：959244571')
        if event == '检查更新':
            webbrowser.open(GITHUB_REPO + '/releases/latest')

    window.close()

if __name__ == '__main__':
    main_window()