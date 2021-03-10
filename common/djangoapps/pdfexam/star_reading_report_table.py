import logging

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from django.conf import settings
from .star_reading_report_k_5_template import star_reading_k_5_columns, star_reading_k_5_template, \
    star_reading_k_5_template_no_name, star_reading_k_5_colors, star_reading_k_5_indexes
from .star_reading_report_6_12_template import star_reading_6_12_columns, star_reading_6_12_template, \
    star_reading_6_12_template_no_name, star_reading_6_12_colors, star_reading_6_12_indexes

# from .models import MapStudentProfile, MapProfileExtResults, MapTestCheckItem

log = logging.getLogger("edx.pdfexam")
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
k_5_grade = ['k', '1st', '2nd', '3rd', '4th', '5th']


def draw_star_reading_table(star_reading_obj):
    log.info("Start to drawing star reading table!")
    if star_reading_obj.grade in k_5_grade:
        colors_dict = create_table_colors_dict(star_reading_obj, star_reading_k_5_colors)
        draw_star_reading_k_5_report(star_reading_obj, colors_dict)
        draw_star_reading_k_5_report_no_name(star_reading_obj, colors_dict)
        log.info("star reading grade is {}, drew pdfs for report.".format(star_reading_obj.grade))
    else:
        colors_dict = create_table_colors_dict(star_reading_obj, star_reading_6_12_colors)
        draw_star_reading_6_12_report(star_reading_obj, colors_dict)
        draw_star_reading_6_12_report_no_name(star_reading_obj, colors_dict)
        log.info("Map report type is {}, drew pdfs for report.".format(star_reading_obj.Growth))
    star_reading_obj.save()


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
            elif color == 2:
                the_table[indexes].set_facecolor(mcolors.CSS4_COLORS['red'])
            else:
                the_table[indexes].set_facecolor(mcolors.CSS4_COLORS['lightgrey'])


def create_table_colors_dict(star_reading_obj, colors_dict_template):
    test_res = star_reading_obj.star_reading_report.all()
    colors_dict = colors_dict_template.copy()
    # log.info("map file {}'s init color is {}".format(star_reading_obj.Growth, colors_dict))
    for item_result in test_res:
        item_name = item_result.ccss_item.item_name
        item_score = item_result.item_score
        if 0 < item_score < 60:
            colors_dict[item_name] = 2
        elif 60 <= item_score < 80:
            colors_dict[item_name] = 1
        elif 80 <= item_score:
            colors_dict[item_name] = 0
    # log.info("map file {}'s color index after filling green is {}".format(star_reading_obj.Growth, colors_dict))
    return colors_dict


def draw_star_reading_k_5_report(star_reading_obj, colors_dict):
    phone_number = star_reading_obj.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=star_reading_k_5_template, cellColours=None,
                         colLabels=star_reading_k_5_columns, loc='center', cellLoc='center')
    fig.set_size_inches(12, 30)
    # fig.set_size_inches(10, 12)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(star_reading_k_5_columns))))
    the_table.scale(1, 0.24)

    set_color_for_table(colors_dict, the_table, star_reading_k_5_indexes)

    file_name = phone_number + star_reading_obj.test_date + '_star_reading.pdf'
    file_path = settings.MEDIA_ROOT + file_name
    plt.savefig(file_path, dpi=300)
    star_reading_obj.main_pdf_url = settings.MEDIA_URL + file_name
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             star_reading_obj.main_pdf_url))
    plt.clf()
    plt.cla()
    plt.close('all')


def draw_star_reading_k_5_report_no_name(star_reading_obj, colors_dict):
    phone_number = star_reading_obj.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=star_reading_k_5_template_no_name, cellColours=None,
                         colLabels=star_reading_k_5_columns, loc='center', cellLoc='center')
    fig.set_size_inches(12, 30)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(star_reading_k_5_columns))))
    the_table.scale(1, 0.24)

    set_color_for_table(colors_dict, the_table, star_reading_k_5_indexes)

    file_name = phone_number + star_reading_obj.test_date + '_star_reading_no_name.pdf'
    file_path = settings.MEDIA_ROOT + file_name
    plt.savefig(file_path, dpi=300)
    star_reading_obj.simple_pdf_url = settings.MEDIA_URL + file_name
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             star_reading_obj.simple_pdf_url))
    plt.clf()
    plt.cla()
    plt.close('all')


def draw_star_reading_6_12_report(star_reading_obj, colors_dict):
    phone_number = star_reading_obj.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=star_reading_6_12_template, cellColours=None,
                         colLabels=star_reading_6_12_columns, loc='center', cellLoc='center')
    fig.set_size_inches(12, 24)
    # fig.set_size_inches(10, 12)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(star_reading_6_12_columns))))
    the_table.scale(1, 0.32)

    set_color_for_table(colors_dict, the_table, star_reading_6_12_indexes)

    file_name = phone_number + star_reading_obj.test_date + '_star_reading.pdf'
    file_path = settings.MEDIA_ROOT + file_name
    plt.savefig(file_path, dpi=300)
    star_reading_obj.main_pdf_url = settings.MEDIA_URL + file_name
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             star_reading_obj.main_pdf_url))
    plt.clf()
    plt.cla()
    plt.close('all')


def draw_star_reading_6_12_report_no_name(star_reading_obj, colors_dict):
    phone_number = star_reading_obj.phone_number

    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=star_reading_6_12_template_no_name, cellColours=None,
                         colLabels=star_reading_6_12_columns, loc='center', cellLoc='center')
    fig.set_size_inches(12, 24)
    # fig.set_size_inches(10, 12)
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(star_reading_6_12_columns))))
    the_table.scale(1, 0.32)

    set_color_for_table(colors_dict, the_table, star_reading_6_12_indexes)

    file_name = phone_number + star_reading_obj.test_date + '_star_reading_no_name.pdf'
    file_path = settings.MEDIA_ROOT + file_name
    plt.savefig(file_path, dpi=300)
    star_reading_obj.simple_pdf_url = settings.MEDIA_URL + file_name
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             star_reading_obj.simple_pdf_url))
    plt.clf()
    plt.cla()
    plt.close('all')
