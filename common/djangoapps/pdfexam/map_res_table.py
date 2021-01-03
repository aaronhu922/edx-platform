import logging

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy
from django.conf import settings

from .map_table_tmplate import reading_2_5
from .models import MapStudentProfile, MapProfileExtResults, MapTestCheckItem

log = logging.getLogger("edx.pdfexam")


def draw_map_table(map_pro):
    phone_number = map_pro.phone_number

    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

    # Prepare table
    columns = ('Number', 'Domain', 'Items', 'GK', 'G1', 'G2', 'G3', 'G4', 'G5')
    cell_text = [
        ["1", "Language Standards(K-5)", "Conventions of Standard English", "L.K.1", "L.1.1", "L.2.1", "L.3.1",
         "L.4.1", "L.5.1"],
        ["", "", "", "L.K.1.A", "L.1.1.A", "L.2.1.A", "L.3.1.A", "L.4.1.A", "L.5.1.A"],
        ["", "", "", "L.K.1.B", "L.1.1.B", "L.2.1.B", "L.3.1.B", "L.4.1.B", "L.5.1.B"],
        ["", "", "", "L.K.1.C", "L.1.1.C", "L.2.1.C", "L.3.1.C", "L.4.1.C", "L.5.1.C"],
        ["", "", "", "L.K.1.D", "L.1.1.D", "L.2.1.D", "L.3.1.D", "L.4.1.D", "L.5.1.D"],
        ["", "", "", "L.K.1.E", "L.1.1.E", "L.2.1.E", "L.3.1.E", "L.4.1.E", "L.5.1.E"],
        ["", "", "", "L.K.1.F", "L.1.1.F", "L.2.1.F", "L.3.1.F", "L.4.1.F", ""],
        ["", "", "", "", "L.1.1.G", "", "L.3.1.G", "L.4.1.G", ""],
        ["", "", "", "", "L.1.1.H", "", "L.3.1.H", "", ""],
        ["", "", "", "", "L.1.1.I", "", "L.3.1.I", "", ""],
        ["", "", "", "", "L.1.1.J", "", "", "", ""],
        ["", "", "", "L.K.2", "L.1.2", "L.2.2", "L.3.2", "L.4.2", "L.5.2"],
        ["", "", "", "L.K.2.A", "L.1.2.A", "L.2.2.A", "L.3.2.A", "L.4.2.A", "L.5.2.A"],
        ["", "", "", "L.K.2.B", "L.1.2.B", "L.2.2.B", "L.3.2.B", "L.4.2.B", "L.5.2.B"],
        ["", "", "", "L.K.2.C", "L.1.2.C", "L.2.2.C", "L.3.2.C", "L.4.2.C", "L.5.2.C"],
        ["", "", "", "L.K.2.D", "L.1.2.D", "L.2.2.D", "L.3.2.D", "L.4.2.D", "L.5.2.D"],
        ["", "", "", "", "L.1.2.E", "L.2.2.E", "L.3.2.E", "", "L.5.2.E"],
        ["", "", "", "", "", "", "L.3.2.F", "", ""],
        ["", "", "", "", "", "", "L.3.2.G", "", ""],
        ["", "", "Knowledge of Language", "L.K.3", "L.K.3", "L.2.3", "L.3.3", "L.4.3", "L.5.3"],
        ["", "", "", "", "", "L.2.3.A", "L.3.3.A", "L.4.3.A", "L.5.3.A"],
        ["", "", "", "", "", "", "L.3.3.B", "L.4.3.B", "L.5.3.B"],
        ["", "", "", "", "", "", "", "L.4.3.C", ""],
        ["", "", "Vocabulary Acquisition and Use", "L.K.4", "L.1.4", "L.2.4", "L.3.4", "L.4.4", "L.5.4"],
        ["", "", "", "L.K.4.A", "L.1.4.A", "L.2.4.A", "L.3.4.A", "L.4.4.A", "L.5.4.A"],
        ["", "", "", "L.K.4.B", "L.1.4.B", "L.2.4.B", "L.3.4.B", "L.4.4.B", "L.5.4.B"],
        ["", "", "", "", "L.1.4.C", "L.2.4.C", "L.3.4.C", "L.4.4.C", "L.5.4.C"],
        ["", "", "", "", "", "L.2.4.D", "L.3.4.D", "", ""],
        ["", "", "", "", "", "L.2.4.E", "", "", ""],
        ["", "", "", "L.K.5", "L.1.5", "L.2.5", "L.3.5", "L.4.5", "L.5.5"],
        ["", "", "", "L.K.5.A", "L.1.5.A", "L.2.5.A", "L.3.5.A", "L.4.5.A", "L.5.5.A"],
        ["", "", "", "L.K.5.B", "L.1.5.B", "L.2.5.B", "L.3.5.B", "L.4.5.B", "L.5.5.B"],
        ["", "", "", "L.K.5.C", "L.1.5.C", "", "L.3.5.C", "L.4.5.C", "L.5.5.C"],
        ["", "", "", "L.K.5.D", "L.1.5.D", "", "", "", ""],
        ["", "", "", "L.K.6", "L.1.6", "L.2.6", "L.3.6", "L.4.6", "L.5.6"],
        ["2", "Speaking & Listening(K-5)", "Comprehension and Collaboration", "SL.K.1", "SL.1.1", "SL.2.1",
         "SL.3.1", "SL.4.1", "SL.5.1.1"],
        ["", "", "", "SL.K.1.A", "SL.1.1.A", "SL.2.1.A", "SL.3.1.A", "SL.4.1.A", "SL.5.1.1.A"],
        ["", "", "", "SL.K.1.B", "SL.1.1.B", "SL.2.1.B", "SL.3.1.B", "SL.4.1.B", "SL.5.1.1.B"],
        ["", "", "", "", "SL.1.1.C", "SL.2.1.C", "SL.3.1.C", "SL.4.1.C", "SL.5.1.1..C"],
        ["", "", "", "", "", "", "SL.3.1.D", "SL.4.1.D", "SL.5.1.1.D"],
        ["", "", "", "SL.K.2", "SL.1.2", "SL.2.2", "SL.3.2", "SL.4.1.2", "SL.5.2"],
        ["", "", "", "SL.K.3", "SL.1.3", "SL.2.3", "SL.3.3", "SL.4.1.3", "SL.5.3"],
        ["", "", "Presentation of Knowledge and Ideas", "SL.K.4", "SL.1.4", "SL.2.4", "SL.3.4", "SL.4.1.4",
         "SL.5.4"],
        ["", "", "", "SL.K.5", "SL.1.5", "SL.2.5", "SL.3.5", "SL.4.1.5", "SL.5.5"],
        ["", "", "", "SL.K.6", "SL.1.6", "SL.2.6", "SL.3.6", "SL.4.1.6", "SL.5.6"],
        ["3", "Writing", "Text Types and Purposes", "W.K.1", "W.1.1", "W.2.1", "W.3.1", "W.4.1", "W.5.1"],
        ["", "", "", "", "", "", "W.3.1.A", "W.4.1.A", "W.5.1.A"],
        ["", "", "", "", "", "", "W.3.1.B", "W.4.1.B", "W.5.1.B"],
        ["", "", "", "", "", "", "W.3.1.C", "W.4.1.C", "W.5.1.C"],
        ["", "", "", "", "", "", "W.3.1.D", "W.4.1.D", "W.5.1.D"],
        ["", "", "", "W.K.2", "W.1.2", "W.2.2", "W.3.2", "W.4.2", "W.5.2"],
        ["", "", "", "", "", "", "W.3.2.A", "W.4.2.A", "W.5.2.A"],
        ["", "", "", "", "", "", "W.3.2.B", "W.4.2.B", "W.5.2.B"],
        ["", "", "", "", "", "", "W.3.2.C", "W.4.2.C", "W.5.2.C"],
        ["", "", "", "", "", "", "W.3.2.D", "W.4.2.D", "W.5.2.D"],
        ["", "", "", "", "", "", "", "W.4.2.E", "W.5.2.E"],
        ["", "", "", "W.K.3", "W.1.3", "W.2.3", "W.3.3", "W.4.3", "W.5.3"],
        ["", "", "", "", "", "", "W.3.3.A", "W.4.3.A", "W.5.3.A"],
        ["", "", "", "", "", "", "W.3.3.B", "W.4.3.B", "W.5.3.B"],
        ["", "", "", "", "", "", "W.3.3.C", "W.4.3.C", "W.5.3.C"],
        ["", "", "", "", "", "", "W.3.3.D", "W.4.3.D", "W.5.3.D"],
        ["", "", "", "", "", "", "", "W.4.3.E", "W.5.3.E"],
        ["", "", "Production and Distribution of Writing", "W.K.4", "W.1.4", "W.2.4", "W.3.4", "W.4.4", "W.5.4"],
        ["", "", "", "W.K.5", "W.1.5", "W.2.5", "W.3.5", "W.4.5", "W.5.5"],
        ["", "", "", "W.K.6", "W.1.6", "W.2.6", "W.3.6", "W.4.6", "W.5.6"],
        ["", "", "Research to Build and Present Knowledge", "W.K.7", "W.1.7", "W.2.7", "W.3.7", "W.4.7",
         "W.5.7"],
        ["", "", "", "W.K.8", "W.1.8", "W.2.8", "W.3.8", "W.4.8", "W.5.8"],
        ["", "", "", "W.K.9", "W.1.9", "W.2.9", "W.3.9", "W.4.9", "W.5.9"],
        ["", "", "", "", "", "", "", "W.4.9.A", "W.5.9.A"],
        ["", "", "", "", "", "", "", "W.4.9.B", "W.5.9.B"],
        ["", "", "Range of Writing", "W.K.10", "W.1.10", "W.2.10", "W.3.10", "W.4.10", "W.5.10"],
        ["4", "Reading: Foundational Skills(K-5)", "Print Concepts", "RF.K.1", "RF.1.1", "", "", "", ""],
        ["", "", "", "RF.K.1.A", "RF.1.1.A", "", "", "", ""],
        ["", "", "", "RF.K.1.B", "", "", "", "", ""],
        ["", "", "", "RF.K.1.C", "", "", "", "", ""],
        ["", "", "", "RF.K.1.D", "", "", "", "", ""],
        ["", "", "Phonological Awareness", "RF.K.2", "RF.1.2", "", "", "", ""],
        ["", "", "", "RF.K.2.A", "RF.1.2A", "", "", "", ""],
        ["", "", "", "RF.K.2.B", "RF.1.2B", "", "", "", ""],
        ["", "", "", "RF.K.2.C", "RF.1.2.C", "", "", "", ""],
        ["", "", "", "RF.K.2.D", "RF.1.2.D", "", "", "", ""],
        ["", "", "", "RF.K.2.E", "", "", "", "", ""],
        ["", "", "Phonics and Word Recognition", "RF.K.3", "RF.1.3", "RF.2.3", "RF.3.3", "RF.4.3", "RF.5.3"],
        ["", "", "", "RF.K.3.A", "RF.1.3.A", "RF.2.3.A", "RF.3.3.A", "RF.4.3.A", "RF.5.3.A"],
        ["", "", "", "RF.K.3.B", "RF.1.3.B", "RF.2.3.B", "RF.3.3.B", "", ""],
        ["", "", "", "RF.K.3.C", "RF.1.3.C", "RF.2.3.C", "RF.3.3.C", "", ""],
        ["", "", "", "RF.K.3.D", "RF.1.3.D", "RF.2.3.D", "RF.3.3.D", "", ""],
        ["", "", "", "", "RF.1.3.E", "RF.2.3.E", "", "", ""],
        ["", "", "", "", "RF.1.3.F", "RF.2.3.F", "", "", ""],
        ["", "", "", "", "RF.1.3.G", "", "", "", ""],
        ["", "", "Fluency", "RF.K.4", "RF.1.4", "RF.2.4", "RF.3.4", "RF.4.4", "RF.5.4"],
        ["", "", "", "", "RF.1.4.A", "RF.2.4.A", "RF.3.4.A", "RF.4.4.A", "RF.5.4.A"],
        ["", "", "", "", "RF.1.4.B", "RF.2.4.B", "RF.3.4.B", "RF.4.4.B", "RF.5.4.B"],
        ["", "", "", "", "RF.1.4.C", "RF.2.4.C", "RF.3.4.C", "RF.4.4.C", "RF.5.4.C"],
        ["5", "Reading Literature", "Key Ideas and Details", "RL.K.1", "RL.1.1", "RL.2.1", "RL.3.1",
         "RL.4.1", "RL.5.1"],
        ["", "", "", "RL.K.2", "RL.1.2", "RL.2.2", "RL.3.2", "RL.4.2", "RL.5.2"],
        ["", "", "", "RL.K.3", "RL.1.3", "RL.2.3", "RL.3.3", "RL.4.3", "RL.5.3"],
        ["", "", "Craft and Structure", "RL.K.4", "RL.1.4", "RL.2.4", "RL.3.4", "RL.4.4", "RL.5.4"],
        ["", "", "", "RL.K.5", "RL.1.5", "RL.2.5", "RL.3.5", "RL.4.5", "RL.5.5"],
        ["", "", "", "RL.K.6", "RL.1.6", "RL.2.6", "RL.3.6", "RL.4.6", "RL.5.6"],
        ["", "", "Integration of Knowledge and Ideas", "RL.K.7", "RL.1.7", "RL.2.7", "RL.3.7", "RL.4.7", "RL.5.7"],
        ["", "", "", "RL.K.8", "RL.1.8", "RL.2.8", "RL.3.8", "RL.4.8", "RL.5.8"],
        ["", "", "", "RL.K.9", "RL.1.9", "RL.2.9", "RL.3.9", "RL.4.9", "RL.5.9"],
        ["", "", "Range of Reading and Level of Text Complexity", "RL.K.10", "RL.1.10", "RL.2.10", "RL.3.10",
         "RL.4.10", "RL.5.10"],
        ["6", "Reading Standards for Informational Text(K-5)", "Key Ideas and Details", "RI.K.1", "RI.1.1",
         "RI.2.1", "RI.3.1", "RI.4.1", "RI.5.1"],
        ["", "", "", "RI.K.2", "RI.1.2", "RI.2.2", "RI.3.2", "RI.4.2", "RI.5.2"],
        ["", "", "", "RI.K.3", "RI.1.3", "RI.2.3", "RI.3.3", "RI.4.3", "RI.5.3"],
        ["", "", "Craft and Structure", "RI.K.4", "RI.1.4", "RI.2.4", "RI.3.4", "RI.4.4", "RI.5.4"],
        ["", "", "", "RI.K.5", "RI.1.5", "RI.2.5", "RI.3.5", "RI.4.5", "RI.5.5"],
        ["", "", "", "RI.K.6", "RI.1.6", "RI.2.6", "RI.3.6", "RI.4.6", "RI.5.6"],
        ["", "", "Integration of Knowledge and Ideas", "RI.K.7", "RI.1.7", "RI.2.7", "RI.3.7", "RI.4.7", "RI.5.7"],
        ["", "", "", "RI.K.8", "RI.1.8", "RI.2.8", "RI.3.8", "RI.4.8", "RI.5.8"],
        ["", "", "", "RI.K.9", "RI.1.9", "RI.2.9", "RI.3.9", "RI.4.9", "RI.5.9"],
        ["", "", "Range of Reading and Level of Text Complexity", "RI.K.10", "RI.1.10", "RI.2.10", "RI.3.10",
         "RI.4.10", "RI.5.10"]]

    matrix = numpy.array(cell_text)
    fig, ax = plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=cell_text, cellColours=None,
                         colLabels=columns, loc='center', cellLoc='left')
    fig.set_size_inches(14, 30)
    # plt.figure(figsize=(1800, 1000))
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.auto_set_column_width(col=list(range(len(columns))))
    the_table.scale(1, 0.24)

    map_res = map_pro.map_ext_results.all()

    for item_result in map_res:
        item_name = item_result.check_item.item_name
        reading_2_5.remove(item_name)
        item_level = item_result.item_level
        indexes = numpy.argwhere(matrix == item_name)
        if indexes.size > 0:
            if item_level == "DEVELOP" or item_level == "REINFORCE_DEVELOP":
                the_table[(indexes[0][0] + 1, indexes[0][1])].set_facecolor(mcolors.CSS4_COLORS['red'])
            elif item_level == "REINFORCE":
                the_table[(indexes[0][0] + 1, indexes[0][1])].set_facecolor(mcolors.CSS4_COLORS['yellow'])
            else:
                the_table[(indexes[0][0] + 1, indexes[0][1])].set_facecolor(mcolors.CSS4_COLORS['green'])

    log.info("Length of green cell is {}.".format(len(reading_2_5)))
    for green_item_name in reading_2_5:
        indexes = numpy.argwhere(matrix == green_item_name)
        log.info("Item {}'s index is {}".format(green_item_name, indexes))
        if indexes.size > 0:
            the_table[(indexes[0][0] + 1, indexes[0][1])].set_facecolor(mcolors.CSS4_COLORS['green'])
    file_path = settings.MEDIA_ROOT + phone_number + '.pdf'
    plt.savefig(file_path, dpi=200)
    map_pro.map_pdf_url = settings.MEDIA_URL + phone_number + '.pdf'
    map_pro.save()
    log.info("Successfully create the table for {}'s map test to file {}, url is {}.".format(phone_number, file_path,
                                                                                             map_pro.map_pdf_url))
    plt.clf()
