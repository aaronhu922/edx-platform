import logging

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from django.conf import settings

from .reading_2_5_template import short_columns, reading_2_5_no_txt, reading_2_5_indexes, \
    reading_2_5_cells_color, reading_2_5_items_name
from .map_table_tmplate import all_map_indexes_dict, all_map_cell_text, all_cells_no_text
from .reading_k_2_template import reading_k_2_indexes, reading_k_2_cell_no_text, reading_k_2_cells_color, \
    reading_k_2_items_array
from .lanuage_2_12_template import language_2_12_indexes, language_2_12_simple_no_txt, map_2_12_columns, \
    language_2_12_cells_color, language_2_12_items_array
from .map_2_12_table_template import map_2_12_simple_table, map_2_12_table, map_2_12_table_indexes

# from .models import MapStudentProfile, MapProfileExtResults, MapTestCheckItem

log = logging.getLogger("edx.pdfexam")
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


def draw_map_table(map_pro):
    log.info("Start to drawing map table!")
    if map_pro.Growth.startswith('Reading 2-5'):
        colors_dict = create_table_colors_dict(map_pro, reading_2_5_items_name, reading_2_5_cells_color)
        draw_reading_2_5_map_table(map_pro, colors_dict)
        draw_reading_2_5_in_all_table(map_pro, colors_dict)
        draw_reading_2_5_no_txt_all_table(map_pro, colors_dict)
        log.info("Map report type is {}, drew pdfs for report.".format(map_pro.Growth))
    elif map_pro.Growth.startswith('Reading K-2'):
        colors_dict = create_table_colors_dict(map_pro, reading_k_2_items_array, reading_k_2_cells_color)
        draw_reading_k_2_simple_map_table(map_pro, colors_dict)
        draw_reading_k_2_in_all_table(map_pro, colors_dict)
        draw_reading_k_2_no_txt_all_table(map_pro, colors_dict)
        log.info("Map report type is {}, drew pdfs for report.".format(map_pro.Growth))
    elif map_pro.Growth.startswith('Language'):
        colors_dict = create_table_colors_dict(map_pro, language_2_12_items_array, language_2_12_cells_color)
        draw_language_2_12_simple_map_table(map_pro, colors_dict)
        draw_language_2_12_in_all_table(map_pro, colors_dict)
        draw_language_2_12_no_txt_all_table(map_pro, colors_dict)
        log.info("Map report type is {}, drew pdfs for report.".format(map_pro.Growth))
    else:
        log.info("Wrong map type {}".format(map_pro.Growth))
        pass

    map_pro.save()


def draw_reading_2_5_map_table(map_pro, colors_dict):
    phone_number = map_pro.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=reading_2_5_no_txt, cellColours=None,
                         colLabels=short_columns, loc='center', cellLoc='center')
    # fig.set_size_inches(14, 30)
    fig.set_size_inches(10, 12)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(short_columns))))
    the_table.scale(1, 0.85)

    set_color_for_table(colors_dict, the_table, reading_2_5_indexes)

    file_path = settings.MEDIA_ROOT + phone_number + '.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url = settings.MEDIA_URL + phone_number + '.pdf'

    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url))
    plt.clf()


def set_color_for_table(colors_dict, the_table, table_indexes):
    for name, color in colors_dict.items():
        try:
            indexes = table_indexes[name]
        except KeyError as err:
            log.info("Item {} is not exist in map test table, error is: {}".format(name, err))
        else:
            # log.info("item {}'s color is {}, index is {}".format(name, color, indexes))
            if color == 0:
                the_table[indexes].set_facecolor(mcolors.CSS4_COLORS['limegreen'])
            elif color == 1:
                the_table[indexes].set_facecolor(mcolors.CSS4_COLORS['yellow'])
            else:
                the_table[indexes].set_facecolor(mcolors.CSS4_COLORS['red'])


def create_table_colors_dict(map_pro, ccss_items_template, colors_dict_template):
    map_res = map_pro.map_ext_results.all()
    colors_dict = colors_dict_template.copy()
    # log.info("map file {}'s init color is {}".format(map_pro.Growth, colors_dict))
    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level

        if item_level == "DEVELOP" or item_level == "REINFORCE_DEVELOP":
            colors_dict[item_name] = 2
        elif item_level == "REINFORCE":
            colors_dict[item_name] = 1
    for item in ccss_items_template:
        i = 0
        green_back = True
        while i < len(item):
            if green_back and colors_dict[item[i]] == 0:
                i += 1
            else:
                green_back = False
                if colors_dict[item[i]] == 0:
                    colors_dict[item[i]] = 2
                i += 1
    # log.info("map file {}'s color index after filling green is {}".format(map_pro.Growth, colors_dict))
    return colors_dict


def draw_reading_2_5_in_all_table(map_pro, colors_dict):
    phone_number = map_pro.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=all_map_cell_text, cellColours=None,
                         colLabels=short_columns, loc='center', cellLoc='center')
    fig.set_size_inches(12, 30)
    # fig.set_size_inches(10, 12)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(short_columns))))
    the_table.scale(1, 0.24)

    set_color_for_table(colors_dict, the_table, all_map_indexes_dict)

    file_path = settings.MEDIA_ROOT + phone_number + '_all.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items = settings.MEDIA_URL + phone_number + '_all.pdf'
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items))
    plt.clf()


def draw_reading_2_5_no_txt_all_table(map_pro, colors_dict):
    phone_number = map_pro.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=all_cells_no_text, cellColours=None,
                         colLabels=short_columns, loc='center', cellLoc='center')
    fig.set_size_inches(12, 30)
    # fig.set_size_inches(10, 12)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(short_columns))))
    the_table.scale(1, 0.24)
    set_color_for_table(colors_dict, the_table, all_map_indexes_dict)

    file_path = settings.MEDIA_ROOT + phone_number + '_all_no_txt.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items_no_txt = settings.MEDIA_URL + phone_number + '_all_no_txt.pdf'
    # map_pro.save()
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items_no_txt))
    plt.clf()


def draw_reading_k_2_simple_map_table(map_pro, colors_dict):
    phone_number = map_pro.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=reading_k_2_cell_no_text, cellColours=None,
                         colLabels=short_columns, loc='center', cellLoc='center')
    # fig.set_size_inches(14, 30)
    fig.set_size_inches(10, 22)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(short_columns))))
    the_table.scale(1, 0.35)

    for i in range(len(reading_k_2_cell_no_text)):
        the_table[(i + 1, 7)].set_facecolor(mcolors.CSS4_COLORS['lightgrey'])
        the_table[(i + 1, 8)].set_facecolor(mcolors.CSS4_COLORS['lightgrey'])

    set_color_for_table(colors_dict, the_table, reading_k_2_indexes)

    file_path = settings.MEDIA_ROOT + phone_number + '.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url = settings.MEDIA_URL + phone_number + '.pdf'

    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url))
    plt.clf()


def draw_reading_k_2_in_all_table(map_pro, colors_dict):
    phone_number = map_pro.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=all_map_cell_text, cellColours=None,
                         colLabels=short_columns, loc='center', cellLoc='center')
    fig.set_size_inches(12, 30)
    # fig.set_size_inches(10, 12)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(short_columns))))
    the_table.scale(1, 0.24)

    set_color_for_table(colors_dict, the_table, all_map_indexes_dict)
    file_path = settings.MEDIA_ROOT + phone_number + '_all.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items = settings.MEDIA_URL + phone_number + '_all.pdf'
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items))
    plt.clf()


def draw_reading_k_2_no_txt_all_table(map_pro, colors_dict):
    phone_number = map_pro.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=all_cells_no_text, cellColours=None,
                         colLabels=short_columns, loc='center', cellLoc='center')
    fig.set_size_inches(12, 30)
    # fig.set_size_inches(10, 12)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(short_columns))))
    the_table.scale(1, 0.24)

    set_color_for_table(colors_dict, the_table, all_map_indexes_dict)
    file_path = settings.MEDIA_ROOT + phone_number + '_all_no_txt.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items_no_txt = settings.MEDIA_URL + phone_number + '_all_no_txt.pdf'
    # map_pro.save()
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items_no_txt))
    plt.clf()


def draw_language_2_12_simple_map_table(map_pro, colors_dict):
    phone_number = map_pro.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=language_2_12_simple_no_txt, cellColours=None,
                         colLabels=map_2_12_columns, loc='center', cellLoc='center')
    # fig.set_size_inches(14, 30)
    fig.set_size_inches(11, 17)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(map_2_12_columns))))
    the_table.scale(1, 0.55)

    set_color_for_table(colors_dict, the_table, language_2_12_indexes)
    file_path = settings.MEDIA_ROOT + phone_number + '.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url = settings.MEDIA_URL + phone_number + '.pdf'

    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url))
    plt.clf()


def draw_language_2_12_in_all_table(map_pro, colors_dict):
    phone_number = map_pro.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=map_2_12_table, cellColours=None,
                         colLabels=map_2_12_columns, loc='center', cellLoc='center')
    fig.set_size_inches(14, 30)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(map_2_12_columns))))
    the_table.scale(1, 0.24)

    map_res = map_pro.map_ext_results.all()
    for index_name in language_2_12_indexes.keys():
        index = map_2_12_table_indexes[index_name]
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])

    set_color_for_table(colors_dict, the_table, map_2_12_table_indexes)
    file_path = settings.MEDIA_ROOT + phone_number + '_all.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items = settings.MEDIA_URL + phone_number + '_all.pdf'
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items))
    plt.clf()


def draw_language_2_12_no_txt_all_table(map_pro, colors_dict):
    phone_number = map_pro.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=map_2_12_simple_table, cellColours=None,
                         colLabels=map_2_12_columns, loc='center', cellLoc='center')
    fig.set_size_inches(13, 30)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(map_2_12_columns))))
    the_table.scale(1, 0.24)

    set_color_for_table(colors_dict, the_table, map_2_12_table_indexes)

    file_path = settings.MEDIA_ROOT + phone_number + '_all_no_txt.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items_no_txt = settings.MEDIA_URL + phone_number + '_all_no_txt.pdf'
    # map_pro.save()
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items_no_txt))
    plt.clf()
