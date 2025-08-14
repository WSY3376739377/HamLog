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
    根据统计计数器创建一个饼图。
    返回PNG格式的图像字节数据。
    """
    if not MATPLOTLIB_AVAILABLE or not stats_counter:
        return None

    labels = stats_counter.keys()
    sizes = stats_counter.values()

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10})
    ax.axis('equal')  # 确保饼图是圆的
    ax.set_title('按模式统计QSO数量', fontsize=14)
    
    # 将图表绘制到内存缓冲区
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig) # 关闭图形，释放内存
    buf.seek(0)
    
    return buf.read()