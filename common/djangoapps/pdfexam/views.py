import logging

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
from .parse_helper import ExtractStarData, extract_map_data
from .star_reading_table import draw_star_reading_table

log = logging.getLogger("edx.pdfexam")


# Create your views here.

def choose_file(request):
    temp = loader.get_template('pdf2MySQL/upload_file.html')
    return HttpResponse(temp.render())


def upload_file(request):
    return render(request, 'pdf2MySQL/upload_file.html')


@csrf_exempt
def handle_pdf_data(request):
    # request.Files['myfile']
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
    log.warning("Import {} report for user {}".format(test_type, phonenumber))
    if not phonenumber:
        return JsonResponse({"errorCode": "400",
                             "executed": True,
                             "message": "No phone number input for pdf upload!",
                             "success": False}, status=200)

    if request.method == 'POST':  # 请求方法为POST时，进行处理
        try:
            myFile = request.FILES['myfile']  # 获取上传的文件，如果没有文件，则默认为None
        except MultiValueDictKeyError as err:
            log.warning(err)
            return JsonResponse({"errorCode": "400",
                                 "executed": True,
                                 "message": "Need to choose a PDF file for upload. {}!".format(err),
                                 "success": False}, status=200)
        if not myFile:
            return JsonResponse({"errorCode": "400",
                                 "executed": True,
                                 "message": "No file was uploaded!",
                                 "success": False}, status=200)

        destination = open(os.path.join(settings.MEDIA_ROOT, myFile.name), 'wb+')  # 打开特定的文件进行二进制的写操作

        for chunk in myFile.chunks():  # 分块写入文件
            destination.write(chunk)

        destination.close()

        ################################################################
        #  trans to txt file and stored in txtintermediate dictionary
        ################################################################
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
            # print(content)

        ################################################################
        #  trans end
        ################################################################
        try:
            if test_type == "star_early":
                ExtractStarData(content, phonenumber)
            elif test_type == "map_test":
                stu_map_pro = extract_map_data(content, phonenumber)
                draw_map_table(stu_map_pro)
            elif test_type == "star_reading":
                draw_star_reading_table()
            else:
                raise
        except Exception as err:
            log.error(err)
            log.error("Upload pdf {} failed!".format(myFile.name))
            temp = loader.get_template('pdf2MySQL/show_failed.html')
        else:
            temp = loader.get_template('pdf2MySQL/show_success.html')

        os.remove(pdffilestored)
        return HttpResponse(temp.render())


def show(self, request):
    temp = loader.get_template('pdf2MySQL/show_success.html')
    return HttpResponse(temp.render())


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
