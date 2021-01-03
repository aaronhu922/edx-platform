import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from django.conf import settings

from .map_table_tmplate import cell_text, columns, indexes_dict

plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


def draw_star_reading_table():
    table_len = len(cell_text)

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=cell_text, cellColours=None,
                         colLabels=columns, loc='center', cellLoc='center')

    for index in indexes_dict.values():
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['lightgrey'])
        the_table[(index[0], index[1] + 7)].set_facecolor(mcolors.CSS4_COLORS['lightgrey'])

    for i in range(table_len + 1):
        the_table[(i, 9)].visible_edges = "LR"

    the_table[(1, 3)].set_facecolor(mcolors.CSS4_COLORS['green'])
    the_table[(1, 10)].set_facecolor(mcolors.CSS4_COLORS['green'])

    fig.set_size_inches(14, 30)
    the_table.auto_set_font_size(True)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(columns))))
    the_table.scale(1, 0.24)
    file_path = settings.MEDIA_ROOT + 'star_reading_test.pdf'

    plt.savefig(file_path, dpi=300)
    plt.clf()
