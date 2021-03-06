#Reads data from WordsBank proportion table and transpose the matrix
#Loads the transcript dictionaries that we created using YouTube_ReadVideos
#Vectorize the videos series, 
#Calculate Cosine Similarity between words and Video trasncript matrices (same dimentions)
#Scale data so that they go from 0 to 1
#Bin the similarity score into 3 bins (2 easy, 1 moderate, 0 difficult)
#Transform into long format for sampling one  video at a time
#Get age and difficulty level and sample one video from the list of possible videos


import re
import pickle
import pandas as pd
import numpy as numpy
import numpy as np
from sklearn import preprocessing
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import KBinsDiscretizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import cosine
import nltk
from scipy import stats





#Reads data from WordsBank proportion table
data = pd.read_csv("item_data.csv") 
data2=pd.DataFrame(data)
columns = ['num_item_id','type', 'category']
df1= data2.drop(columns, axis=1)

def videolength(s3):
    lengthvideo2=[]
    for s in range(len(s3)):
        words=getwordcounts(s3[s])
        lengthvideo = 0    
        for i in words:
            lengthvideo += words[i]
# lengthvideo=len(words)
        lengthvideo2.append(lengthvideo)
    return lengthvideo2


#Loads the transcript dictionaries that we created using YouTube_ReadVideos
prediction=[]
VideoKnowledgePercentage=[]

CategoryDictionary= {'Educational': ('Blippi', 'SciShow Kids'), 'Cartoon': ('POCOYO in ENGLISH', 'peppa pig' ), 'Entertainment': ('ryan toysreview', 'Kids TV - Nursery Rhymes And Baby Songs')} 
inputscore='difficult' #Hardcoded here
age=16 #Hardcoded here

def My_Recommendation_Model(CategoryDictionary, age, inputscore, df1):
    #Transpose so that words are columns names, used later for Cosyne Similarity
    datasettransposed= df1.set_index('definition').T
    CategoryDictionary={}
    for key, value in CategoryDictionary.items():
        CategoryUnified= {}
        myvalue= [str(i) for i in CategoryDictionary[key]] 
        for i in range(len(myvalue)):
            test = pickle.load(open(myvalue[i]+"_released.pickle", "rb")) 
            CategoryUnified.update(test)       
        #make a series out of videos data
        s2 = pd.Series(CategoryUnified, name='Mytext')
        s2.index.name = 'Video_id'
        s2.reset_index()

        #Vectorize the videos series, this makes a matrix of words with the relative frequency in each video
        #Since we used the vocabulary attribute it is only checking for words that are within the vocabulary
        vectorizer = CountVectorizer(vocabulary=df1.definition)
        X = vectorizer.fit_transform(s2)
        CosineSimilarityVideoMatrix=cosine_similarity(datasettransposed, X.toarray())
        CosineSimMatrixDataFrame= pd.DataFrame(CosineSimilarityVideoMatrix) #rows= "age", columns= 'videos'
        
        #Calculating proportion of video's words in the dictionary over total number of words in the videos 
        videolen= videolength(s2)
        AgeByVideosDotProduct = np.matmul(datasettransposed.values, X.toarray().transpose())
        DOTPRODUCTOVERLENGTH= (AgeByVideosDotProduct/videolen)*100


        #Scaling data so that they go from 0 to 1
        min_max_scaler = preprocessing.MinMaxScaler()
        y_scaled = min_max_scaler.fit_transform(CosineSimMatrixDataFrame.T)
        ScaledDataFrame = pd.DataFrame(y_scaled.T)

        #Binning the similarity score into 3 bins for easy interpretation
        est = KBinsDiscretizer(n_bins=3, encode='ordinal', strategy='uniform')
        Xbinned = est.fit_transform(ScaledDataFrame) 
        BinnedDataFrame = pd.DataFrame(Xbinned)
        
        #Give names to index and columns of the binned data matrix
        columnsnames =numpy.linspace(0, (len(ScaledDataFrame.iloc[1,:])-1), num=len(ScaledDataFrame.iloc[1,:]), endpoint=True, retstep=False, dtype=int)
        agename=numpy.linspace(16, 30, num=15, endpoint=True, retstep=False, dtype=int)
        BinnedDataFrame = pd.DataFrame(Xbinned, index=agename,columns=columnsnames  )


        #Transforming the data matrix from wide format into long format
        BinnedDataFrame_df = BinnedDataFrame.reset_index()
        BinnedDataFrame_long = pd.melt(BinnedDataFrame_df, id_vars='index', value_vars = list(BinnedDataFrame_df.columns[1:]))
        BinnedDataFrame_long.columns = ['age', 'vid_index', 'score']

        #Reshaping proportion of video's words in the dictionary over total number of words in the videos 
        DOTPRODUCTOVERLENGTHDataFrame= pd.DataFrame(DOTPRODUCTOVERLENGTH, index=['16', '17', '18', '19', '20','21','22', '23','24', '25', '26', '27', '28', '29', '30'])
        DOTPRODUCTOVERLENGTHDataFrameIndex=DOTPRODUCTOVERLENGTHDataFrame.reset_index()
        DOTPRODUCTOVERLENGTH_long = pd.melt(DOTPRODUCTOVERLENGTHDataFrameIndex, id_vars='index', value_vars = list(DOTPRODUCTOVERLENGTHDataFrameIndex.columns[1:]))
        DOTPRODUCTOVERLENGTH_long
        DOTPRODUCTOVERLENGTH_long.columns = ['age', 'vid_index', 'Actualscore'] 

        BinnedDataFrameWITHSCORE= pd.concat([BinnedDataFrame_long, DOTPRODUCTOVERLENGTH_long['Actualscore']], axis=1)


    #For the app:
    #Now I need to add a feature that based on the App input age level (index) and bin (value)
    #chooses randomly a video location (column) and ultimately a video_id

        
        if inputscore=="easy": scoretoUse=2.0
        elif inputscore=="moderate": scoretoUse=1.0
        elif  inputscore=="difficult": scoretoUse=0.0

    #Gets the rows that contain the desired value for score
        # ScoreDF= BinnedDataFrame_long.loc[BinnedDataFrame_long['score']==scoretoUse]
        ScoreDF=BinnedDataFrameWITHSCORE.loc[BinnedDataFrameWITHSCORE['score']==scoretoUse]
        

    ##Gets the rows that contain the desired value for age
        #We need to add int() before the age input because the html input is read as text
        AgeScoreDF= ScoreDF.loc[ScoreDF['age']==int(age)]
    #Sample randomly one video from the set
        Sample= AgeScoreDF.sample(1)

    #Gets the video position value from Sample without the row indexing
        IndexVideo = list(Sample['vid_index'])[0]
    #Gets the one video from the video_id series
        Video_id=list(s2.index)[IndexVideo]

        ActualScoreFor= list(Sample['Actualscore'])[0]
        ActualScoreForVideo= round(ActualScoreFor, 2)

        prediction.append(Video_id)
        VideoKnowledgePercentage.append(ActualScoreForVideo)

    return prediction, VideoKnowledgePercentage


prediction, VideoKnowledgePercentage= My_Recommendation_Model(CategoryDictionary, age, inputscore, df1)

