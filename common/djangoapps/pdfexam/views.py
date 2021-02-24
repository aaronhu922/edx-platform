import logging
import re
from pathlib import Path

from django.conf import settings
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from io import open
import os
import pdfplumber

from .map_res_table import draw_map_table
from .models import EarlyliteracySkillSetScores, MapTestCheckItem
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from .parse_helper import ExtractStarData, extract_map_data, extract_map_ext_data
from .star_reading_table import draw_star_reading_table
from student.models import UserProfile
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from reportlab.pdfgen import canvas

log = logging.getLogger("edx.pdfexam")


# Create your views here.

def choose_file(request):
    temp = loader.get_template('pdf2MySQL/upload_file.html')
    return HttpResponse(temp.render())


def upload_file(request):
    return render(request, 'pdf2MySQL/upload_file.html')


# @login_required
# @ensure_csrf_cookie
@csrf_exempt
def handle_pdf_data(request):
    # request.Files['myfile']
    context = {
        'message': "",
    }
    if 'phone_number' not in request.POST:
        return JsonResponse({"errorCode": "400",
                             "executed": True,
                             "message": "No phone number input for pdf upload!",
                             "success": False}, status=200)

    phonenumber = request.POST['phone_number']
    test_type = request.POST['test_type']
    '''  3 types of test report.
    "star_early", "star_reading", "map_test"
    '''
    log.info("Import {} report for user {}".format(test_type, phonenumber))
    user_pro = UserProfile.objects.filter(phone_number=phonenumber).first()
    if not user_pro:
        context["message"] = "手机号 {} 不存在，请先用手机号注册。".format(phonenumber)
        return render(request, 'pdf2MySQL/show_failed.html', context)

    if request.method == 'POST':  # 请求方法为POST时，进行处理
        try:
            myFile = request.FILES['myfile']  # 获取上传的文件，如果没有文件，则默认为None
        except MultiValueDictKeyError as err:
            log.error(err)
            context["message"] = "请选择要上传的测试pdf。"
            return render(request, 'pdf2MySQL/show_failed.html', context)

        destination = open(os.path.join(settings.MEDIA_ROOT, myFile.name), 'wb+')  # 打开特定的文件进行二进制的写操作

        for chunk in myFile.chunks():  # 分块写入文件
            destination.write(chunk)

        destination.close()
        #
        # ################################################################
        # #  trans to txt file and stored in txtintermediate dictionary
        # ################################################################
        pdffilestored = os.path.join(settings.MEDIA_ROOT, myFile.name)

        with pdfplumber.open(pdffilestored) as pdf:
            content = ''
            # len(pdf.pages)为PDF文档页数
            for i in range(len(pdf.pages)):
                # pdf.pages[i] 是读取PDF文档第i+1页
                page = pdf.pages[i]
                # page.extract_text()函数即读取文本内容，下面这步是去掉文档最下面的页码
                page_content = '\n'.join(page.extract_text().split('\n')[1:-1])
                content = content + page_content
        os.remove(pdffilestored)
        try:
            ext_data = None
            ext_file = request.FILES.get('ext_file')
            if test_type == "map_test" and ext_file:
                # ext_file = request.FILES['ext_file']
                destination = open(os.path.join(settings.MEDIA_ROOT, ext_file.name), 'wb+')
                for chunk in ext_file.chunks():
                    destination.write(chunk)
                destination.close()
                ext_pdffilestored = os.path.join(settings.MEDIA_ROOT, ext_file.name)
                with pdfplumber.open(ext_pdffilestored) as pdf1:
                    pages = pdf1.pages
                    tbl = pages[0].extract_tables()
                    ext_data = str(tbl[0][-2])
                    ext_data = ext_data.replace('\\n', '&')
                    ext_data = ext_data.replace('\\uf120', '---')
                log.info("Map ext data is {}".format(ext_data))
                os.remove(ext_pdffilestored)
        except Exception as err:
            log.error(err)
            log.error("Upload pdf {} failed!".format(ext_file.name))
            context["message"] = "辅助报告上传失败，错误原因：" + str(err)
            return render(request, 'pdf2MySQL/show_failed.html', context)

        try:
            instructional_file = request.FILES.get('instructional_file')
            if test_type == "map_test" and instructional_file:
                create_instructional_report(phonenumber, instructional_file)
        except Exception as err:
            raise err
            log.error(err)
            log.error("Upload pdf {} failed!".format(ext_file.name))
            context["message"] = "指导报告上传失败，错误原因：" + str(err)
            return render(request, 'pdf2MySQL/show_failed.html', context)

        try:
            if test_type == "star_early":
                ExtractStarData(content, phonenumber)
            elif test_type == "map_test":
                stu_map_pro = extract_map_data(content, phonenumber)
                if ext_data:
                    stu_map_pro = extract_map_ext_data(ext_data, stu_map_pro)
                draw_map_table(stu_map_pro)
            elif test_type == "star_reading":
                draw_star_reading_table()
            else:
                context["message"] = "类型暂不支持！"
                return render(request, 'pdf2MySQL/show_failed.html', context)
        except Exception as err:
            log.error(err)
            log.error("Upload pdf {} failed!".format(myFile.name))
            context["message"] = "解析错误，请选择正确的文件类型！" + str(err)
            return render(request, 'pdf2MySQL/show_failed.html', context)
        if ext_file:
            context["message"] = "用户{}，上传的报告： {} 和 {}。".format(phonenumber, myFile.name, ext_file.name)
        else:
            context["message"] = "用户{}，上传的报告： {}。".format(phonenumber, myFile.name)
        return render(request, 'pdf2MySQL/show_success.html', context)


def show(self, request):
    temp = loader.get_template('pdf2MySQL/show_success.html')
    return HttpResponse(temp.render())


def create_instructional_report(phonenumber, instructional_file):
    destination = open(os.path.join(settings.MEDIA_ROOT, instructional_file.name), 'wb+')
    for chunk in instructional_file.chunks():
        destination.write(chunk)
    destination.close()
    instruct_pdffilestored = os.path.join(settings.MEDIA_ROOT, instructional_file.name)
    pdf_writer = PdfFileWriter()
    original_report = PdfFileReader(open(instruct_pdffilestored, "rb"))
    pages_num = len(original_report.pages)
    first_page = original_report.getPage(0)
    up_right = first_page.mediaBox.upperRight
    first_page.mediaBox.upperLeft = (0, up_right[1] - 320)
    pdf_writer.addPage(first_page)
    first_page_new = os.path.join(settings.MEDIA_ROOT, phonenumber + "_0.pdf")
    last_page_new = os.path.join(settings.MEDIA_ROOT, phonenumber + "_1.pdf")
    with Path(first_page_new).open(mode="wb") as output_file:
        pdf_writer.write(output_file)

    with pdfplumber.open(instruct_pdffilestored) as pdf1:
        pages = pdf1.pages
        text = pages[-1].extract_text()
        log.info("Map instructional data of last page is {}".format(text))
        make_pdf_file(last_page_new, text, up_right)
    merger = PdfFileMerger()
    input_first = open(first_page_new, "rb")
    input_last = open(last_page_new, "rb")
    merger.append(input_first)
    merger.append(fileobj=original_report, pages=(1, pages_num - 1))
    merger.append(input_last)
    final_name = phonenumber + "_instruction.pdf"
    final_page = os.path.join(settings.MEDIA_ROOT, final_name)
    output = open(final_page, "wb")
    merger.write(output)
    merger.close()
    os.remove(instruct_pdffilestored)
    os.remove(first_page_new)
    os.remove(last_page_new)

    return final_name


def make_pdf_file(output_filename, text, up_right):
    inch = 72
    point = 1
    # title = output_filename
    log.warning("Page size of instructional report is {}".format(up_right))

    c = canvas.Canvas(output_filename, pagesize=up_right)
    v = int(up_right[1]) - 40
    width = int(up_right[0])
    text = re.sub('re.ning', 'refining', text)
    text = re.sub('on.ction', 'onfiction', text)
    text = re.sub('speci.c', 'specific', text)
    text = re.sub('Identi.es', 'Identifies', text)
    text = re.sub('e.ectiveness', 'effectiveness', text)
    text = re.sub('di.erent', 'different', text)
    text = re.sub('re.ects', 'reflects', text)
    text = re.sub('con.icting', 'conflicting', text)
    text = re.sub(' .ts', ' fits', text)
    txt_arr = text.split('\n')
    i = 0
    for subtline in txt_arr:
        log.info(subtline)
        if len(subtline) < 5:
            v -= 20 * point
            i += 1
            continue
        if subtline.startswith("CONFIDENTIALITY NOTICE:"):
            break
        if subtline.endswith(":"):
            c.setFont("Helvetica-Bold", 10 * point)
            c.drawString(1 * inch, v, subtline)
        elif subtline.startswith("CCSS.ELA"):
            v -= 40 * point
            c.setFont("Helvetica", 14 * point)
            c.drawString(1 * inch, v, subtline)
        elif i + 1 < len(txt_arr) and txt_arr[i + 1].endswith(":"):
            c.setFont("Helvetica", 14 * point)
            if i - 1 >= 0 and not txt_arr[i - 1].startswith("CCSS.ELA"):
                v -= 40 * point
            c.drawString(1 * inch, v, subtline)
            v -= 8 * point
            c.line(1 * inch, v, width - 1 * inch, v)
        else:
            c.setFont("Helvetica", 10 * point)
            c.drawString(1 * inch, v, "--" + subtline)
        v -= 20 * point
        i += 1

    c.showPage()
    c.save()


# @login_required
# @ensure_csrf_cookie
@csrf_exempt
def get_student_exam_stats(request, phone):
    if request.method == 'GET':
        instance = list(EarlyliteracySkillSetScores.objects.filter(phone_number=phone).order_by('-TestDate')[:3])
        log.warning("Get {} test results for user {}".format(len(instance), phone))
        if not instance or len(instance) <= 0:
            return JsonResponse({"errorCode": "400",
                                 "executed": True,
                                 "message": "User with phone {} does not have any test result!".format(phone),
                                 "success": False}, status=200)
        else:
            scaled_score = instance[0].ScaledScore
            lexile_measure = instance[0].LexileMeasure
            test_date = instance[0].TestDate

            sub_items_alphabetic_principle = [instance[0].AlphabeticKnowledge,
                                              instance[0].AlphabeticSequence,
                                              instance[0].LetterSounds,
                                              instance[0].PrintConceptsWordLength,
                                              instance[0].PrintConceptsWordBorders,
                                              instance[0].PrintConceptsLettersAndWords,
                                              instance[0].Letters,
                                              instance[0].IdentificationAndWordMatching]

            sub_items_phonemic_awareness = [instance[0].RhymingAndWordFamilies,
                                            instance[0].BlendingWordParts,
                                            instance[0].BlendingPhonemes,
                                            instance[0].InitialAndFinalPhonemes,
                                            instance[0].ConsonantBlendsPA,
                                            instance[0].MedialPhonemeDiscrimination,
                                            instance[0].PhonemeIsolationORManipulation,
                                            instance[0].PhonemeSegmentation]

            sub_items_phonics1 = [instance[0].ShortVowelSounds,
                                  instance[0].InitialConsonantSounds,
                                  instance[0].FinalConsonantSounds,
                                  instance[0].LongVowelSounds,
                                  instance[0].VariantVowelSounds,
                                  instance[0].ConsonantBlendsPH]

            sub_items_phonics2 = [instance[0].ConsonantDigraphs,
                                  instance[0].OtherVowelSounds,
                                  instance[0].SoundSymbolCorrespondenceConsonants,
                                  instance[0].WordBuilding,
                                  instance[0].SoundSymbolCorrespondenceVowels,
                                  instance[0].WordFamiliesOrRhyming]

            sub_items_structural_vocabulary = [instance[0].WordsWithAffixes,
                                               instance[0].Syllabification,
                                               instance[0].CompoundWords,
                                               instance[0].WordFacility,
                                               instance[0].Synonyms,
                                               instance[0].Antonyms]

            sub_items_other_domains = [instance[0].ComprehensionATtheSentenceLevel,
                                       instance[0].ComprehensionOfParagraphs,
                                       instance[0].NumberNamingAndNumberIdentification,
                                       instance[0].NumberObjectCorrespondence,
                                       instance[0].SequenceCompletion,
                                       instance[0].ComposingAndDecomposing,
                                       instance[0].Measurement]

            # sub_domain_score = [instance[0].AlphabeticPrinciple, instance[0].ConceptOfWord,
            #                     instance[0].VisualDiscrimination,
            #                     instance[0].Phonics, instance[0].StructuralAnalysis, instance[0].Vocabulary,
            #                     instance[0].SentenceLevelComprehension, instance[0].PhonemicAwareness,
            #                     instance[0].ParagraphLevelComprehension, instance[0].EarlyNumeracy]

            sub_domain_score_trend_date = []
            sub_domain_score_trend_value = []

            for result in reversed(instance):
                sub_domain_score_trend_date.append(result.TestDate)
                sub_domain_score_data = [
                    round((result.AlphabeticPrinciple + result.ConceptOfWord + result.VisualDiscrimination) / 3, 1),
                    result.PhonemicAwareness, result.Phonics, (result.StructuralAnalysis + result.Vocabulary) / 2,
                    round((
                              result.SentenceLevelComprehension + result.ParagraphLevelComprehension + result.EarlyNumeracy) / 3,
                          1)]
                sub_domain_score_trend_value.append(sub_domain_score_data)

            return JsonResponse({
                "test_date": test_date,
                "lexile_measure": lexile_measure,
                "scaled_score": scaled_score,
                "sub_items_alphabetic_principle": sub_items_alphabetic_principle,
                "sub_items_phonemic_awareness": sub_items_phonemic_awareness,
                "sub_items_phonics1": sub_items_phonics1,
                "sub_items_phonics2": sub_items_phonics2,
                "sub_items_structural_vocabulary": sub_items_structural_vocabulary,
                "sub_items_other_domains": sub_items_other_domains,
                "sub_domain_score_trend_date": sub_domain_score_trend_date,
                "sub_domain_score_trend_value": sub_domain_score_trend_value,
                "errorCode": "200",
                "executed": True,
                "message": "Succeed to get latest test result of user {}!".format(phone),
                "success": True
            }, status=200)


# @login_required
# @ensure_csrf_cookie
@csrf_exempt
def ccss_items_management(request, pk=None):
    if request.method == 'GET':
        items = list(MapTestCheckItem.objects.values().order_by('-id'))
        return JsonResponse({
            "data_list": items,
            "errorCode": "200",
            "executed": True,
            "message": "Succeed to get all the map test items!",
            "success": True
        }, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        log.warning(data)
        check_item, created = MapTestCheckItem.objects.update_or_create(
            item_name=data['item_name'], defaults={"l1_domain": data["l1_domain"],
                                                   "l2_sub_domain": data["l2_sub_domain"],
                                                   "l3_grade": data["l3_grade"],
                                                   "item_desc": data["item_desc"]}
        )
        log.warning("result: {}, item: {}".format(created, check_item))
        if created:
            return JsonResponse({
                "errorCode": "201",
                "executed": True,
                "message": "Succeed to create a ccss test item {}!".format(check_item.item_name),
                "success": True
            }, status=201)
        else:
            return JsonResponse({
                "errorCode": "200",
                "executed": True,
                "message": "Succeed to update a ccss test item {}!".format(check_item.item_name),
                "success": True}, status=200)
    elif request.method == 'DELETE':
        MapTestCheckItem.objects.filter(id=pk).delete()
        return JsonResponse({"errorCode": "200",
                             "executed": True,
                             "message": "Deleted a ccss item!",
                             "success": True}, status=200)
