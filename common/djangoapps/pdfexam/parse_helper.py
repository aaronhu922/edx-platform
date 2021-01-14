import logging
import re
import datetime
from .models import MapStudentProfile, EarlyliteracySkillSetScores, MapProfileExtResults, MapTestCheckItem

log = logging.getLogger("edx.pdfexam")


def ExtractStarData(data, phonenumber):
    StarEarlyLiteracyPDFReportExtractListBriefInfo = ['FirstName', 'FamilyName', 'ID', 'PrintedDay', 'PrintedDateTime',
                                                      'Reporting Period', 'SchoolYear', 'School', 'Class', 'Grade',
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


def extract_map_data(data, phonenumber):
    # InstructionalAreas = ["Informational Text: Key Ideas and Details", "Vocabulary: Acquisition and Use", \
    #                       "Informational Text: Language, Craft, and Structure", \
    #                       "Literary Text: Language, Craft, and Structure", "Literary Text: Key Ideas and Details"]

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

    mapnwea_student_profile_summary_info_dict = {}

    data = data.replace('\n', ' ')
    data = data.replace('\xa0', ' ')
    data = data.replace('NBSP', ' ')
    data = data.replace(' ', ' ')

    # with open(phonenumber + ".txt", "w+", encoding='utf-8') as f:
    #     f.write(data)
    # f.close()
    ##################################################################
    ##    定制对报告的简要信息的提取正则表达式  Extract Brief Info
    #################################################################
    for source in MapnweaStudentProfileSummaryINFO:

        if source == "ExportDate":
            # 日期格式 月/日/年
            extract_regex = "(?<=" + 'on' + "\s)\d+/\d+/\d+"
        elif source == "ExportStaff":
            # use email address as a staff name, so match a email
            extract_regex = "(?<=Exported by )[0-9a-zA-Z.@]+"
        elif source == "FirstName":
            # temp extract as family name, waiting for extracting split
            extract_regex = '/\d{4}\s(.*?)Grade:'
        elif source == "Grade":
            extract_regex = "(?<=" + source + "\:\s)\S+"
        elif source == "ID":
            extract_regex = "(?<=" + source + "\:\s)\S+"
        elif source == "TestCategory":
            extract_regex = "READING"
        elif source == "Score":
            extract_regex = "(?<=" + 'READING' + "\s)\d{3}"
        elif source == "Standard Error":
            extract_regex = "Standard Error:" + "(.*?)" + "Rapid-Guessing %:"
        elif source == "Rapid-Guessing %":
            # don't know what value could be, except for 'N/A'
            extract_regex = "(?<=" + source + "\:\s)\S+"
        elif source == "Semester":
            extract_regex = "\S+\s\S+" + "(?=" + "\s" + "Possible range" + ")"
        elif source == "Possible range":
            extract_regex = "(?<=" + source + "\:\s)\d{3}\-\d{3}"
        elif source == "Est. Impact of Rapid-Guessing % on RIT":
            extract_regex = "(?<=" + source + "\:\s)\S+"
        elif source == "TestDate":
            # 日期格式 月/日/年
            extract_regex = "\d+/\d+/\d+\s\-\s\d{1,3}"
        elif source == "TestDuration":
            extract_regex = "\d+/\d+/\d+\s\-\s\d{1,3}"
        elif source == "Growth":
            extract_regex = source + ":\s+" + "(.*?)" + "\s+" + "HIGHLIGHTS"
        elif source == "HIGHLIGHTS":
            extract_regex = source + "\s+(.*?)\s+" + "INSTRUCTIONAL"
        elif source == "Group by":
            extract_regex = "(?<=" + source + "\s\:\s)\S+"
        elif source == "Grade(s)":
            tempSource = "Grade[(]s[)]"
            extract_regex = tempSource + "\s\:\s" + "(.*?)" + "\s" + "Concepts to :"
        # elif source == "Concepts to":
        #     ExtractRegex = source + "\s\:\s" + "(.*?)" + "\s" + "Informational Text"
        elif source == "Informational Text: Key Ideas and Details SCORE":
            temp_source = "Informational Text: Key Ideas and Details"
            extract_regex = "(?<=" + temp_source + ")\s\d{1,3}"
        elif source == "Informational Text: Key Ideas and Details STANDARD ERROR":
            temp_source1 = "Draw Conclusions, Infer, Predict"
            temp_source0 = "Informational Text: Key Ideas and Details"
            extract_regex = temp_source0 + "(.*?)" + temp_source1
        elif source == "Vocabulary: Acquisition and Use SCORE":
            temp_source = "Vocabulary: Acquisition and Use"
            extract_regex = "(?<=" + temp_source + ")\s+\d{3}"
        elif source == "Vocabulary: Acquisition and Use STANDARD ERROR":
            temp_source0 = "Vocabulary: Acquisition and Use"
            temp_source1 = "Context Clues and Multiple-Meaning Words"
            extract_regex = temp_source0 + "(.*?)" + temp_source1
        elif source == "Informational Text: Language, Craft, and Structure SCORE":
            temp_source = "Informational Text: Language, Craft, and Structure"
            extract_regex = "(?<=" + temp_source + ")\s+\d{1,3}"
        elif source == "Informational Text: Language, Craft, and Structure STANDARD ERROR":
            temp_source0 = "Informational Text: Language, Craft, and Structure"
            temp_source1 = "Point of View, Purpose, Perspective, Figurative and Rhetorical Language"
            extract_regex = temp_source0 + "(.*?)" + temp_source1
        elif source == "Literary Text: Language, Craft, and Structure SCORE":
            temp_source = "Literary Text: Language, Craft, and Structure"
            extract_regex = "(?<=" + temp_source + ")\s+\d{1,3}"
        elif source == "Literary Text: Language, Craft, and Structure STANDARD ERROR":
            temp_source0 = "Literary Text: Language, Craft, and Structure"
            temp_source1 = "Figurative, Connotative Meanings; Tone"
            extract_regex = temp_source0 + "(.*?)" + temp_source1
        elif source == "Literary Text: Key Ideas and Details SCORE":
            temp_source = "Literary Text: Key Ideas and Details"
            extract_regex = "(?<=" + temp_source + ")\s+\d{1,3}"
        elif source == "Literary Text: Key Ideas and Details STANDARD ERROR":
            temp_source0 = "Literary Text: Key Ideas and Details"
            temp_source1 = "Draw Conclusions, Infer, Predict"
            extract_regex = temp_source0 + "(.*?)" + temp_source1
        else:
            pass
        logging.info("-----regex of {}-----{}---".format(source, extract_regex))

        value = re.findall(extract_regex, data)
        logging.info("-----{}-----{}---".format(source, value))
        if value and len(value) > 0:
            mapnwea_student_profile_summary_info_dict[source] = value[0].strip()

    name = str(mapnwea_student_profile_summary_info_dict["FirstName"]).strip()
    mapnwea_student_profile_summary_info_dict["FirstName"] = name
    mapnwea_student_profile_summary_info_dict["FamilyName"] = name
    logging.info("---name is ----{}---".format(name))

    ##################################################################################
    ##  change date format MM/DD/YYYY to YYYY-MM-DD
    ##  Sample Code:
    ##  #import datetime
    #   datetime.datetime.strptime("21/12/2008", "%d/%m/%Y").strftime("%Y-%m-%d")
    ##################################################################################
    mapnwea_student_profile_summary_info_dict["ExportDate"] = datetime.datetime.strptime(
        mapnwea_student_profile_summary_info_dict["ExportDate"], "%m/%d/%Y").strftime("%Y-%m-%d")

    #################################################################
    ## Change date format END
    #################################################################

    TestDateAndDuration = str(mapnwea_student_profile_summary_info_dict["TestDate"]).split("-")

    ##################################################################################
    ##  change date format MM/DD/YYYY to YYYY-MM-DD
    ##  Sample Code:
    ##  #import datetime
    #   datetime.datetime.strptime("21/12/2008", "%d/%m/%Y").strftime("%Y-%m-%d")
    ##################################################################################
    mapnwea_student_profile_summary_info_dict["TestDate"] = datetime.datetime.strptime(
        str(TestDateAndDuration[0]).rstrip(),
        "%m/%d/%Y").strftime("%Y-%m-%d")

    #################################################################
    ## Change date format END
    #################################################################

    mapnwea_student_profile_summary_info_dict["TestDuration"] = str(TestDateAndDuration[1])

    ####################################################################
    ##  Extract the CheckItemlist
    ####################################################################
    check_list_extract_regex = "CCSS.ELA-Literacy.(.*?):"
    check_list_value = re.findall(check_list_extract_regex, data)

    mapnwea_student_profile_reinfore_develop_status_dict = {}
    logging.info("---check items list:{}".format(check_list_value))
    logging.info("---check items list size:{}".format(len(check_list_value)))

    for item in check_list_value:
        check_item_desc_reg = item + ':(.*?)CCSS.ELA-Literacy'
        desc_text = re.findall(check_item_desc_reg, data)
        for desc in desc_text:
            logging.info("text ---{}".format(desc))
            if ("REINFORCE" in str(desc)) and ("DEVELOP" in str(desc)):
                mapnwea_student_profile_reinfore_develop_status_dict[item] = "REINFORCE_DEVELOP"
            elif ("REINFORCE" in str(desc)) and ("DEVELOP" not in str(desc)):
                mapnwea_student_profile_reinfore_develop_status_dict[item] = "REINFORCE"
            elif ("REINFORCE" not in str(desc)) and (
                    "DEVELOP" in str(desc)):
                mapnwea_student_profile_reinfore_develop_status_dict[item] = "DEVELOP"
            else:
                mapnwea_student_profile_reinfore_develop_status_dict[item] = "No More Recommendation"

    logging.info("---check items dict:{}".format(mapnwea_student_profile_reinfore_develop_status_dict))

    extract_data_dict_ready2_my_sql_model = {}

    for KeyItem in mapnwea_student_profile_summary_info_dict.keys():
        if KeyItem == 'ExportDate':
            extract_data_dict_ready2_my_sql_model['ExportDate'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'ExportStaff':
            extract_data_dict_ready2_my_sql_model['ExportStaff'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'FirstName':
            extract_data_dict_ready2_my_sql_model['FirstName'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'FamilyName':
            extract_data_dict_ready2_my_sql_model['FamilyName'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Grade':
            extract_data_dict_ready2_my_sql_model['Grade'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'ID':
            extract_data_dict_ready2_my_sql_model['MapID'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'TestCategory':
            extract_data_dict_ready2_my_sql_model['TestCategory'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Standard Error':
            extract_data_dict_ready2_my_sql_model['Standard_Error'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Possible range':
            extract_data_dict_ready2_my_sql_model['Possible_range'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'TestDate':
            extract_data_dict_ready2_my_sql_model['TestDate'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'TestDuration':
            extract_data_dict_ready2_my_sql_model['TestDuration'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Growth':
            extract_data_dict_ready2_my_sql_model['Growth'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Rapid-Guessing %':
            extract_data_dict_ready2_my_sql_model['Rapid_Guessing_Percent'] = mapnwea_student_profile_summary_info_dict[
                KeyItem]
        elif KeyItem == 'Est. Impact of Rapid-Guessing % on RIT':
            extract_data_dict_ready2_my_sql_model['Est_Impact_of_Rapid_Guessing_Percent_on_RIT'] = \
                mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Semester':
            extract_data_dict_ready2_my_sql_model['Semester'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Score':
            extract_data_dict_ready2_my_sql_model['Score'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'HIGHLIGHTS':
            extract_data_dict_ready2_my_sql_model['HIGHLIGHTS'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Group by':
            extract_data_dict_ready2_my_sql_model['Group_by'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Grade(s)':
            extract_data_dict_ready2_my_sql_model['Grades'] = mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Concepts to':
            extract_data_dict_ready2_my_sql_model['Concepts_to'] = 'Reinforce, Develop'
        elif KeyItem == 'Informational Text: Key Ideas and Details SCORE':
            extract_data_dict_ready2_my_sql_model['Informational_Text_Key_Ideas_and_Details_SCORE'] = \
                mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Informational Text: Key Ideas and Details STANDARD ERROR':
            extract_data_dict_ready2_my_sql_model['Informational_Text_Key_Ideas_and_Details_STANDARD_ERROR'] = \
                mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Vocabulary: Acquisition and Use SCORE':
            extract_data_dict_ready2_my_sql_model['Vocabulary_Acquisition_and_Use_SCORE'] = \
                mapnwea_student_profile_summary_info_dict[
                    KeyItem]
        elif KeyItem == 'Vocabulary: Acquisition and Use STANDARD ERROR':
            extract_data_dict_ready2_my_sql_model['Vocabulary_Acquisition_and_Use_STANDARD_ERROR'] = \
                mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Informational Text: Language, Craft, and Structure SCORE':
            extract_data_dict_ready2_my_sql_model['Informational_Text_Language_Craft_and_Structure_SCORE'] = \
                mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Informational Text: Language, Craft, and Structure STANDARD ERROR':
            extract_data_dict_ready2_my_sql_model['Informational_Text_Language_Craft_and_Structure_STANDARD_ERROR'] = \
                mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Literary Text: Language, Craft, and Structure SCORE':
            extract_data_dict_ready2_my_sql_model['Literary_Text_Language_Craft_and_Structure_SCORE'] = \
                mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Literary Text: Language, Craft, and Structure STANDARD ERROR':
            extract_data_dict_ready2_my_sql_model['Literary_Text_Language_Craft_and_Structure_STANDARD_ERROR'] = \
                mapnwea_student_profile_summary_info_dict[KeyItem]
        elif KeyItem == 'Literary Text: Key Ideas and Details SCORE':
            extract_data_dict_ready2_my_sql_model['Literary_Text_Key_Ideas_and_Details_SCORE'] = \
                mapnwea_student_profile_summary_info_dict[
                    KeyItem]
        elif KeyItem == 'Literary Text: Key Ideas and Details STANDARD ERROR':
            extract_data_dict_ready2_my_sql_model['Literary_Text_Key_Ideas_and_Details_STANDARD_ERROR'] = \
                mapnwea_student_profile_summary_info_dict[KeyItem]
        else:
            pass

    extract_data_dict_ready2_my_sql_model['phone_number'] = phonenumber

    stu_map_pro, created = MapStudentProfile.objects.update_or_create(phone_number=phonenumber,
                                                                      TestDate=extract_data_dict_ready2_my_sql_model[
                                                                          'TestDate'],
                                                                      defaults=extract_data_dict_ready2_my_sql_model)

    if not created:
        log.warning(
            "It is going to update a student {} map result, need to clear pre checked items.".format(phonenumber))
        MapProfileExtResults.objects.filter(map_student_profile=stu_map_pro).delete()

    log.info(mapnwea_student_profile_reinfore_develop_status_dict)
    log.info(len(mapnwea_student_profile_reinfore_develop_status_dict))

    for GKtoG5CheckItem in mapnwea_student_profile_reinfore_develop_status_dict.keys():
        check_item = MapTestCheckItem.objects.filter(item_name=GKtoG5CheckItem.upper()).first()
        if check_item:
            MapProfileExtResults.objects.update_or_create(map_student_profile=stu_map_pro, check_item=check_item,
                                                          defaults={
                                                              "item_level":
                                                                  mapnwea_student_profile_reinfore_develop_status_dict[
                                                                      GKtoG5CheckItem]
                                                          }
                                                          )
    return stu_map_pro
