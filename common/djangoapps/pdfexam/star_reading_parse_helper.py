import logging
import re
from datetime import datetime
from .models import MapTestCheckItem, StarReadingTestInfo, StarReadingTestInfoReport
from .map_table_tmplate import domain_full_name_list, domain_name_reg_list

log = logging.getLogger("edx.pdfexam")


def parse_star_reading_data(content, phone_number):
    star_reading_model = {}

    regex1 = 'Benchmark Type (.*?District)'
    value = re.findall(regex1, content)
    log.info("school - benchmark regex {}".format(regex1))
    # 'Thompson Edu Cooper, L 08/01/20–07/30/21 All Demographics  Star Enterprise Scale District'
    if value:
        log.info("school - benchmark info {}".format(value[0]))
        temp_arr = value[0].split(" ")
        star_reading_model['school'] = temp_arr[0] + " " + temp_arr[1]
        star_reading_model['date_range'] = temp_arr[4]
        stu_name = temp_arr[2] + temp_arr[3]
        star_reading_model['stu_name'] = stu_name

    regex1 = 'Test Date Grade (.*?) Teacher Class/Group'
    value1 = re.findall(regex1, content)
    # ['Cooper, L 56d48a9e-1b50-49e4-ae17-3d852a012361  Jan 31, 2021, 2:50 AM  8th']
    # ['n','newstar03,','newstar03', 'd115e9a9-e207-4394-9d32-1292f1321a', '', 'Jan', '29,', '2021,', '7:51', 'PM', '',
    # '2nd']
    log.info("name - grade regex {}".format(regex1))
    if value1:
        log.info("name - grade: {}".format(value1[0]))
        name_list = value1[0].split(" ")
        date_string = name_list[-7] + name_list[-6] + name_list[-5]
        test_date = datetime.strptime(date_string.strip(','), '%b%d,%Y').strftime("%Y-%m-%d")
        stu_id = name_list[-9]
        grade = name_list[-1]
        if len(grade) > 2:
            grade = grade[:-2]

        star_reading_model['test_date'] = test_date
        star_reading_model['stu_id'] = stu_id
        star_reading_model['grade'] = grade

    # regex1 = 'Teacher Class/Group (.*?) District'
    # value1 = re.findall(regex1, content)
    # log.info("teacher - class: {}".format(value1[0]))
    # if value1:
    #     list_str = value1[0].split("  ")
    #     teacher = list_str[0]
    #     class_group = list_str[1]
    #     star_reading_model['teacher'] = teacher
    #     star_reading_model['class_group'] = class_group

    # SS PR GE 196 81 2.1
    regex1 = 'SS PR GE (.*?) \(Scaled Score\)'
    value1 = re.findall(regex1, content)
    log.info("SS PR GE regex: {}".format(regex1))
    if value1:
        log.info("SS PR GE: {}".format(value1[0]))
        value_list = value1[0].split(" ")
        star_reading_model['scaled_score'] = value_list[0]
        star_reading_model['percentile_rank'] = value_list[1]
        star_reading_model['grade_equivalent'] = value_list[2]

    regex1 = '(IRL.*?) \(Instructional'
    value1 = re.findall(regex1, content)
    log.info("IRL regex: {}".format(regex1))
    if value1:
        log.info("IRL: {}".format(value1[0]))
        value_list = value1[0].split(" ")
        if len(value_list) == 5:
            star_reading_model['instructional_reading_level'] = value_list[-2]
            star_reading_model['estimated_oral_fluency'] = value_list[-1]
        else:
            star_reading_model['instructional_reading_level'] = value_list[-1]

    regex1 = 'Literature (.*?) Informational Text'
    value1 = re.findall(regex1, content)
    log.info("Literature score regex: {}".format(regex1))
    if value1:
        log.info("Literature score: {}".format(value1[0]))
        value_list = re.findall("\d{1,2}", value1[0])
        star_reading_model['literature_key_ideas_and_details'] = value_list[0]
        if len(value_list) >= 3:
            star_reading_model['literature_craft_and_structure'] = value_list[1]
            star_reading_model['literature_range_of_reading_and_text_complexity'] = value_list[2]
        elif len(value_list) == 2:
            if "Structure" in value1[0]:
                star_reading_model['literature_craft_and_structure'] = value_list[1]
            else:
                star_reading_model['literature_range_of_reading_and_text_complexity'] = value_list[1]

    regex1 = 'Informational Text (.*?) Language'
    value1 = re.findall(regex1, content)
    log.info("Informational Text regex: {}".format(regex1))
    if value1:
        log.info("Informational Text: {}".format(value1[0]))
        value_list = re.findall("\d{1,2}", value1[0])
        star_reading_model['information_text_key_ideas_and_details'] = value_list[0]
        if len(value_list) >= 4:
            star_reading_model['information_text_craft_and_structure'] = value_list[1]
            star_reading_model['information_text_integration_of_knowledge_and_ideas'] = value_list[2]
            star_reading_model['information_text_range_of_reading_and_text_complexity'] = value_list[3]
        elif len(value_list) == 3:
            star_reading_model['information_text_craft_and_structure'] = value_list[1]
            star_reading_model['information_text_integration_of_knowledge_and_ideas'] = value_list[2]
        elif len(value_list) == 2:
            if "Structure" in value1[0]:
                star_reading_model['information_text_craft_and_structure'] = value_list[1]
            else:
                star_reading_model['information_text_integration_of_knowledge_and_ideas'] = value_list[1]

    regex1 = '(\d{1,2}) Vocabulary Acquisition and Use'
    value1 = re.findall(regex1, content)
    if value1:
        log.info("Vocabulary Acquisition score: {}".format(value1[0]))
        score = value1[0]
    else:
        value1 = re.findall("Vocabulary Acquisition and (\d{1,2})", content)
        if value1:
            score = value1[0]
        else:
            value1 = re.findall("Vocabulary Acquisition and Use (\d{1,2})", content)
            score = value1[0]
        log.info("Vocabulary Acquisition score: {}".format(value1[0]))
    if score:
        star_reading_model['language_vocabulary_acquisition_and_use'] = score

    regex1 = 'Test Duration: (.*secs)'
    value1 = re.findall(regex1, content)
    if value1:
        log.info("Test Duration: {}".format(value1[0]))
        star_reading_model['test_duration'] = value1[0]

    # regex1 = 'Lexile® (.*?) Range'
    # value1 = re.findall(regex1, content)
    # log.info("Lexile range: {}".format(value1))
    # if value1:
    #     star_reading_model[''] = value1[0]

    regex1 = '\w{2,5}L - \w{2,5}L'
    value1 = re.findall(regex1, content)
    log.info("Lexile range regex: {}".format(regex1))
    if value1:
        log.info("Lexile range: {}".format(value1))
        star_reading_model['lexile_range'] = value1[0]
    log.info(star_reading_model)
    star_reading_obj, created = StarReadingTestInfo.objects.update_or_create(phone_number=phone_number,
                                                                             test_date=star_reading_model["test_date"],
                                                                             defaults=star_reading_model)
    if not created:
        log.warning(
            "Updated star reading test {} {}, need to clear pre report info.".format(phone_number, test_date))
        StarReadingTestInfoReport.objects.filter(star_reading_test_info=star_reading_obj).delete()
    else:
        log.info("created star reading test {} {}".format(phone_number, test_date))
    return star_reading_obj


def parse_star_reading_report(item_table, star_reading_obj):
    domain_name = ""
    for page_info in item_table:
        for ccss_items in page_info:
            if "CCSS.ELA-Literacy" in ccss_items[0]:
                # it is item.
                desc = ccss_items[0]
                value = re.findall("CCSS.ELA-Literacy.[\w.]+", desc)

                item_name = value[0]
                desc = desc.replace(item_name, "")
                desc = desc.replace("Cra\x00", "Craft")
                desc = desc.replace("\x00", "ff")
                if item_name[-1].isalpha():
                    item_name = (item_name[18:-1] + "." + item_name[-1]).upper()
                else:
                    item_name = item_name[18:].upper()

                # item = {
                #     "star_reading_test_info": star_reading_obj,
                #     "domain_name": domain_name,
                #     "item_desc": desc,
                #     "item_score": ccss_items[2]
                # }
                if ccss_items[2].isdigit():
                    item_score = ccss_items[2]
                else:
                    item_score = 0
                report_item = StarReadingTestInfoReport(star_reading_test_info=star_reading_obj,
                                                        domain_name=domain_name, item_desc=desc,
                                                        item_score=item_score)
                check_item = MapTestCheckItem.objects.filter(item_name=item_name).first()

                if check_item:
                    report_item.ccss_item = check_item
                    # log.info("item {} {}, score {}".format(item_name, desc, item_score))
                    report_item.save()
                else:
                    log.warning("there is no ccss item {}, with item {}".format(item_name, report_item))
            else:
                domain_name = ccss_items[0]
                domain_name = domain_name.replace("Cra\x00", "Craft")
