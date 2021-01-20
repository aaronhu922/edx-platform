import logging

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from django.conf import settings

# from .map_table_tmplate import reading_2_5, indexes_dict, reading_k_2, language_2_5, reading_language_2_5
from .reading_2_5_template import columns, reading_2_5_with_txt, reading_2_5_no_txt, reading_2_5_indexes

# from .models import MapStudentProfile, MapProfileExtResults, MapTestCheckItem

log = logging.getLogger("edx.pdfexam")


def draw_map_table(map_pro):
    phone_number = map_pro.phone_number
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

    table_len = len(reading_2_5_with_txt)

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=reading_2_5_with_txt, cellColours=None,
                         colLabels=columns, loc='center', cellLoc='center')
    # fig.set_size_inches(14, 30)
    fig.set_size_inches(14, 12)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(columns))))
    the_table.scale(1, 0.8)

    map_res = map_pro.map_ext_results.all()
    for index in reading_2_5_indexes.values():
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])
        the_table[(index[0], index[1] + 7)].set_facecolor(mcolors.CSS4_COLORS['lightgrey'])

    for i in range(table_len + 1):
        the_table[(i, 9)].visible_edges = "LR"

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level
        try:
            indexes = reading_2_5_indexes[item_name]
        except KeyError as err:
            log.info("Item {} is not exist in map test table, error is: {}".format(item_name, err))
        else:
            if item_level == "DEVELOP" or item_level == "REINFORCE_DEVELOP":
                the_table[(indexes[0], indexes[1])].set_facecolor(mcolors.CSS4_COLORS['red'])
            elif item_level == "REINFORCE":
                the_table[(indexes[0], indexes[1])].set_facecolor(mcolors.CSS4_COLORS['yellow'])
            else:
                the_table[(indexes[0], indexes[1])].set_facecolor(mcolors.CSS4_COLORS['green'])
            # log.info("Item {}'s index is {}, with level {}".format(item_name, indexes, item_level))

    file_path = settings.MEDIA_ROOT + phone_number + '_map.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url = settings.MEDIA_URL + phone_number + '.pdf'
    map_pro.save()
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url))
    ####Create table with out txt
    fig1, ax1 = plt.subplots()
    ax1.axis('tight')
    ax1.axis('off')
    cli_table = ax1.table(cellText=reading_2_5_no_txt, cellColours=None,
                         colLabels=columns, loc='center', cellLoc='center')
    # fig.set_size_inches(14, 30)
    fig1.set_size_inches(14, 12)
    cli_table.auto_set_font_size(False)
    cli_table.set_fontsize(9)
    cli_table.auto_set_column_width(col=list(range(len(columns))))
    cli_table.scale(1, 0.8)

    map_res = map_pro.map_ext_results.all()
    for index in reading_2_5_indexes.values():
        cli_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])
        cli_table[(index[0], index[1] + 7)].set_facecolor(mcolors.CSS4_COLORS['lightgrey'])

    for i in range(table_len + 1):
        cli_table[(i, 9)].visible_edges = "LR"

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level
        try:
            indexes = reading_2_5_indexes[item_name]
        except KeyError as err:
            log.info("Item {} is not exist in map test table, error is: {}".format(item_name, err))
        else:
            if item_level == "DEVELOP" or item_level == "REINFORCE_DEVELOP":
                cli_table[(indexes[0], indexes[1])].set_facecolor(mcolors.CSS4_COLORS['red'])
            elif item_level == "REINFORCE":
                cli_table[(indexes[0], indexes[1])].set_facecolor(mcolors.CSS4_COLORS['yellow'])
            else:
                cli_table[(indexes[0], indexes[1])].set_facecolor(mcolors.CSS4_COLORS['green'])
            # log.info("Item {}'s index is {}, with level {}".format(item_name, indexes, item_level))

    file_path = settings.MEDIA_ROOT + phone_number + '.pdf'
    plt.savefig(file_path, dpi=300)
    # map_pro.map_pdf_url = settings.MEDIA_URL + phone_number + '.pdf'
    # map_pro.save()
    plt.clf()
