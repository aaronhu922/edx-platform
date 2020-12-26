from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from io import open
import os
import re
import json
import datetime
from .models import MapStudentProfile, EarlyliteracySkillSetScores, MapProfileExtResults
from django.conf import settings


def ExtractStarData(pathfilename, phonenumber):
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
    ExtractDataFromStarEarlyLiteracySubDomainCollectScoreDict = dict.fromkeys(
        StarEarlyLiteracyPDFReportExtractListSubDomainCollectScore)
    ExtractDataFromStarEarlyLiteracySubDomainDetailScoreDict = dict.fromkeys(
        StarEarlyLiteracyPDFReportExtractListSubDomainDetail)
    ExtractDataFromStarEarlyLiteracySubDomainNStepSymbolDict = dict.fromkeys(
        StarEarlyLiteracyPDFReportExtractListSubDomainDetail)

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
            ExtractDataFromStarEarlyLiteracyBriefInfoDict['Test Date'] = datetime.datetime.strptime(value[0],
                                                                                                    "%m/%d/%Y").strftime(
                "%Y-%m-%d")

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

    Dicttxtfilestored = os.path.join(settings.MEDIA_ROOT, Dicttxtfilename)

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

            ExtractDataDictReady2DjangoModel['ReportPeriodStart'] = datetime.datetime.strptime(value[0],
                                                                                               "%m/%d/%Y").strftime(
                "%Y-%m-%d")

            ExtractDataDictReady2DjangoModel['ReportPeriodEnd'] = datetime.datetime.strptime(value[1],
                                                                                             "%m/%d/%Y").strftime(
                "%Y-%m-%d")
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
            ExtractDataDictReady2DjangoModel['NextStepForPrintConceptsLettersAndWords'] = ExtractDataDictMergeTemp[
                KeyItem]

        if KeyItem == 'NextStepLetters':
            ExtractDataDictReady2DjangoModel['NextStepForLetters'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepIdentification and Word Matching':
            ExtractDataDictReady2DjangoModel['NextStepForIdentificationAndWordMatching'] = ExtractDataDictMergeTemp[
                KeyItem]

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
            ExtractDataDictReady2DjangoModel['NextStepForMedialPhonemeDiscrimination'] = ExtractDataDictMergeTemp[
                KeyItem]

        if KeyItem == 'NextStepPhoneme Isolation/Manipulation':
            ExtractDataDictReady2DjangoModel['NextStepForPhonemeIsolationORManipulation'] = ExtractDataDictMergeTemp[
                KeyItem]

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
            ExtractDataDictReady2DjangoModel['NextStepForSoundSymbolCorrespondenceConsonants'] = \
                ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepWord Building':
            ExtractDataDictReady2DjangoModel['NextStepForWordBuilding'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepSound-Symbol Correspondence: Vowels':
            ExtractDataDictReady2DjangoModel['NextStepForSoundSymbolCorrespondenceVowels'] = ExtractDataDictMergeTemp[
                KeyItem]

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
            ExtractDataDictReady2DjangoModel['NextStepForComprehensionATtheSentenceLevel'] = ExtractDataDictMergeTemp[
                KeyItem]

        if KeyItem == 'NextStepComprehension of Paragraphs':
            ExtractDataDictReady2DjangoModel['NextStepForComprehensionOfParagraphs'] = ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepNumber Naming and Number Identification':
            ExtractDataDictReady2DjangoModel['NextStepForNumberNamingAndNumberIdentification'] = \
                ExtractDataDictMergeTemp[KeyItem]

        if KeyItem == 'NextStepNumber Object Correspondence':
            ExtractDataDictReady2DjangoModel['NextStepForNumberObjectCorrespondence'] = ExtractDataDictMergeTemp[
                KeyItem]

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

    EarlyliteracySkillSetScores.objects.update_or_create(phone_number=phonenumber,
                                                         TestDate=ExtractDataDictReady2DjangoModel['TestDate'],
                                                         defaults=ExtractDataDictReady2DjangoModel)


def ExtractDataMap(pathfilename):
    InstructionalAreas = []

    InstructionalAreas = ["Informational Text: Key Ideas and Details", "Vocabulary: Acquisition and Use", \
                          "Informational Text: Language, Craft, and Structure", \
                          "Literary Text: Language, Craft, and Structure", "Literary Text: Key Ideas and Details"]

    MapnweaStudentProfileSummaryINFO = ['ExportDate', 'ExportStaff', 'FirstName', 'FamilyName', 'Grade', 'ID', \
                                        'TestCategory', 'Standard Error', 'Possible range', 'TestDate', 'TestDuration', \
                                        'Rapid-Guessing %', 'Est. Impact of Rapid-Guessing % on RIT', 'Growth', \
                                        'Semester', 'Score', 'HIGHLIGHTS', 'Group by', 'Grade(s)', 'Concepts to', \
                                        'Informational Text: Key Ideas and Details SCORE', \
                                        'Informational Text: Key Ideas and Details STANDARD ERROR', \
                                        'Vocabulary: Acquisition and Use SCORE', \
                                        'Vocabulary: Acquisition and Use STANDARD ERROR', \
                                        'Informational Text: Language, Craft, and Structure SCORE', \
                                        'Informational Text: Language, Craft, and Structure STANDARD ERROR', \
                                        'Literary Text: Language, Craft, and Structure SCORE', \
                                        'Literary Text: Language, Craft, and Structure STANDARD ERROR', \
                                        'Literary Text: Key Ideas and Details SCORE', \
                                        'Literary Text: Key Ideas and Details STANDARD ERROR']

    MapnweaStudentProfileSummaryINFO_Dict = dict.fromkeys(MapnweaStudentProfileSummaryINFO)

    ##################################################################
    ##    Open the data txtfile, which from pdfplumber
    #################################################################

    with open('/home/denghongbo/Student Profile.txt', encoding='utf-8-sig') as f:
        data0 = f.read()
        data = data0.replace("2020/11/30 Student Profile", ' ')
        data = data.replace('\n', ' ')
        data = data.replace('\xa0', ' ')
        data = data.replace('NBSP', ' ')
        ExtractRegPageNUM = "(?<=" + "https://teach.mapnwea.org/nextgen-report/students/profile" + "\s)\d+/\d+"
        PageNUM = re.findall(ExtractRegPageNUM, data)

        j = len(PageNUM)
        while j >= 1:
            replacePageNUM = str(j) + '/' + str(len(PageNUM))
            data = data.replace(replacePageNUM, ' ')
            j = j - 1
        else:
            pass

        data = data.replace("https://teach.mapnwea.org/nextgen-report/students/profile", ' ')

    ##################################################################
    ##    定制对报告的简要信息的提取正则表达式  Extract Brief Info
    #################################################################
    for KeyItem in MapnweaStudentProfileSummaryINFO:
        source = KeyItem

        if source == "ExportDate":
            # 日期格式 月/日/年
            ExtractRegex = "(?<=" + 'on' + "\s)\d+/\d+/\d+"
        elif source == "ExportStaff":
            # use email address as a staff name, so match a email
            ExtractRegex = "(?<=" + 'Exported by' + "\s)[0-9a-zA-Z.]+@[0-9a-zA-Z.]+?com"
        elif source == "FirstName":
            # temp extract as family name, waiting for extracting split
            ExtractRegex = ExtractRegexPrefixForName + "(.*?)" + 'Grade:'
        elif source == "Grade":
            ExtractRegex = "(?<=" + source + "\:\s)\S+"
        elif source == "ID":
            ExtractRegex = "(?<=" + source + "\:\s)\S+"
        elif source == "TestCategory":
            ExtractRegex = "READING"
        elif source == "Score":
            ExtractRegex = "(?<=" + 'READING' + "\s)\d{3}"
        elif source == "Standard Error":
            ExtractRegex = "Standard Error:" + "(.*?)" + "Rapid-Guessing %:"
        elif source == "Rapid-Guessing %":
            # don't know what value could be, except for 'N/A'
            ExtractRegex = "(?<=" + source + "\:\s)\S+"
        elif source == "Semester":
            ExtractRegex = "\S+\s\S+" + "(?=" + "\s" + "Possible range" + ")"
        elif source == "Possible range":
            ExtractRegex = "(?<=" + source + "\:\s)\d{3}\-\d{3}"
        elif source == "Est. Impact of Rapid-Guessing % on RIT":
            ExtractRegex = "(?<=" + source + "\:\s)\S+"
        elif source == "TestDate":
            # 日期格式 月/日/年
            ExtractRegex = "\d+/\d+/\d+\s\-\s\d{3}"
        elif source == "TestDuration":
            ExtractRegex = "\d+/\d+/\d+\s\-\s\d{3}"
        elif source == "Growth":
            ExtractRegex = source + ":\s+" + "(.*?)" + "\s+" + "HIGHLIGHTS"
        elif source == "HIGHLIGHTS":
            ExtractRegex = source + "\s+(.*?)\s+" + "INSTRUCTIONAL"
        elif source == "Group by":
            ExtractRegex = "(?<=" + source + "\s\:\s)\S+"
        elif source == "Grade(s)":
            tempSource = "Grade[(]s[)]"
            ExtractRegex = tempSource + "\s\:\s" + "(.*?)" + "\s" + "Concepts to :"
        elif source == "Concepts to":
            ExtractRegex = source + "\s\:\s" + "(.*?)" + "\s" + "Informational Text"
        elif source == "Informational Text: Key Ideas and Details SCORE":
            TempSource = "Informational Text: Key Ideas and Details"
            ExtractRegex = "(?<=" + TempSource + ")\s\d{3}"
        elif source == "Informational Text: Key Ideas and Details STANDARD ERROR":
            TempSource1 = "Draw Conclusions, Infer, Predict"
            TempSource0 = "Informational Text: Key Ideas and Details" + ExtractRegexPrefixForITKIDSE
            ExtractRegex = TempSource0 + "(.*?)" + TempSource1
        elif source == "Vocabulary: Acquisition and Use SCORE":
            TempSource = "Vocabulary: Acquisition and Use"
            ExtractRegex = "(?<=" + TempSource + ")\s+\d{3}"
        elif source == "Vocabulary: Acquisition and Use STANDARD ERROR":
            TempSource0 = "Vocabulary: Acquisition and Use" + ExtractRegexPrefixForVAUSSE
            TempSource1 = "Context Clues and Multiple-Meaning Words"
            ExtractRegex = TempSource0 + "(.*?)" + TempSource1
        elif source == "Informational Text: Language, Craft, and Structure SCORE":
            TempSource = "Informational Text: Language, Craft, and Structure"
            ExtractRegex = "(?<=" + TempSource + ")\s+\d{3}"
        elif source == "Informational Text: Language, Craft, and Structure STANDARD ERROR":
            TempSource0 = "Informational Text: Language, Craft, and Structure" + ExtractRegexPrefixForITLCSSE
            TempSource1 = "Point of View, Purpose, Perspective, Figurative and Rhetorical Language"
            ExtractRegex = TempSource0 + "(.*?)" + TempSource1
        elif source == "Literary Text: Language, Craft, and Structure SCORE":
            TempSource = "Literary Text: Language, Craft, and Structure"
            ExtractRegex = "(?<=" + TempSource + ")\s+\d{3}"
        elif source == "Literary Text: Language, Craft, and Structure STANDARD ERROR":
            TempSource0 = "Literary Text: Language, Craft, and Structure" + ExtractRegexPrefixForLTLCSSE
            TempSource1 = "Figurative, Connotative Meanings; Tone"
            ExtractRegex = TempSource0 + "(.*?)" + TempSource1
        elif source == "Literary Text: Key Ideas and Details SCORE":
            TempSource = "Literary Text: Key Ideas and Details"
            ExtractRegex = "(?<=" + TempSource + ")\s+\d{3}"
        elif source == "Literary Text: Key Ideas and Details STANDARD ERROR":
            TempSource0 = "Literary Text: Key Ideas and Details" + ExtractRegexPrefixForLTKIDSSE
            TempSource1 = "Draw Conclusions, Infer, Predict"
            ExtractRegex = TempSource0 + "(.*?)" + TempSource1
        else:
            pass

        value = re.findall(ExtractRegex, data)

        if KeyItem == "ExportDate":
            ExtractRegexPrefixForName = value[0]

        if KeyItem == "Informational Text: Key Ideas and Details SCORE":
            ExtractRegexPrefixForITKIDSE = value[0]

        if KeyItem == "Vocabulary: Acquisition and Use SCORE":
            ExtractRegexPrefixForVAUSSE = value[0]

        if KeyItem == "Informational Text: Language, Craft, and Structure SCORE":
            ExtractRegexPrefixForITLCSSE = value[0]

        if KeyItem == "Literary Text: Key Ideas and Details SCORE":
            ExtractRegexPrefixForLTKIDSSE = value[0]

        if KeyItem == "Literary Text: Language, Craft, and Structure SCORE":
            ExtractRegexPrefixForLTLCSSE = value[0]

        MapnweaStudentProfileSummaryINFO_Dict[KeyItem] = value[0]

    MapnweaStudentProfileSummaryINFO_Dict["FirstName"] = str(
        MapnweaStudentProfileSummaryINFO_Dict["FirstName"]).lstrip()
    Name = str(MapnweaStudentProfileSummaryINFO_Dict["FirstName"]).split()
    MapnweaStudentProfileSummaryINFO_Dict["FirstName"] = str(Name[0])
    MapnweaStudentProfileSummaryINFO_Dict["FamilyName"] = str(Name[1])

    ##################################################################################
    ##  change date format MM/DD/YYYY to YYYY-MM-DD
    ##  Sample Code:
    ##  #import datetime
    #   datetime.datetime.strptime("21/12/2008", "%d/%m/%Y").strftime("%Y-%m-%d")
    ##################################################################################
    MapnweaStudentProfileSummaryINFO_Dict["ExportDate"] = datetime.datetime.strptime(
        MapnweaStudentProfileSummaryINFO_Dict["ExportDate"], "%m/%d/%Y").strftime("%Y-%m-%d")

    #################################################################
    ## Change date format END
    #################################################################

    TestDateAndDuration = str(MapnweaStudentProfileSummaryINFO_Dict["TestDate"]).split("-")

    ##################################################################################
    ##  change date format MM/DD/YYYY to YYYY-MM-DD
    ##  Sample Code:
    ##  #import datetime
    #   datetime.datetime.strptime("21/12/2008", "%d/%m/%Y").strftime("%Y-%m-%d")
    ##################################################################################
    MapnweaStudentProfileSummaryINFO_Dict["TestDate"] = datetime.datetime.strptime(str(TestDateAndDuration[0]).rstrip(),
                                                                                   "%m/%d/%Y").strftime("%Y-%m-%d")

    #################################################################
    ## Change date format END
    #################################################################

    MapnweaStudentProfileSummaryINFO_Dict["TestDuration"] = str(TestDateAndDuration[1])

    ####################################################################
    ##  Extract the CheckItemlist
    ####################################################################
    TempCheckListSource = "CCSS.ELA-Literacy."
    CheckListExtractRegex = TempCheckListSource + "(.*?)" + ":"
    CheckListValue = re.findall(CheckListExtractRegex, data)
    CheckListValue2 = []

    REINFORE_DEVELOP_Status_List = []

    for Item in CheckListValue:
        FieldName = "CCSS.ELA-Literacy." + Item
        CheckListValue2.append(FieldName)
        REINFORE_DEVELOP_Status_List.append(Item)

    MapnweaStudentProfile_REINFORE_DEVELOP_Status_Dict = dict.fromkeys(REINFORE_DEVELOP_Status_List)

    ############################################
    ## remove the CheckItem Category from data
    ############################################

    CheckCategory1 = ["Draw Conclusions, Infer, Predict", "Summarize; Analyze Central Ideas, Concepts, and Events", \
                      "Context Clues and Multiple-Meaning Words", "Word Parts, Reference, and Academic Vocabulary", \
                      "Word Relationships and Nuance",
                      "Point of View, Purpose, Perspective, Figurative and Rhetorical Language", \
                      "Text Structures, Text Features", "Figurative, Connotative Meanings; Tone"]

    Score = [MapnweaStudentProfileSummaryINFO_Dict["Informational Text: Key Ideas and Details SCORE"], \
             MapnweaStudentProfileSummaryINFO_Dict["Vocabulary: Acquisition and Use SCORE"], \
             MapnweaStudentProfileSummaryINFO_Dict["Informational Text: Language, Craft, and Structure SCORE"], \
             MapnweaStudentProfileSummaryINFO_Dict["Literary Text: Language, Craft, and Structure SCORE"], \
             MapnweaStudentProfileSummaryINFO_Dict["Literary Text: Key Ideas and Details SCORE"]]

    StandardError = [MapnweaStudentProfileSummaryINFO_Dict["Informational Text: Key Ideas and Details STANDARD ERROR"], \
                     MapnweaStudentProfileSummaryINFO_Dict["Vocabulary: Acquisition and Use STANDARD ERROR"], \
                     MapnweaStudentProfileSummaryINFO_Dict[
                         "Informational Text: Language, Craft, and Structure STANDARD ERROR"], \
                     MapnweaStudentProfileSummaryINFO_Dict[
                         "Literary Text: Language, Craft, and Structure STANDARD ERROR"], \
                     MapnweaStudentProfileSummaryINFO_Dict["Literary Text: Key Ideas and Details STANDARD ERROR"]]

    i = 0
    while i < len(CheckCategory1):
        data = data.replace(CheckCategory1[i], ' ')
        i = i + 1
    else:
        pass

    i = 0
    while i < len(InstructionalAreas):
        RemoveStr = InstructionalAreas[i] + Score[i] + StandardError[i]
        data = data.replace(RemoveStr, ' ')
        i = i + 1
    else:
        pass

    ############################################################################################################
    ##
    ## Extract All CheckItem Section in the Report
    ##
    ############################################################################################################
    CheckItemSectionDict = {}
    CheckItemSectionlist = CheckListValue2
    CheckItemSectionDict = dict.fromkeys(CheckItemSectionlist)
    CheckItemSectionContentValue = []
    Counter = len(CheckItemSectionlist)

    i = 0
    while (i < (Counter - 1)):
        SectionBeginTag = CheckItemSectionlist[i]
        SectionEndTag = CheckItemSectionlist[i + 1]
        CheckItemSectionContentExtractReg = SectionBeginTag + "\:\s(.*?)" + SectionEndTag
        CheckItemSectionContentValue = re.findall(CheckItemSectionContentExtractReg, data)
        CheckItemSectionDict[CheckItemSectionlist[i]] = CheckItemSectionContentValue

        i = i + 1
        if i == (Counter - 1):
            SectionBeginTag = CheckItemSectionlist[i]
            SectionEndTag = "CONFIDENTIALITY NOTICE"
            CheckItemSectionContentExtractReg = SectionBeginTag + "\:\s(.*?)" + SectionEndTag
            CheckItemSectionContentValue = re.findall(CheckItemSectionContentExtractReg, data)
            CheckItemSectionDict[CheckItemSectionlist[i]] = CheckItemSectionContentValue
    else:
        pass

    ###################################################################
    ## Setup  CheckItem REINFORCE AND DEVELOP Recommendation Status
    ###################################################################

    i = 0
    while (i <= (Counter - 1)):
        SectionData = str(CheckItemSectionDict[CheckItemSectionlist[i]])
        if ("REINFORCE" in str(CheckItemSectionDict[CheckItemSectionlist[i]])) and (
            "DEVELOP" in str(CheckItemSectionDict[CheckItemSectionlist[i]])):
            MapnweaStudentProfile_REINFORE_DEVELOP_Status_Dict[REINFORE_DEVELOP_Status_List[i]] = "REINFORCE_DEVELOP"
        elif ("REINFORCE" in str(CheckItemSectionDict[CheckItemSectionlist[i]])) and (
            "DEVELOP" not in str(CheckItemSectionDict[CheckItemSectionlist[i]])):
            MapnweaStudentProfile_REINFORE_DEVELOP_Status_Dict[REINFORE_DEVELOP_Status_List[i]] = "REINFORCE"
        elif ("REINFORCE" not in str(CheckItemSectionDict[CheckItemSectionlist[i]])) and (
            "DEVELOP" in str(CheckItemSectionDict[CheckItemSectionlist[i]])):
            MapnweaStudentProfile_REINFORE_DEVELOP_Status_Dict[REINFORE_DEVELOP_Status_List[i]] = "DEVELOP"
        else:
            MapnweaStudentProfile_REINFORE_DEVELOP_Status_Dict[
                REINFORE_DEVELOP_Status_List[i]] = "No More Recommendation"

        i = i + 1

    ##################################################################################
    ##
    ## Drop the CheckItem ( G5 < Grade)
    ##
    ###################################################################################

    CheckItem_GKtoG5 = []
    CounterCheckItem = len(CheckListValue)

    i = 0

    while (i <= (CounterCheckItem - 1)):
        TempStrList = str(CheckListValue[i]).split(".")
        if (int(TempStrList[1]) < 6):
            CheckItem_GKtoG5.append(CheckListValue[i])

        i = i + 1

    ###################################################################
    ## Extract   CheckItem REINFORCE AND DEVELOP Recommendation List  GK TO G5
    ###################################################################

    MapnweaStudentProfile_REINFORE_DEVELOP_Status_Dict_GKtoG5 = dict.fromkeys(CheckItem_GKtoG5)
    MapProfileExtResultsListReady2MySQLModel = []
    tempDict = {}
    KeyItemNormalization = ''
    tempDictKey = ''
    for GKtoG5CheckItem in CheckItem_GKtoG5:
        KeyItemNormalization = GKtoG5CheckItem
        tempDictKey = KeyItemNormalization.replace('.', '_')
        tempDict[tempDictKey] = MapnweaStudentProfile_REINFORE_DEVELOP_Status_Dict[GKtoG5CheckItem]
        MapProfileExtResultsListReady2MySQLModel.append(tempDict.copy())

        #       MapProfileExtResultsListReady2MySQLModel.append(MapProfileExtResults(item_level=tempDict[tempDictKey], check_item=tempDictKey))
        tempDict = {}

    ##########################################################################################
    ExtractStudentProfileDictMerge = MapnweaStudentProfileSummaryINFO_Dict.copy()

    for key in ExtractStudentProfileDictMerge:
        ExtractStudentProfileDictMerge[key] = ExtractStudentProfileDictMerge[key].strip()

    #################################################################################################

    #################################################################################################
    ## alignment the dict's key for importing  into Django MySQL Models
    #################################################################################################
    DictKeys2List = ExtractStudentProfileDictMerge.keys()

    ExtractDataDictReady2MySQLModel = {}

    for KeyItem in DictKeys2List:
        if KeyItem == 'ExportDate':
            ExtractDataDictReady2MySQLModel['ExportDate'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'ExportStaff':
            ExtractDataDictReady2MySQLModel['ExportStaff'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'FirstName':
            ExtractDataDictReady2MySQLModel['FirstName'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'FamilyName':
            ExtractDataDictReady2MySQLModel['FamilyName'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Grade':
            ExtractDataDictReady2MySQLModel['Grade'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'ID':
            ExtractDataDictReady2MySQLModel['MapID'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'TestCategory':
            ExtractDataDictReady2MySQLModel['TestCategory'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Standard Error':
            ExtractDataDictReady2MySQLModel['Standard_Error'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Possible range':
            ExtractDataDictReady2MySQLModel['Possible_range'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'TestDate':
            ExtractDataDictReady2MySQLModel['TestDate'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'TestDuration':
            ExtractDataDictReady2MySQLModel['TestDuration'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Rapid-Guessing %':
            ExtractDataDictReady2MySQLModel['Rapid_Guessing_Percent'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Est. Impact of Rapid-Guessing % on RIT':
            ExtractDataDictReady2MySQLModel['Est_Impact_of_Rapid_Guessing_Percent_on_RIT'] = \
                ExtractStudentProfileDictMerge[
                    KeyItem]
        elif KeyItem == 'Semester':
            ExtractDataDictReady2MySQLModel['Semester'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Score':
            ExtractDataDictReady2MySQLModel['Score'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'HIGHLIGHTS':
            ExtractDataDictReady2MySQLModel['HIGHLIGHTS'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Group by':
            ExtractDataDictReady2MySQLModel['Group_by'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Grade(s)':
            ExtractDataDictReady2MySQLModel['Grades'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Concepts to':
            ExtractDataDictReady2MySQLModel['Concepts_to'] = ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Informational Text: Key Ideas and Details SCORE':
            ExtractDataDictReady2MySQLModel['Informational_Text_Key_Ideas_and_Details_SCORE'] = \
                ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Informational Text: Key Ideas and Details STANDARD ERROR':
            ExtractDataDictReady2MySQLModel['Informational_Text_Key_Ideas_and_Details_STANDARD_ERROR'] = \
                ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Vocabulary: Acquisition and Use SCORE':
            ExtractDataDictReady2MySQLModel['Vocabulary_Acquisition_and_Use_SCORE'] = ExtractStudentProfileDictMerge[
                KeyItem]
        elif KeyItem == 'Vocabulary: Acquisition and Use STANDARD ERROR':
            ExtractDataDictReady2MySQLModel['Vocabulary_Acquisition_and_Use_STANDARD_ERROR'] = \
                ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Informational Text: Language, Craft, and Structure SCORE':
            ExtractDataDictReady2MySQLModel['Informational_Text_Language_Craft_and_Structure_SCORE'] = \
                ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Informational Text: Language, Craft, and Structure STANDARD ERROR':
            ExtractDataDictReady2MySQLModel['Informational_Text_Language_Craft_and_Structure_STANDARD_ERROR'] = \
                ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Literary Text: Language, Craft, and Structure SCORE':
            ExtractDataDictReady2MySQLModel['Literary_Text_Language_Craft_and_Structure_SCORE'] = \
                ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Literary Text: Language, Craft, and Structure STANDARD ERROR':
            ExtractDataDictReady2MySQLModel['Literary_Text_Language_Craft_and_Structure_STANDARD_ERROR'] = \
                ExtractStudentProfileDictMerge[KeyItem]
        elif KeyItem == 'Literary Text: Key Ideas and Details SCORE':
            ExtractDataDictReady2MySQLModel['Literary_Text_Key_Ideas_and_Details_SCORE'] = \
                ExtractStudentProfileDictMerge[
                    KeyItem]
        elif KeyItem == 'Literary Text: Key Ideas and Details STANDARD ERROR':
            ExtractDataDictReady2MySQLModel['Literary_Text_Key_Ideas_and_Details_STANDARD_ERROR'] = \
                ExtractStudentProfileDictMerge[KeyItem]
        else:
            pass

    ##################################################################
    ##     Extract Data END
    ##################################################################

    ##############################################################################
    ## Save the Extract Info in a txtfile, and the name in parttern xxxx.dict.txt
    ##############################################################################

    ExtractDataDictMergeTempConvert2Str = json.dumps(ExtractDataDictReady2MySQLModel)

    Dictfilenameportion = os.path.splitext(pathfilename)

    Dicttxtfilename = Dictfilenameportion[0] + '.dict.txt'

    Dicttxtfilestored = os.path.join(settings.MEDIA_ROOT, Dicttxtfilename)

    with open(Dicttxtfilestored, "w", encoding='utf-8') as f:
        f.write(ExtractDataDictMergeTempConvert2Str)

    ##############################################################################

    #    ExtractDataDictMergeTempConvert2Str = json.dumps(ExtractDataDictReady2MySQLModel)

    Dictfilenameportion = os.path.splitext(pathfilename)

    Dicttxtfilename = Dictfilenameportion[0] + '.list.txt'

    Dicttxtfilestored = os.path.join(settings.MEDIA_ROOT, Dicttxtfilename)

    with open(Dicttxtfilestored, "w", encoding='utf-8') as f:
        f.write(str(MapProfileExtResultsListReady2MySQLModel))

    ##############################################################################
    ## Save the Extract Info END
    ##############################################################################

    #######################################################################################
    ## write Map Student Profile Data to MySQL
    ##
    #######################################################################################

    # ReportDataStr = json.dumps(ExtractDataDictReady2DjangoModel)

    obj, created = MapStudentProfile.objects.update_or_create(**ExtractDataDictReady2MySQLModel)

    # e.objects.bulk_create(MapProfileExtResultsListReady2MySQLModel)

    # obj = p(ExtractDataDictReady2MySQLModel)
    # obj.save()

    ExtResult_foreignKey = obj

    for GKtoG5CheckItem in CheckItem_GKtoG5:
        MapProfileExtResults.objects.create(map_student_profile=ExtResult_foreignKey,
                                            item_level=MapnweaStudentProfile_REINFORE_DEVELOP_Status_Dict[
                                                GKtoG5CheckItem], check_item=GKtoG5CheckItem)
