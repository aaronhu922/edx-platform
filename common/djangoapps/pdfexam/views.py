import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from io import open
import os
import pdfplumber
import re
import json
import datetime
from .models import EarlyliteracySkillSetScores as EarlyliteracySkillSetScores
from django.http import JsonResponse

log = logging.getLogger("edx.pdfexam")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create your views here.

def choose_file(request):
    temp = loader.get_template('pdf2MySQL/upload_file.html')
    return HttpResponse(temp.render())

def upload_file(request):
    return render(request, 'pdf2MySQL/upload_file.html')


@csrf_exempt
def Handle(request):
    # request.Files['myfile']
    if 'phone_number' not in request.POST:
        return HttpResponse("No phone_number for pdf importing!")

    phonenumber = request.POST['phone_number']
    log.warning(phonenumber)

    if request.method == 'POST':  # 请求方法为POST时，进行处理
        myFile = request.FILES['myfile']  # 获取上传的文件，如果没有文件，则默认为None
        if not myFile:
            return HttpResponse("no files for upload!")

        destination = open(os.path.join(BASE_DIR, 'pdfsource', myFile.name), 'wb+')  # 打开特定的文件进行二进制的写操作

        for chunk in myFile.chunks():  # 分块写入文件
            destination.write(chunk)

        destination.close()

        ################################################################
        #  trans to txt file and stored in txtintermediate dictionary
        ################################################################
        pdffilestored = os.path.join(BASE_DIR, 'pdfsource', myFile.name)


        with pdfplumber.open(pdffilestored) as pdf:
            content = ''
            # len(pdf.pages)为PDF文档页数
            for i in range(len(pdf.pages)):
                # pdf.pages[i] 是读取PDF文档第i+1页
                page = pdf.pages[i]
                # page.extract_text()函数即读取文本内容，下面这步是去掉文档最下面的页码
                page_content = '\n'.join(page.extract_text().split('\n')[:-1])
                content = content + page_content
            # print(content)

        pdffilenameportion = os.path.splitext(myFile.name)

        txtfilename = pdffilenameportion[0] + '.txt'

        txtfilestored = os.path.join(BASE_DIR, 'txtintermediate', txtfilename)

        with open(txtfilestored, "w", encoding='utf-8') as f:
            f.write(content)

        ################################################################
        #  trans end
        ################################################################

    ExtractData(txtfilestored, phonenumber)

    return HttpResponse('upload over!')


def ExtractData(pathfilename, phonenumber):
    StarEarlyLiteracyPDFReportExtractListBriefInfo = ['FirstName', 'FamilyName', 'ID', 'PrintedDay', 'PrintedDateTime', \
                                                      'Reporting Period', 'SchoolYear', 'School', 'Class', 'Grade', \
                                                      'Teacher', 'Test Date', 'SS', 'Lexile® Measure', \
                                                      'Lexile® Rangeb', \
                                                      'Estimated Oral Reading Fluency (Words Correct Per Minute)']

    StarEarlyLiteracyPDFReportExtractListSubDomainCollectScore = ['Alphabetic Principle', 'Concept of Word', \
                                                                  'Visual Discrimination', 'Phonemic Awareness',
                                                                  'Phonics', \
                                                                  'Structural Analysis', 'Vocabulary', \
                                                                  'Sentence-Level Comprehension', \
                                                                  'Paragraph-Level Comprehension', 'Early Numeracy']

    StarEarlyLiteracyPDFReportExtractListSubDomainDetail = ['Alphabetic Knowledge', 'Alphabetic Sequence', \
                                                            'Letter Sounds', 'Print Concepts: Word length', \
                                                            'Print Concepts: Word borders', \
                                                            'Print Concepts: Letters and Words', 'Letters', \
                                                            'Identification and Word Matching', \
                                                            'Rhyming and Word Families', 'Blending Word Parts', \
                                                            'Blending Phonemes', 'Initial and Final Phonemes', \
                                                            'Consonant Blends (PA)', 'Medial Phoneme Discrimination', \
                                                            'Phoneme Isolation/Manipulation', 'Phoneme Segmentation', \
                                                            'Short Vowel Sounds', 'Initial Consonant Sounds', \
                                                            'Final Consonant Sounds', 'Long Vowel Sounds', \
                                                            'Variant Vowel Sounds', 'Consonant Blends (PH)', \
                                                            'Consonant Digraphs', 'Other Vowel Sounds', \
                                                            'Sound-Symbol Correspondence: Consonants', 'Word Building', \
                                                            'Sound-Symbol Correspondence: Vowels', \
                                                            'Word Families/Rhyming', 'Words with Affixes', \
                                                            'Syllabification', 'Compound Words', 'Word Facility', \
                                                            'Synonyms', 'Antonyms', \
                                                            'Comprehension at the Sentence Level', \
                                                            'Comprehension of Paragraphs', \
                                                            'Number Naming and Number Identification', \
                                                            'Number Object Correspondence', 'Sequence Completion', \
                                                            'Composing and Decomposing', 'Measurement']

    ExtractDataFromStarEarlyLiteracyBriefInfoDict = dict.fromkeys(StarEarlyLiteracyPDFReportExtractListBriefInfo)
    ExtractDataFromStarEarlyLiteracySubDomainCollectScoreDict = dict.fromkeys(StarEarlyLiteracyPDFReportExtractListSubDomainCollectScore)
    ExtractDataFromStarEarlyLiteracySubDomainDetailScoreDict = dict.fromkeys(StarEarlyLiteracyPDFReportExtractListSubDomainDetail)
    ExtractDataFromStarEarlyLiteracySubDomainNStepSymbolDict = dict.fromkeys(StarEarlyLiteracyPDFReportExtractListSubDomainDetail)

    ExtractSubDomainNStepSymbolDict = {}

    ##################################################################
    ##    Open the data txtfile, which from pdfplumber
    #################################################################

    with open(pathfilename) as f:
        data = f.read()


    ##################################################################
    ##    定制对报告的简要信息的提取正则表达式  Extract Brief Info
    #################################################################


    for KeyItem in StarEarlyLiteracyPDFReportExtractListBriefInfo:
        source = KeyItem

        if source == "Estimated Oral Reading Fluency (Words Correct Per Minute)":
            ###################################################
            # eliminate the parentheses in regular expression
            ##################################################
            source = "Estimated Oral Reading Fluency [(]Words Correct Per Minute[)]"
            ExtractRegex = "(?<=" + source + "\:\s)\d+"
        elif source == "Class" or source == "ID":
            ExtractRegex = "(?<=" + source + "\:)\w+"
        elif source == "Teacher":
            ExtractRegex = "(?<=" + source + "\:)\w+\.\s+\w+"
        elif source == "School":
            #   需要注意此正则表达式局限性很强,only for "Fly High Education 3" model
            ExtractRegex = "(?<=" + source + "\:\s)\w+\s\w+\s\w+\s\w+"
        elif source == "Test Date":
            # 日期格式 月/日/年
            ExtractRegex = "(?<=" + source + "\:\s)\d+/\d+/\d+"
        elif source == "PrintedDay":
            source = "Printed"
            # 格式 Saturday, February 22, 2020 2:30:17 PM
            ExtractRegex = "(?<=" + source + "\s)\w+"
        elif source == "Reporting Period":
            # 格式 1/27/2020 - 1/26/2021
            # the django models definition are "ReportingPeriodStart" and "ReportingPeriodEnd", but not "Reporting Period"
            # So, there need be split. I split the "1/27/2020 - 1/26/2021" into Start and End at the  segment code where
            # Preparing dict for ExtractDataDictReady2DjangoModel{}
            ExtractRegex = "(?<=" + source + "\:\s)\d+/\d+/\d+\s" + '-\s' + "\d+/\d+/\d+"
        elif source == "Lexile® Rangeb":
            ExtractRegex = "(?<=" + source + "\:\s)\S+"
        elif source == "PrintedDateTime":
            source = "Printed"
            # 格式 Saturday, February 22, 2020 2:30:17 PM
            ExtractRegex = "(?<=" + source + "\s)\w+\S\s\w+\s\w+\S\s\w+\s\w+\:\w+\:\w+\s\w+"
        elif source == 'FirstName' or source == 'FamilyName':
            ## 姓名的信息来源因为同ID,使用ID数据, 目前符合应用场景的业务逻辑
            source = 'ID'
            ExtractRegex = "(?<=" + source + "\:)\w+"
        elif source == 'SchoolYear':
            ExtractRegex = "\(" + "\d{4}" + '-' + "\d{4}\)"
        else:
            ExtractRegex = "(?<=" + source + "\:\s)\w+"

        value = re.findall(ExtractRegex, data)

        if source == 'SchoolYear':
            value[0] = value[0].strip('(')
            value[0] = value[0].strip(')')

        ExtractDataFromStarEarlyLiteracyBriefInfoDict[KeyItem] = value[0]

        if KeyItem == 'Test Date':
            ##################################################################################
            ##  change date format MM/DD/YYYY to YYYY-MM-DD
            ##  Sample Code:
            ##  #import datetime
            #   datetime.datetime.strptime("21/12/2008", "%d/%m/%Y").strftime("%Y-%m-%d")
            ##################################################################################
            ExtractDataFromStarEarlyLiteracyBriefInfoDict['Test Date'] = datetime.datetime.strptime(value[0], "%m/%d/%Y").strftime("%Y-%m-%d")

            #################################################################
            ## Change date format END
            #################################################################

        if KeyItem == 'PrintedDateTime':
            ################################################################
            ##  remove the "day, " from  "day, MM DD, YYYY HH:MM:ss pm"
            ################################################################
            PrintedDateTimeStr = ExtractDataFromStarEarlyLiteracyBriefInfoDict[KeyItem]
            RemoveDayRegex = "\,\s\w+\s\w+\,\s\w+\s\w+\:\w+\:\w+\s\w+"
            value = re.findall(RemoveDayRegex, PrintedDateTimeStr)
            sourceStr = ","
            RemoveCommaAndBlankSpaceRegex = "(?<=" + sourceStr + "\s)\w+\s\w+\,\s\w+\s\w+\:\w+\:\w+\s\w+"
            value = re.findall(RemoveCommaAndBlankSpaceRegex, value[0])
            ExtractDataFromStarEarlyLiteracyBriefInfoDict['PrintedDateTime'] = value[0]

    #################################################################
    ##  Brief Info Extract End
    #################################################################


    ##################################################################
    ##     Extract Sub Domain Collect Score
    ##################################################################

    for KeyItem in StarEarlyLiteracyPDFReportExtractListSubDomainCollectScore:
        source = KeyItem
        ExtractScoreRegex = "(?<=" + source + "\s)\s?\d+"
        value = re.findall(ExtractScoreRegex, data)
        ExtractDataFromStarEarlyLiteracySubDomainCollectScoreDict[KeyItem] = value[0]

    #################################################################
    ##  Sub Domain Collect Score Extracted End
    #################################################################


    ##################################################################
    ##     Extract Sub Domain Detail Score
    ##################################################################

    for KeyItem in StarEarlyLiteracyPDFReportExtractListSubDomainDetail:
        source = KeyItem

        ###################################################
        # eliminate the parentheses in regular expression
        ##################################################
        if source == "Consonant Blends (PA)":
            source = "Consonant Blends [(]PA[)]"
        elif source == "Consonant Blends (PH)":
            source = "Consonant Blends [(]PH[)]"

        ExtractScoreRegex = "(?<=" + source + "\s)\s?\d+"

        value = re.findall(ExtractScoreRegex, data)

        ExtractDataFromStarEarlyLiteracySubDomainDetailScoreDict[KeyItem] = value[0]

    #################################################################
    ##  Sub Domain Detail Score  End
    #################################################################


    ##################################################################
    ##   Extract Sub Domain Next-Step Symbol
    ##################################################################

    for KeyItem in StarEarlyLiteracyPDFReportExtractListSubDomainDetail:
        source = KeyItem

        ###################################################
        # eliminate the parentheses in regular expression
        ##################################################
        if source == "Consonant Blends (PA)":
            source = "Consonant Blends [(]PA[)]"
        elif source == "Consonant Blends (PH)":
            source = "Consonant Blends [(]PH[)]"

        ExtractNextStepSymbolRegex = "}(?=" + source + ')'

        NextStepSymbol = re.findall(ExtractNextStepSymbolRegex, data)

        if len(NextStepSymbol) == 0:
            ExtractDataFromStarEarlyLiteracySubDomainNStepSymbolDict[KeyItem] = "False"
        elif NextStepSymbol[0] == '}':
            ExtractDataFromStarEarlyLiteracySubDomainNStepSymbolDict[KeyItem] = "True"

    ##################################################################
    ##     Extract Sub Domain Next-Step Symbol END
    ##################################################################


    ############################################################################
    ##     Merge the Extract Data from 4 Dictionary, and at first alignment the
    #      Next Step Symbol DICT's Key for Merge all DICT'S Key in the for loop
    ############################################################################

    for KeyItem in ExtractDataFromStarEarlyLiteracySubDomainNStepSymbolDict:
        NSKeyItem = "NextStep" + KeyItem
        ExtractSubDomainNStepSymbolDict[NSKeyItem] = ExtractDataFromStarEarlyLiteracySubDomainNStepSymbolDict[KeyItem]

    ExtractDataDictMergeTemp = ExtractDataFromStarEarlyLiteracyBriefInfoDict.copy()
    ExtractDataDictMergeTemp.update(ExtractDataFromStarEarlyLiteracySubDomainCollectScoreDict)
    ExtractDataDictMergeTemp.update(ExtractDataFromStarEarlyLiteracySubDomainDetailScoreDict)
    ExtractDataDictMergeTemp.update(ExtractSubDomainNStepSymbolDict)

    ##################################################################
    ##     Merge the Extract Data END
    ##################################################################

    ##############################################################################
    ## Save the Extract Info in a txtfile, and the name in parttern xxxx.dict.txt
    ##############################################################################

    ExtractDataDictMergeTempConvert2Str = json.dumps(ExtractDataDictMergeTemp)

    Dictfilenameportion = os.path.splitext(pathfilename)

    Dicttxtfilename = Dictfilenameportion[0] + '.dict.txt'

    Dicttxtfilestored = os.path.join(BASE_DIR, 'txtintermediate', Dicttxtfilename)

    with open(Dicttxtfilestored, "w", encoding='utf-8') as f:
        f.write(ExtractDataDictMergeTempConvert2Str)

    ##############################################################################
    ## Save the Extract Info END
    ##############################################################################


    ##################################################################
    ## alignment the dict's key for importing  into Django Models
    ##################################################################
    DictKeys2List = ExtractDataDictMergeTemp.keys()

    ExtractDataDictReady2DjangoModel = {}

    ExtractDataDictReady2DjangoModel['phone_number'] = phonenumber

    for KeyItem in DictKeys2List:
        if KeyItem == 'FirstName':
            ExtractDataDictReady2DjangoModel['FirstName'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'FamilyName':
            ExtractDataDictReady2DjangoModel['FamilyName'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'ID':
            ExtractDataDictReady2DjangoModel['STARPlatformStudentID'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'PrintedDay':
            ExtractDataDictReady2DjangoModel['PrintDay'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'PrintedDateTime':
            ExtractDataDictReady2DjangoModel['PrintDateTime'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Reporting Period':
            # split ReportPeriodStart and  ReportPeriodEnd from ExtractDataDictMergeTemp["Report Period"]
            # source Reporting Period is string:"1/27/2020 - 1/26/2021"
            # THere need trans formation MM/DD/YYYY to YYYY-MM-DD after take apart with "Reporting Period"
            source = ExtractDataDictMergeTemp[KeyItem]
            ExtractRegex = "\d+/\d+/\d+"
            value = re.findall(ExtractRegex, source)

            ##################################################################################
            ##  change date format MM/DD/YYYY to YYYY-MM-DD
            ##  Sample Code:
            ##  #import datetime
            #   datetime.datetime.strptime("21/12/2008", "%d/%m/%Y").strftime("%Y-%m-%d")
            ##################################################################################

            ExtractDataDictReady2DjangoModel['ReportPeriodStart'] = datetime.datetime.strptime(value[0], "%m/%d/%Y").strftime("%Y-%m-%d")

            ExtractDataDictReady2DjangoModel['ReportPeriodEnd'] = datetime.datetime.strptime(value[1], "%m/%d/%Y").strftime("%Y-%m-%d")
            #################################################################
            ## Change date format END
            #################################################################

        if KeyItem == 'SchoolYear':
            ExtractDataDictReady2DjangoModel['SchoolYear'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'School':
            ExtractDataDictReady2DjangoModel['SchoolName'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Class':
            ExtractDataDictReady2DjangoModel['Class'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Grade':
            ExtractDataDictReady2DjangoModel['Grade'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Teacher':
            ExtractDataDictReady2DjangoModel['TeacherName'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Test Date':
            ExtractDataDictReady2DjangoModel['TestDate'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'SS':
            ExtractDataDictReady2DjangoModel['ScaledScore'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Lexile® Measure':
            ExtractDataDictReady2DjangoModel['LexileMeasure'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Lexile® Rangeb':
            ExtractDataDictReady2DjangoModel['LexileRange'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Estimated Oral Reading Fluency (Words Correct Per Minute)':
            ExtractDataDictReady2DjangoModel['EstORF'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Alphabetic Principle':
            ExtractDataDictReady2DjangoModel['AlphabeticPrinciple'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Concept of Word':
            ExtractDataDictReady2DjangoModel['ConceptOfWord'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Visual Discrimination':
            ExtractDataDictReady2DjangoModel['VisualDiscrimination'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Phonemic Awareness':
            ExtractDataDictReady2DjangoModel['PhonemicAwareness'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Phonics':
            ExtractDataDictReady2DjangoModel['Phonics'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Structural Analysis':
            ExtractDataDictReady2DjangoModel['StructuralAnalysis'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Vocabulary':
            ExtractDataDictReady2DjangoModel['Vocabulary'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Sentence-Level Comprehension':
            ExtractDataDictReady2DjangoModel['SentenceLevelComprehension'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Paragraph-Level Comprehension':
            ExtractDataDictReady2DjangoModel['ParagraphLevelComprehension'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Early Numeracy':
            ExtractDataDictReady2DjangoModel['EarlyNumeracy'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Alphabetic Knowledge':
            ExtractDataDictReady2DjangoModel['AlphabeticKnowledge'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Alphabetic Sequence':
            ExtractDataDictReady2DjangoModel['AlphabeticSequence'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Letter Sounds':
            ExtractDataDictReady2DjangoModel['LetterSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Print Concepts: Word length':
            ExtractDataDictReady2DjangoModel['PrintConceptsWordLength'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Print Concepts: Word borders':
            ExtractDataDictReady2DjangoModel['PrintConceptsWordBorders'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Print Concepts: Letters and Words':
            ExtractDataDictReady2DjangoModel['PrintConceptsLettersAndWords'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Letters':
            ExtractDataDictReady2DjangoModel['Letters'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Identification and Word Matching':
            ExtractDataDictReady2DjangoModel['IdentificationAndWordMatching'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Rhyming and Word Families':
            ExtractDataDictReady2DjangoModel['RhymingAndWordFamilies'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Blending Word Parts':
            ExtractDataDictReady2DjangoModel['BlendingWordParts'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Blending Phonemes':
            ExtractDataDictReady2DjangoModel['BlendingPhonemes'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Initial and Final Phonemes':
            ExtractDataDictReady2DjangoModel['InitialAndFinalPhonemes'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Consonant Blends (PA)':
            ExtractDataDictReady2DjangoModel['ConsonantBlendsPA'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Medial Phoneme Discrimination':
            ExtractDataDictReady2DjangoModel['MedialPhonemeDiscrimination'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Phoneme Isolation/Manipulation':
            ExtractDataDictReady2DjangoModel['PhonemeIsolationORManipulation'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Phoneme Segmentation':
            ExtractDataDictReady2DjangoModel['PhonemeSegmentation'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Short Vowel Sounds':
            ExtractDataDictReady2DjangoModel['ShortVowelSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Initial Consonant Sounds':
            ExtractDataDictReady2DjangoModel['InitialConsonantSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Final Consonant Sounds':
            ExtractDataDictReady2DjangoModel['FinalConsonantSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Long Vowel Sounds':
            ExtractDataDictReady2DjangoModel['LongVowelSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Variant Vowel Sounds':
            ExtractDataDictReady2DjangoModel['VariantVowelSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Consonant Blends (PH)':
            ExtractDataDictReady2DjangoModel['ConsonantBlendsPH'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Consonant Digraphs':
            ExtractDataDictReady2DjangoModel['ConsonantDigraphs'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Other Vowel Sounds':
            ExtractDataDictReady2DjangoModel['OtherVowelSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Sound-Symbol Correspondence: Consonants':
            ExtractDataDictReady2DjangoModel['SoundSymbolCorrespondenceConsonants'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Word Building':
            ExtractDataDictReady2DjangoModel['WordBuilding'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Sound-Symbol Correspondence: Vowels':
            ExtractDataDictReady2DjangoModel['SoundSymbolCorrespondenceVowels'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Word Families/Rhyming':
            ExtractDataDictReady2DjangoModel['WordFamiliesOrRhyming'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Words with Affixes':
            ExtractDataDictReady2DjangoModel['WordsWithAffixes'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Syllabification':
            ExtractDataDictReady2DjangoModel['Syllabification'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Compound Words':
            ExtractDataDictReady2DjangoModel['CompoundWords'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Word Facility':
            ExtractDataDictReady2DjangoModel['WordFacility'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Synonyms':
            ExtractDataDictReady2DjangoModel['Synonyms'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Antonyms':
            ExtractDataDictReady2DjangoModel['Antonyms'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Comprehension at the Sentence Level':
            ExtractDataDictReady2DjangoModel['ComprehensionATtheSentenceLevel'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Comprehension of Paragraphs':
            ExtractDataDictReady2DjangoModel['ComprehensionOfParagraphs'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Number Naming and Number Identification':
            ExtractDataDictReady2DjangoModel['NumberNamingAndNumberIdentification'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Number Object Correspondence':
            ExtractDataDictReady2DjangoModel['NumberObjectCorrespondence'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Sequence Completion':
            ExtractDataDictReady2DjangoModel['SequenceCompletion'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Composing and Decomposing':
            ExtractDataDictReady2DjangoModel['ComposingAndDecomposing'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'Measurement':
            ExtractDataDictReady2DjangoModel['Measurement'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepAlphabetic Knowledge':
            ExtractDataDictReady2DjangoModel['NextStepForAlphabeticKnowledge'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepAlphabetic Sequence':
            ExtractDataDictReady2DjangoModel['NextStepForAlphabeticSequence'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepLetter Sounds':
            ExtractDataDictReady2DjangoModel['NextStepForLetterSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepPrint Concepts: Word length':
            ExtractDataDictReady2DjangoModel['NextStepForPrintConceptsWordLength'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepPrint Concepts: Word borders':
            ExtractDataDictReady2DjangoModel['NextStepForPrintConceptsWordBorders'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepPrint Concepts: Letters and Words':
            ExtractDataDictReady2DjangoModel['NextStepForPrintConceptsLettersAndWords'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepLetters':
            ExtractDataDictReady2DjangoModel['NextStepForLetters'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepIdentification and Word Matching':
            ExtractDataDictReady2DjangoModel['NextStepForIdentificationAndWordMatching'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepRhyming and Word Families':
            ExtractDataDictReady2DjangoModel['NextStepForRhymingAndWordFamilies'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepBlending Word Parts':
            ExtractDataDictReady2DjangoModel['NextStepForBlendingWordParts'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepBlending Phonemes':
            ExtractDataDictReady2DjangoModel['NextStepForBlendingPhonemes'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepInitial and Final Phonemes':
            ExtractDataDictReady2DjangoModel['NextStepForInitialAndFinalPhonemes'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepConsonant Blends (PA)':
            ExtractDataDictReady2DjangoModel['NextStepForConsonantBlendsPA'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepMedial Phoneme Discrimination':
            ExtractDataDictReady2DjangoModel['NextStepForMedialPhonemeDiscrimination'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepPhoneme Isolation/Manipulation':
            ExtractDataDictReady2DjangoModel['NextStepForPhonemeIsolationORManipulation'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepPhoneme Segmentation':
            ExtractDataDictReady2DjangoModel['NextStepForPhonemeSegmentation'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepShort Vowel Sounds':
            ExtractDataDictReady2DjangoModel['NextStepForShortVowelSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepInitial Consonant Sounds':
            ExtractDataDictReady2DjangoModel['NextStepForInitialConsonantSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepFinal Consonant Sounds':
            ExtractDataDictReady2DjangoModel['NextStepForFinalConsonantSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepLong Vowel Sounds':
            ExtractDataDictReady2DjangoModel['NextStepForLongVowelSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepVariant Vowel Sounds':
            ExtractDataDictReady2DjangoModel['NextStepForVariantVowelSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepConsonant Blends (PH)':
            ExtractDataDictReady2DjangoModel['NextStepForConsonantBlendsPH'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepConsonant Digraphs':
            ExtractDataDictReady2DjangoModel['NextStepForConsonantDigraphs'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepOther Vowel Sounds':
            ExtractDataDictReady2DjangoModel['NextStepForOtherVowelSounds'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepSound-Symbol Correspondence: Consonants':
            ExtractDataDictReady2DjangoModel['NextStepForSoundSymbolCorrespondenceConsonants'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepWord Building':
            ExtractDataDictReady2DjangoModel['NextStepForWordBuilding'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepSound-Symbol Correspondence: Vowels':
            ExtractDataDictReady2DjangoModel['NextStepForSoundSymbolCorrespondenceVowels'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepWord Families/Rhyming':
            ExtractDataDictReady2DjangoModel['NextStepForWordFamiliesOrRhyming'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepWords with Affixes':
            ExtractDataDictReady2DjangoModel['NextStepForWordsWithAffixes'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepSyllabification':
            ExtractDataDictReady2DjangoModel['NextStepForSyllabification'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepCompound Words':
            ExtractDataDictReady2DjangoModel['NextStepForCompoundWords'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepWord Facility':
            ExtractDataDictReady2DjangoModel['NextStepForWordFacility'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepSynonyms':
            ExtractDataDictReady2DjangoModel['NextStepForSynonyms'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepAntonyms':
            ExtractDataDictReady2DjangoModel['NextStepForAntonyms'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepComprehension at the Sentence Level':
            ExtractDataDictReady2DjangoModel['NextStepForComprehensionATtheSentenceLevel'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepComprehension of Paragraphs':
            ExtractDataDictReady2DjangoModel['NextStepForComprehensionOfParagraphs'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepNumber Naming and Number Identification':
            ExtractDataDictReady2DjangoModel['NextStepForNumberNamingAndNumberIdentification'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepNumber Object Correspondence':
            ExtractDataDictReady2DjangoModel['NextStepForNumberObjectCorrespondence'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepSequence Completion':
            ExtractDataDictReady2DjangoModel['NextStepForSequenceCompletion'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepComposing and Decomposing':
            ExtractDataDictReady2DjangoModel['NextStepForComposingAndDecomposing'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepMeasurement':
            ExtractDataDictReady2DjangoModel['NextStepForMeasurement'] = ExtractDataDictMergeTemp[KeyItem]

    ####################################################################################################################
    ## Prepare the ExtractDataDictReady2DjangoModel Dict END
    ####################################################################################################################



    ####################################################################################################################
    ## Save the Django models formation  Extract Data in a txtfile, and the name in parttern xxxx.djangomodels.dict.txt
    ####################################################################################################################

    # ExtractDataDictReady2DjangoModelConvert2Str = json.dumps(ExtractDataDictReady2DjangoModel)
    #
    # DjangomodelsDictfilenameportion = os.path.splitext(pathfilename)
    #
    # DjangomodelsDicttxtfilename = DjangomodelsDictfilenameportion[0] + '.djangomodels.dict.txt'
    #
    # DjangomodelsDicttxtfilestored = os.path.join(BASE_DIR, 'txtintermediate', DjangomodelsDicttxtfilename)
    #
    # with open(DjangomodelsDicttxtfilestored, "w", encoding='utf-8') as f:
    #     f.write(ExtractDataDictReady2DjangoModelConvert2Str)

    ####################################################################################################################
    ## Save the Django models formation  Extract Data in a file END
    ####################################################################################################################

    # ReportDataStr = json.dumps(ExtractDataDictReady2DjangoModel)

    EarlyliteracySkillSetScores.objects.create(**ExtractDataDictReady2DjangoModel)


def show(self, request):
    temp = loader.get_template('pdf2MySQL/show.html')
    return HttpResponse(temp.render())


def get_student_exam_stats(request, phone):
    if request.method == 'GET':
        instance = list(EarlyliteracySkillSetScores.objects.filter(phone_number=phone).order_by('-TestDate'))
        log.warning("Get {} test results for user {}".format(len(instance), phone))
        if not instance or len(instance) <= 0:
            return JsonResponse({"errorCode": "400",
                                 "executed": True,
                                 "message": "User with phone {} does not have any test result!".format(phone),
                                 "success": False}, status=200)
        else:
            ScaledScore = instance[0].ScaledScore
            sub_domain_score = [instance[0].AlphabeticPrinciple, instance[0].ConceptOfWord, instance[0].VisualDiscrimination,
                                instance[0].Phonics, instance[0].StructuralAnalysis, instance[0].Vocabulary,
                                instance[0].SentenceLevelComprehension, instance[0].PhonemicAwareness,
                                instance[0].ParagraphLevelComprehension, instance[0].EarlyNumeracy]
            sub_items_score = [instance[0].AlphabeticKnowledge,
                               instance[0].AlphabeticSequence,
                               instance[0].LetterSounds,
                               instance[0].PrintConceptsWordLength,
                               instance[0].PrintConceptsWordBorders,
                               instance[0].PrintConceptsLettersAndWords,
                               instance[0].Letters,
                               instance[0].IdentificationAndWordMatching,
                               instance[0].RhymingAndWordFamilies,
                               instance[0].BlendingWordParts,
                               instance[0].BlendingPhonemes,
                               instance[0].InitialAndFinalPhonemes,
                               instance[0].ConsonantBlendsPA,
                               instance[0].MedialPhonemeDiscrimination,
                               instance[0].PhonemeIsolationORManipulation,
                               instance[0].PhonemeSegmentation,
                               instance[0].ShortVowelSounds,
                               instance[0].InitialConsonantSounds,
                               instance[0].FinalConsonantSounds,
                               instance[0].LongVowelSounds,
                               instance[0].VariantVowelSounds,
                               instance[0].ConsonantBlendsPH,
                               instance[0].ConsonantDigraphs,
                               instance[0].OtherVowelSounds,
                               instance[0].SoundSymbolCorrespondenceConsonants,
                               instance[0].WordBuilding,
                               instance[0].SoundSymbolCorrespondenceVowels,
                               instance[0].WordFamiliesOrRhyming,
                               instance[0].WordsWithAffixes,
                               instance[0].Syllabification,
                               instance[0].CompoundWords,
                               instance[0].WordFacility,
                               instance[0].Synonyms,
                               instance[0].Antonyms,
                               instance[0].ComprehensionATtheSentenceLevel,
                               instance[0].ComprehensionOfParagraphs,
                               instance[0].NumberNamingAndNumberIdentification,
                               instance[0].NumberObjectCorrespondence,
                               instance[0].SequenceCompletion,
                               instance[0].ComposingAndDecomposing,
                               instance[0].Measurement]

            scaled_scores_trend = {}
            sub_domain_score_trend = {}
            for result in instance:
                scaled_scores_trend[str(result.TestDate)] = result.ScaledScore
                sub_domain_score_trend[str(result.TestDate)] = [result.AlphabeticPrinciple, result.ConceptOfWord,
                                                           result.VisualDiscrimination,
                                                           result.Phonics, result.StructuralAnalysis, result.Vocabulary,
                                                           result.SentenceLevelComprehension, result.PhonemicAwareness,
                                                           result.ParagraphLevelComprehension, result.EarlyNumeracy]
            return JsonResponse({
                "scaled_score": ScaledScore,
                "sub_domain_score": sub_domain_score,
                "sub_items_score": sub_items_score,
                "scaled_scores_trend": scaled_scores_trend,
                "sub_domain_score_trend": sub_domain_score_trend,
                "errorCode": "200",
                "executed": True,
                "message": "Succeed to get latest test result of user {}!".format(phone),
                "success": True
            }, status=200)
