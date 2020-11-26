from django.db import models

# Create your models here.

class EarlyliteracySkillSetScores(models.Model):

    SkillSetScoresReportID = models.AutoField(primary_key=True)
    IsDelete = models.BooleanField(default=False)
    FirstName = models.CharField(max_length=10)
    FamilyName = models.CharField(max_length=10)
    FlyHighPlatformStudentID = models.CharField(max_length=32, null=True)
    STARPlatformStudentID = models.CharField(max_length=32)
    PrintDay = models.CharField(max_length=10)
    PrintDateTime = models.CharField(max_length=60)
    ReportPeriodStart = models.DateField()
    ReportPeriodEnd = models.DateField()
    SchoolYear = models.CharField(max_length=22)
    SchoolName = models.CharField(max_length=20)
    Class = models.CharField(max_length=5)
    Grade = models.CharField(max_length=2)
    TeacherName = models.CharField(max_length=20)
    TestDate = models.DateField()
    ScaledScore = models.IntegerField()
    LexileMeasure = models.CharField(max_length=15)
    LexileRange = models.CharField(max_length=15)
    EstORF = models.CharField(max_length=5)
    AlphabeticPrinciple = models.CharField(max_length=3)
    ConceptOfWord = models.IntegerField()
    VisualDiscrimination = models.IntegerField()
    PhonemicAwareness = models.IntegerField()
    Phonics = models.IntegerField()
    StructuralAnalysis = models.IntegerField()
    Vocabulary = models.IntegerField()
    SentenceLevelComprehension = models.IntegerField()
    ParagraphLevelComprehension = models.IntegerField()
    EarlyNumeracy = models.IntegerField()
    AlphabeticKnowledge = models.IntegerField()
    NextStepForAlphabeticKnowledge = models.BooleanField(default=False)
    AlphabeticSequence = models.IntegerField()
    NextStepForAlphabeticSequence = models.BooleanField(default=False)
    LetterSounds = models.IntegerField()
    NextStepForLetterSounds = models.BooleanField(default=False)
    PrintConceptsWordLength = models.IntegerField()
    NextStepForPrintConceptsWordLength = models.BooleanField(default=False)
    PrintConceptsWordBorders = models.IntegerField()
    NextStepForPrintConceptsWordBorders = models.BooleanField(default=False)
    PrintConceptsLettersAndWords = models.IntegerField()
    NextStepForPrintConceptsLettersAndWords = models.BooleanField(default=False)
    Letters = models.IntegerField()
    NextStepForLetters = models.BooleanField(default=False)
    IdentificationAndWordMatching = models.IntegerField()
    NextStepForIdentificationAndWordMatching = models.BooleanField(default=False)
    RhymingAndWordFamilies = models.IntegerField()
    NextStepForRhymingAndWordFamilies = models.BooleanField(default=False)
    BlendingWordParts = models.IntegerField()
    NextStepForBlendingWordParts = models.BooleanField(default=False)
    BlendingPhonemes = models.IntegerField()
    NextStepForBlendingPhonemes = models.BooleanField(default=False)
    InitialAndFinalPhonemes = models.IntegerField()
    NextStepForInitialAndFinalPhonemes = models.BooleanField(default=False)
    ConsonantBlendsPA = models.IntegerField()
    NextStepForConsonantBlendsPA = models.BooleanField(default=False)
    MedialPhonemeDiscrimination = models.IntegerField()
    NextStepForMedialPhonemeDiscrimination = models.BooleanField(default=False)
    PhonemeIsolationORManipulation = models.IntegerField()
    NextStepForPhonemeIsolationORManipulation = models.BooleanField(default=False)
    PhonemeSegmentation = models.IntegerField()
    NextStepForPhonemeSegmentation = models.BooleanField(default=False)
    ShortVowelSounds = models.IntegerField()
    NextStepForShortVowelSounds = models.BooleanField(default=False)
    InitialConsonantSounds = models.IntegerField()
    NextStepForInitialConsonantSounds = models.BooleanField(default=False)
    FinalConsonantSounds = models.IntegerField()
    NextStepForFinalConsonantSounds = models.BooleanField(default=False)
    LongVowelSounds = models.IntegerField()
    NextStepForLongVowelSounds = models.BooleanField(default=False)
    VariantVowelSounds = models.IntegerField()
    NextStepForVariantVowelSounds = models.BooleanField(default=False)
    ConsonantBlendsPH = models.IntegerField()
    NextStepForConsonantBlendsPH = models.BooleanField(default=False)
    ConsonantDigraphs = models.IntegerField()
    NextStepForConsonantDigraphs = models.BooleanField(default=False)
    OtherVowelSounds = models.IntegerField()
    NextStepForOtherVowelSounds = models.BooleanField(default=False)
    SoundSymbolCorrespondenceConsonants = models.IntegerField()
    NextStepForSoundSymbolCorrespondenceConsonants = models.BooleanField(default=False)
    WordBuilding = models.IntegerField()
    NextStepForWordBuilding = models.BooleanField(default=False)
    SoundSymbolCorrespondenceVowels = models.IntegerField()
    NextStepForSoundSymbolCorrespondenceVowels = models.BooleanField(default=False)
    WordFamiliesOrRhyming = models.IntegerField()
    NextStepForWordFamiliesOrRhyming = models.BooleanField(default=False)
    WordsWithAffixes = models.IntegerField()
    NextStepForWordsWithAffixes = models.BooleanField(default=False)
    Syllabification = models.IntegerField()
    NextStepForSyllabification = models.BooleanField(default=False)
    CompoundWords = models.IntegerField()
    NextStepForCompoundWords = models.BooleanField(default=False)
    WordFacility = models.IntegerField()
    NextStepForWordFacility = models.BooleanField(default=False)
    Synonyms = models.IntegerField()
    NextStepForSynonyms = models.BooleanField(default=False)
    Antonyms = models.IntegerField()
    NextStepForAntonyms = models.BooleanField(default=False)
    ComprehensionATtheSentenceLevel = models.IntegerField()
    NextStepForComprehensionATtheSentenceLevel = models.BooleanField(default=False)
    ComprehensionOfParagraphs = models.IntegerField()
    NextStepForComprehensionOfParagraphs = models.BooleanField(default=False)
    NumberNamingAndNumberIdentification = models.IntegerField()
    NextStepForNumberNamingAndNumberIdentification = models.BooleanField(default=False)
    NumberObjectCorrespondence = models.IntegerField()
    NextStepForNumberObjectCorrespondence = models.BooleanField(default=False)
    SequenceCompletion = models.IntegerField()
    NextStepForSequenceCompletion = models.BooleanField(default=False)
    ComposingAndDecomposing = models.IntegerField()
    NextStepForComposingAndDecomposing = models.BooleanField(default=False)
    Measurement = models.IntegerField()
    NextStepForMeasurement = models.BooleanField(default=False)

