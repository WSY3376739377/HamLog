# -*- coding: utf-8 -*-
from collections import Counter
import io

# 尝试导入matplotlib，如果失败则无法生成图表
try:
    import matplotlib.pyplot as plt
    # 设置matplotlib以支持中文显示
    plt.rcParams['font.sans-serif'] = ['SimHei'] # 使用黑体
    plt.rcParams['axes.unicode_minus'] = False   # 正常显示负号
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

def get_stats_by_mode(records):
    """
    按模式统计QSO数量。
    records: 从数据库查询到的记录元组列表。
    """
    # records中，模式(mode)在索引2的位置
    modes = [rec[2].upper() for rec in records if rec and len(rec) > 2 and rec[2]]
    return Counter(modes)

def create_mode_pie_chart(stats_counter):
    """
    根据统计计数器创建一个饼图 Figure 对象。
    """
    # 总是创建一个Figure对象，即使没有数据或matplotlib不可用
    fig, ax = plt.subplots(figsize=(6, 4))

    if not MATPLOTLIB_AVAILABLE:
        ax.text(0.5, 0.5, 'matplotlib 库未安装\n无法显示图表', ha='center', va='center')
        return fig
        
    if not stats_counter:
        ax.text(0.5, 0.5, '无可用数据', ha='center', va='center')
        return fig

    labels = stats_counter.keys()
    sizes = stats_counter.values()

    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10})
    ax.axis('equal')  # 确保饼图是圆的
    ax.set_title('按模式统计QSO数量', fontsize=14)
    
    return fig