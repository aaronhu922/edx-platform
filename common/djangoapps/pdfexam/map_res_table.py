import logging

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from django.conf import settings

from .reading_2_5_template import short_columns, reading_2_5_short_txt, reading_2_5_no_txt, reading_2_5_indexes
from .map_table_tmplate import all_map_indexes_dict, all_map_cell_text, all_cells_no_text
from .reading_k_2_template import reading_k_2_indexes, reading_k_2_cell_no_text
from .lanuage_2_12_template import language_2_12_indexes, language_2_12_simple_no_txt, map_2_12_columns
from .map_2_12_table_template import map_2_12_simple_table, map_2_12_table, map_2_12_table_indexes
# from .models import MapStudentProfile, MapProfileExtResults, MapTestCheckItem

log = logging.getLogger("edx.pdfexam")
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


def draw_map_table(map_pro):
    if map_pro.Growth.startswith('Reading 2-5'):
        draw_reading_2_5_map_table(map_pro)
        draw_reading_2_5_in_all_table(map_pro)
        draw_reading_2_5_no_txt_all_table(map_pro)
        log.info("Map report type is {}, drew pdfs for report.".format(map_pro.Growth))
    elif map_pro.Growth.startswith('Reading K-2'):
        draw_reading_k_2_simple_map_table(map_pro)
        draw_reading_k_2_in_all_table(map_pro)
        draw_reading_k_2_no_txt_all_table(map_pro)
        log.info("Map report type is {}, drew pdfs for report.".format(map_pro.Growth))
    elif map_pro.Growth.startswith('Language'):
        draw_language_2_12_simple_map_table(map_pro)
        draw_language_2_12_in_all_table(map_pro)
        draw_language_2_12_no_txt_all_table(map_pro)
        log.info("Map report type is {}, drew pdfs for report.".format(map_pro.Growth))
    else:
        log.info("Wrong map type {}".format(map_pro.Growth))
        pass

    map_pro.save()


def draw_reading_2_5_map_table(map_pro):
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

    map_res = map_pro.map_ext_results.all()
    for index in reading_2_5_indexes.values():
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])

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

    file_path = settings.MEDIA_ROOT + phone_number + '.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url = settings.MEDIA_URL + phone_number + '.pdf'

    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url))
    plt.clf()


def draw_reading_2_5_in_all_table(map_pro):
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

    map_res = map_pro.map_ext_results.all()
    for index_name in reading_2_5_indexes.keys():
        index = all_map_indexes_dict[index_name]
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level
        try:
            indexes = all_map_indexes_dict[item_name]
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

    file_path = settings.MEDIA_ROOT + phone_number + '_all.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items = settings.MEDIA_URL + phone_number + '_all.pdf'
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items))
    plt.clf()


def draw_reading_2_5_no_txt_all_table(map_pro):
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

    map_res = map_pro.map_ext_results.all()
    for index_name in reading_2_5_indexes.keys():
        index = all_map_indexes_dict[index_name]
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level
        try:
            indexes = all_map_indexes_dict[item_name]
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

    file_path = settings.MEDIA_ROOT + phone_number + '_all_no_txt.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items_no_txt = settings.MEDIA_URL + phone_number + '_all_no_txt.pdf'
    # map_pro.save()
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items_no_txt))
    plt.clf()


def draw_reading_k_2_simple_map_table(map_pro):
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

    map_res = map_pro.map_ext_results.all()
    for index in reading_k_2_indexes.values():
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])

    for i in range(len(reading_k_2_cell_no_text)):
        the_table[(i + 1, 7)].set_facecolor(mcolors.CSS4_COLORS['lightgrey'])
        the_table[(i + 1, 8)].set_facecolor(mcolors.CSS4_COLORS['lightgrey'])

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level
        try:
            indexes = reading_k_2_indexes[item_name]
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

    file_path = settings.MEDIA_ROOT + phone_number + '.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url = settings.MEDIA_URL + phone_number + '.pdf'

    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url))
    plt.clf()


def draw_reading_k_2_in_all_table(map_pro):
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

    map_res = map_pro.map_ext_results.all()
    for index_name in reading_k_2_indexes.keys():
        index = all_map_indexes_dict[index_name]
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level
        try:
            indexes = all_map_indexes_dict[item_name]
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

    file_path = settings.MEDIA_ROOT + phone_number + '_all.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items = settings.MEDIA_URL + phone_number + '_all.pdf'
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items))
    plt.clf()


def draw_reading_k_2_no_txt_all_table(map_pro):
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

    map_res = map_pro.map_ext_results.all()
    for index_name in reading_k_2_indexes.keys():
        index = all_map_indexes_dict[index_name]
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level
        try:
            indexes = all_map_indexes_dict[item_name]
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

    file_path = settings.MEDIA_ROOT + phone_number + '_all_no_txt.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items_no_txt = settings.MEDIA_URL + phone_number + '_all_no_txt.pdf'
    # map_pro.save()
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items_no_txt))
    plt.clf()


def draw_language_2_12_simple_map_table(map_pro):
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

    map_res = map_pro.map_ext_results.all()
    for index in language_2_12_indexes.values():
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level
        try:
            indexes = language_2_12_indexes[item_name]
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

    file_path = settings.MEDIA_ROOT + phone_number + '.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url = settings.MEDIA_URL + phone_number + '.pdf'

    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url))
    plt.clf()


def draw_language_2_12_in_all_table(map_pro):
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

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level
        try:
            indexes = map_2_12_table_indexes[item_name]
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

    file_path = settings.MEDIA_ROOT + phone_number + '_all.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items = settings.MEDIA_URL + phone_number + '_all.pdf'
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items))
    plt.clf()


def draw_language_2_12_no_txt_all_table(map_pro):
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

    map_res = map_pro.map_ext_results.all()
    for index_name in language_2_12_indexes.keys():
        index = map_2_12_table_indexes[index_name]
        the_table[(index[0], index[1])].set_facecolor(mcolors.CSS4_COLORS['limegreen'])

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        item_level = item_result.item_level
        try:
            indexes = map_2_12_table_indexes[item_name]
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

    file_path = settings.MEDIA_ROOT + phone_number + '_all_no_txt.pdf'
    plt.savefig(file_path, dpi=300)
    map_pro.map_pdf_url_all_items_no_txt = settings.MEDIA_URL + phone_number + '_all_no_txt.pdf'
    # map_pro.save()
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url_all_items_no_txt))
    plt.clf()
