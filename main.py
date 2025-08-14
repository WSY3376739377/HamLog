# -*- coding: utf-8 -*-
"""
HamLog – 业余无线电日志管理软件（无归属地查询）
作者：C盘研究所、BG5JQN
"""
import os
import shutil
import threading
import time
import webbrowser
import PySimpleGUI as sg

# 导入重构后的模块
from modules.database import init_db, add_qso, delete_qso, update_qso_cell, query_qso, add_qso_batch
from modules.helpers import now_str, get_beijing_time, get_utc_time
from modules.config import load_config, save_config
from modules import adif

from modules import statistics

VERSION = '1.0.0'
GITHUB_REPO = 'https://github.com/WSY3376739377/HamLog'

# ------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------
def main_window():
    init_db()
    cfg = load_config()
    d = cfg.get('defaults', {})

    # 应用保存的主题，如果未设置则使用默认值
    theme = cfg.get('theme', 'SystemDefaultForReal')
    sg.theme(theme)

    add_tab = sg.Tab('增加日志', [
        [sg.Text('对方呼号*'), sg.Input(d.get('call', ''), key='call', size=15)],
        [sg.Text('模式'), sg.Combo(['SSB','CW','FT8','RTTY','AM','FM'],
                                   default_value=d.get('mode', ''), key='mode', readonly=False, size=12)],
        [sg.Text('频率(MHz)'), sg.Input(d.get('freq', ''), key='freq', size=12)],
        [sg.Text('功率(W)'), sg.Input(d.get('power', ''), key='power', size=12)],
        [sg.Text('日期时间'), sg.Input(now_str(), key='datetime', size=18),
         sg.CalendarButton('选择日期', target='datetime', format='%Y-%m-%d %H:%M'),
         sg.Button('设为当前时间')],
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
        [sg.Frame('数据操作', [
            [sg.Button('恢复数据库', button_color=('white', 'red')), sg.Button('备份数据库'), sg.Button('从 ADIF 导入'), sg.Button('导出为 ADIF')]
        ])],
        [sg.Frame('外观设置', [
            [sg.Text('界面主题'), sg.Combo(sg.theme_list(), default_value=theme, key='-THEME-'), sg.Button('应用主题')]
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

    stats_tab = sg.Tab('统计', [
        [sg.Text('日志统计', font=('Arial', 16))],
        [sg.Button('刷新统计数据', key='-REFRESH_STATS-')],
        [sg.Image(key='-STATS_IMAGE-', size=(600, 400))]
    ], key='-STATS_TAB-')

    layout = [
        [sg.Text('HamLog 日志软件', font=('Arial', 18), text_color='blue'), sg.Push(),
         sg.Text('北京时间：'), sg.Text(get_beijing_time(), key='bj_time', size=20),
         sg.Text('UTC：'), sg.Text(get_utc_time(), key='utc_time', size=20)],
        [sg.Text('请确认系统时间准确', text_color='red')],
        [sg.TabGroup([[add_tab, query_tab, stats_tab, settings_tab, about_tab]], expand_x=True, expand_y=True, enable_events=True, key='-TABGROUP-')]
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
        if event == '设为当前时间':
            window['datetime'].update(now_str())
        if event == '保存':
            # --- 输入验证 ---
            try:
                if values['freq']: float(values['freq'])
                if values['power']: float(values['power'])
            except ValueError:
                sg.popup_error('输入错误', '频率和功率必须为数字！')
                continue # 中断此次保存操作

            if add_qso(values):
                sg.popup('已保存')
                # 保存成功后清空非默认值的字段
                cfg = load_config()
                d = cfg.get('defaults', {})
                for k in ['call', 'freq', 'power', 'qth_prov', 'qth_city', 'rst_sent', 'rst_recv', 'content', 'device']:
                    if k not in d: # 如果该字段没有设置默认值，则清空
                        window[k].update('')
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
                try:
                    rowid = window['table'].Values[idx[0]][0]
                    delete_qso(rowid)
                    sg.popup('已删除')
                    window.write_event_value('查询', None) # 重新触发查询以刷新列表
                except IndexError:
                    sg.popup_error('请在表格中选择要删除的行！')
                except Exception as e:
                    sg.popup_error(f'删除失败: {e}')
        if event == '修改':
            if not values['table']:
                sg.popup_error('请先在表格中选择要修改的行！')
                continue
            try:
                row_idx = values['table'][0]
                row_data = window['table'].Values[row_idx]
                rowid = row_data[0]

                col_map = {
                    '呼号': 1, '模式': 2, '频率': 3, '功率': 4, '时间': 5,
                    'QTH（省）': 6, 'QTH（市）': 7, 'rst发': 8, 'rst收': 9,
                    '设备': 10, '内容': 11
                }
                col_list = list(col_map.keys())

                edit_layout = [
                    [sg.Text('选择要编辑的字段:')],
                    [sg.Combo(col_list, readonly=True, key='-COL-', enable_events=True)],
                    [sg.Text('当前值:')],
                    [sg.Multiline(size=(40, 5), key='-VAL-')],
                    [sg.Button('确定'), sg.Button('取消')]
                ]
                edit_window = sg.Window('修改条目', edit_layout, modal=True, finalize=True)

                while True:
                    win_event, win_values = edit_window.read()
                    if win_event in (sg.WIN_CLOSED, '取消'):
                        break
                    if win_event == '-COL-':
                        selected_col_name = win_values['-COL-']
                        col_index = col_map[selected_col_name]
                        current_value = row_data[col_index]
                        edit_window['-VAL-'].update(current_value)
                    if win_event == '确定':
                        selected_col = win_values['-COL-']
                        new_value = win_values['-VAL-']
                        if selected_col:
                            update_qso_cell(rowid, selected_col, new_value)
                            sg.popup('已更新')
                            window.write_event_value('查询', None)
                        break
                edit_window.close()

            except Exception as e:
                sg.popup_error(f'修改操作失败: {e}')
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
            if save_config(cfg):
                sg.popup('默认值已保存')
        if event == '邮箱':
            webbrowser.open('3376739377@qq.com')
        if event == 'GitHub':
            webbrowser.open(GITHUB_REPO)
        if event == 'QQ群':
            sg.popup('QQ群：959244571')
        if event == '检查更新':
            webbrowser.open(GITHUB_REPO + '/releases/latest')
        if event == '导出为 ADIF':
            filepath = sg.popup_get_file('保存为 ADIF 文件', save_as=True, file_types=(("ADIF Files", "*.adi"),))
            if filepath:
                records = query_qso() # 获取所有记录
                if adif.export_to_adif(records, filepath):
                    sg.popup('成功', f'日志已成功导出到:\n{filepath}')
                else:
                    sg.popup_error('导出失败', '无法写入文件，请检查权限或路径。')
        if event == '从 ADIF 导入':
            filepath = sg.popup_get_file('选择要导入的 ADIF 文件', file_types=(("ADIF Files", "*.adi"), ("All Files", "*.*")))
            if filepath:
                qso_to_add = adif.import_from_adif(filepath)
                if qso_to_add:
                    inserted_count = add_qso_batch(qso_to_add)
                    sg.popup('导入完成', f'成功导入 {inserted_count} / {len(qso_to_add)} 条记录。')
                    window.write_event_value('查询', None) # 刷新表格
                else:
                    sg.popup('导入结束', '没有找到可导入的有效记录。')
        
        if event == '-TABGROUP-' and values['-TABGROUP-'] == '-STATS_TAB-':
            # 当切换到统计选项卡时，自动刷新
            window.write_event_value('-REFRESH_STATS-', None)

        if event == '-REFRESH_STATS-':
            if statistics.MATPLOTLIB_AVAILABLE:
                records = query_qso()
                stats_counter = statistics.get_stats_by_mode(records)
                chart_data = statistics.create_mode_pie_chart(stats_counter)
                if chart_data:
                    window['-STATS_IMAGE-'].update(data=chart_data)
                else:
                    window['-STATS_IMAGE-'].update(data=None)
            else:
                window['-STATS_IMAGE-'].update(data=None)

        if event == '应用主题':
            new_theme = values['-THEME-']
            cfg = load_config()
            cfg['theme'] = new_theme
            save_config(cfg)
            sg.popup('主题已保存', '请重新启动程序以应用新主题。')

        if event == '备份数据库':
            source_db = 'hamlog.db'
            if not os.path.exists(source_db):
                sg.popup_error('错误', '数据库文件 hamlog.db 不存在，无法备份。')
                continue

            backup_filename = f"hamlog_backup_{time.strftime('%Y%m%d_%H%M%S')}.db"
            filepath = sg.popup_get_file(
                '保存数据库备份',
                save_as=True,
                default_path=backup_filename,
                file_types=(("SQLite Database", "*.db"),)
            )
            
            if filepath:
                try:
                    shutil.copy(source_db, filepath)
                    sg.popup('备份成功', f'数据库已成功备份到:\n{filepath}')
                except Exception as e:
                    sg.popup_error(f'备份失败', f'发生错误: {e}')

        if event == '恢复数据库':
            confirm = sg.popup_yes_no(
                '警告：此操作将用备份文件覆盖当前数据库。\n所有未备份的数据都将丢失！\n\n您确定要继续吗？',
                title='确认恢复',
                button_color=('white', 'red')
            )
            if confirm == 'Yes':
                filepath = sg.popup_get_file(
                    '选择要恢复的数据库备份文件',
                    file_types=(("SQLite Database", "*.db"), ("All Files", "*.*"))
                )
                if filepath and os.path.exists(filepath):
                    try:
                        # 在恢复前，最好先关闭当前窗口/数据库连接，但这会使程序复杂化
                        # 简单的做法是直接覆盖文件，并提示用户重启
                        shutil.copy(filepath, 'hamlog.db')
                        sg.popup('恢复成功', '数据库已恢复。\n请立即重启程序以加载新数据。')
                    except Exception as e:
                        sg.popup_error('恢复失败', f'发生错误: {e}')


    window.close()

if __name__ == '__main__':
    main_window()