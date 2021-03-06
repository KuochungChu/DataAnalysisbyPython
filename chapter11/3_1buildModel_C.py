
# coding: utf-8

# In[1]:

##  模型构建——C盘为例
# 核心部分：构建基于ARIMA或者ARMA的模型，采用AIC/BIC/HQ信息准则对模型进行定阶，确定p,q参数，从而选择最优模型
# 根据自相关和偏相关图判定平稳性，确定了所用模型是采用ARMA或者ARIMA，而不是AR或者MA；
# 注意：不管是ARMA还是ARIMA模型，都是对平稳数据建模。前者是直接针对平稳数据建模，无需进行差分变换；后者则需要先对数据进行差分，差分平稳后再建模。
# 此处讨论了四种组合：ARIMA+AIC、ARIMA+BIC、ARMA+AIC、ARMA+BIC 。注意：基于HQ信息准则进行的模型在3_2buildModel_C_HQ_ARIMA.py中介绍，发现此案例中不适合使用HQ
# 步骤：平稳性检验--> 白噪声检验--> 模型识别--> 模型检验
import pandas as pd
inputfile = 'attrsConstruction.xlsx'

data = pd.read_excel(inputfile)
df = data.iloc[:len(data)-5] #不使用后五个值


# In[2]:

# 第 * 1 * 步--C盘---------平稳性检测
#1)平稳性检测 ：判断是否平稳，若不平稳，对其进行差分处理直至平稳
# 方法：此处采用单位根检验（ADF）的方法或者时序图的方法（见数据探索模块）
# 注意：其他平稳性检验方法见steadyCheck.py文件
from statsmodels.tsa.stattools import adfuller as ADF
diff = 0
# 判断D盘数据的平稳性，以及确定几次差分后平稳
adf = ADF(df['CWXT_DB:184:C:\\'])
print adf 

while adf[1] >= 0.05 : # adf[1]是p值，p值小于0.05认为是平稳的
    print adf[1]
    diff = diff + 1
    adf = ADF(df['CWXT_DB:184:C:\\'].diff(diff).dropna())#注意，差分后使用ADF检验时，必须去掉空值
    
print (u'原始序列经过%s阶差分后归于平稳，p值为%s') % (diff, adf[1])
df['CWXT_DB:184:C:\\_adf'] = df['CWXT_DB:184:C:\\'].diff(1)


# In[4]:

# 第 * 2 * 步--C盘---------白噪声检验
# 目的：验证序列中有用信息是否已经被提取完毕，需要进行白噪声检验。若序列是白噪声序列，说明序列中有用信息已经被提取完，只剩随机扰动
# 方法：采用LB统计量的方法进行白噪声检验
# 若没有通过白噪声检验，则需要进行模型识别，识别其模型属于AR、MA还是ARMA。

inputfile2 = 'attrsConstruction.xlsx'
data1 = pd.read_excel(inputfile2)
data1 = data1.iloc[:len(data1)-5]# 不使用最后五个数据（作为预测参考）

# 白噪声检测
from statsmodels.stats.diagnostic import acorr_ljungbox

[[lb], [p]] = acorr_ljungbox(data1['CWXT_DB:184:C:\\'], lags = 1) ## lags是残差延迟个数
if p < 0.05:
    print (u'原始序列为非白噪声序列，对应的p值为：%s' % p)
else:
    print (u'原始序列为白噪声序列，对应的p值为：%s' % p)

[[lb], [p]] = acorr_ljungbox(data1['CWXT_DB:184:C:\\'].diff(1).dropna(), lags = 1)
if p < 0.05:
    print (u'一阶差分序列为非白噪声序列，对应的p值为：%s' % p)
else:
    print (u'一阶差分序列为白噪声序列，对应的p值为：%s' % p)


# In[5]:

# 第 * 3 * 步----------模型识别
# 方法：采用极大似然比方法进行模型的参数估计，估计各个参数的值。
# 然后针对各个不同模型，方法一：采用BIC信息准则对模型进行定阶，确定p,q参数，从而选择最优模型。
# 注意，进行此步时，index需要为时间序列类型
# 确定最佳p、d、q的值
inputfile3 = 'attrsConstruction.xlsx'
data2 = pd.read_excel(inputfile3,index_col='COLLECTTIME')
xtest_value=data2['CWXT_DB:184:C:\\'][-5:]
data2 = data2.iloc[:len(data2)-5]# 不使用最后五个数据（作为预测参考） 
xdata2 = data2['CWXT_DB:184:C:\\']

# ARIMA（p,d,q）/ARIMA（p,q）中,AR是自回归,p为自回归项数；MA为滑动平均,q为滑动平均项数,
#　注意：ARIMA中的d为使之成为平稳序列所做的差分次数(阶数)，由前一步骤知d=1
# from statsmodels.tsa.arima_model import ARMA #建立ARMA（p,q）模型 
from statsmodels.tsa.arima_model import ARIMA#建立ARIMA（p,1，q）模型

# 定阶
# 目前选择模型常用如下准则!!!!!
# 增加自由参数的数目提高了拟合的优良性，
# AIC/BIC/HQ鼓励数据拟合的优良性但是尽量避免出现过度拟合(Overfitting)的情况。所以优先考虑的模型应是AIC/BIC/HQ值最小的那一个
# * AIC=-2 ln(L) + 2 k 中文名字：赤池信息量 akaike information criterion (AIC)
# * BIC=-2 ln(L) + ln(n)*k 中文名字：贝叶斯信息量 bayesian information criterion (BIC)
# * HQ=-2 ln(L) + ln(ln(n))*k hannan-quinn criterion (HQ)

# 　以AIC方式定信息准则　＋　ARIMA为例------------！！！模型检验中也要对应修改！！！------------

pmax = int(len(xdata2)/10) # 一般阶数不超过length/10
qmax = int(len(xdata2)/10) # 一般阶数不超过length/10

aic_matrix = [] # 矩阵
for p in range(pmax+1):
    tmp = []
    for q in range(qmax+1):
        try:
            print ARIMA(xdata2, (p,1,q)).fit().aic
            tmp.append(ARIMA(xdata2, (p,1,q)).fit().aic) #存在部分为空值，会报错
#             tmp.append(ARIMA(xdata2, (p,1,q)).fit().bic) #  BIC方式
#             tmp.append(ARIMA(xdata2, (p,1,q)).fit().hq) #  AIC方式
        except:
            tmp.append(None)
            
    aic_matrix.append(tmp)
    
aic_matrix = pd.DataFrame(aic_matrix) # 从中可以找出最小值
print aic_matrix
print aic_matrix.stack()


# In[6]:

# 第 * 4 * 步--C盘---------模型检验
# 确定模型后，需要检验其残差序列是否是白噪声，若不是，说明，残差中还存在有用的信息，需要修改模型或者进一步提取。
# 若其残差不是白噪声，重新更换p,q的值，重新确定
import pandas as pd
import numpy as np

while 1:
    p, q = aic_matrix.stack().idxmin() # 先展平该表格，然后找出最小值的索引位置
    print (u'当前AIC最小的p值与q值分别为：%s、%s' % (p,q))
    
    lagnum = 12 # 残差延迟个数

    # 由模型识别可知第一次BIC最小的p值与q值分别为：0、1

    arima = ARIMA(xdata2, (p,1,q)).fit() # 建立并训练模型
    xdata_pred = arima.predict(typ = 'levels') # 预测
    pred_error = (xdata_pred - xdata2).dropna() # 计算残差

    # 白噪声检测
    from statsmodels.stats.diagnostic import acorr_ljungbox

    lbx, px = acorr_ljungbox(pred_error, lags = lagnum)
    h = (px < 0.05).sum() # p值小于0.05，认为是非噪声
    if h > 0:
        print (u'模型ARIMA(%s,1,%s)不符合白噪声检验' % (p,q))
        print ('在AIC矩阵中去掉[%s,%s]组合，重新进行计算' % (p,q))
        aic_matrix.iloc[p,q] =  np.nan
        arimafail = arima
        continue
    else:
        print (p,q)
        print (u'模型ARIMA(%s,1,%s)符合白噪声检验' % (p,q))
        break
        
        


# In[7]:

arima.summary() # 注意当p,q值为0，0时，summary方法报错


# In[8]:

forecast_values, forecasts_standard_error, forecast_confidence_interval = arima.forecast(5)
forecast_values
# arimaf = ARIMA(xdata2, (0,1,1)).fit()
# arimaf.forecast(5)[0]


# In[9]:

predictdata = pd.DataFrame(xtest_value)
predictdata.insert(1,'CWXT_DB:184:C:\\_predict',forecast_values)
predictdata.rename(columns={'CWXT_DB:184:C:\\':u'实际值','CWXT_DB:184:C:\_predict':u'预测值'},inplace=True)
predictdata.info()


# In[10]:

result_d = predictdata.applymap(lambda x: '%.2f' % x) # 将表格中各个浮点值都格式化
result_d.to_excel('pedictdata_C.xlsx')
result_d


# In[11]:

# 第 * 5 * 步--D盘---------模型评价
# 为了评价时序预测模型效果的好坏，本章采用3个衡量模型预测精度的统计量指标：平均绝对误差、均方根误差、平均绝对百分误差
# -*- coding:utf-8 -*-
import pandas as pd

inputfile4 = 'pedictdata_C.xlsx'
result = pd.read_excel(inputfile4,index_col='COLLECTTIME')
result = result.applymap(lambda x: x/10**6)
print result

# 计算误差
abs_ = (result[u'预测值']-result[u'实际值']).abs()
mae_ = abs_.mean() # mae平均绝对误差
rmas_ = ((abs_**2).mean())**0.5 #rmas均方根误差
mape_ = (abs_/result[u'实际值']).mean() #mape平均绝对百分误差
print mae_
print rmas_
print mape_
errors = 1.5
print '误差阈值为%s' % errors
if (mae_ < errors) & (rmas_ < errors) & (mape_ < errors):
    print (u'AIC模型下平均绝对误差为：%.4f, \n均方根误差为：%.4f, \n平均绝对百分误差为：%.4f' % (mae_, rmas_, mape_))
    print '误差检验通过！'
else:
    print '误差检验不通过！'


# In[12]:

# 注意：
# 说明：由于用HQ训练模型时，都是空值，所以，本例使用HQ不合适
#-----ARIMA--BIC---
#                    实际值        预测值
# COLLECTTIME                      
# 2014-11-12   35.704313  35.722538
# 2014-11-13   35.704981  35.757104
# 2014-11-14   34.570385  35.791669
# 2014-11-15   34.673821  35.826235
# 2014-11-16   34.793245  35.860800
# 0.70232013
# 0.890203752645
# 0.0202432790493
# 误差阈值为1.5
# BIC模型下平均绝对误差为：0.7023, 
# 均方根误差为：0.8902, 
# 平均绝对百分误差为：0.0202
# 误差检验通过！
#-----ARIMA--AIC---
#                    实际值        预测值
# COLLECTTIME                      
# 2014-11-12   35.704313  35.779972
# 2014-11-13   35.704981  35.836938
# 2014-11-14   34.570385  35.889601
# 2014-11-15   34.673821  35.935428
# 2014-11-16   34.793245  35.981256
# 0.795290026
# 0.976369605661
# 0.0229009946085
# AIC模型下平均绝对误差为：0.7953, 
# 均方根误差为：0.9764, 
# 平均绝对百分误差为：0.0229
# 误差检验通过！
# 通过对比AIC与BIC的结果，可以发现BIC的几个误差均较小
#-----ARMA--BIC---
#                    实际值        预测值
# COLLECTTIME                      
# 2014-11-12   35.704313  35.581706
# 2014-11-13   35.704981  35.488223
# 2014-11-14   34.570385  35.405986
# 2014-11-15   34.673821  35.333641
# 2014-11-16   34.793245  35.270000
# 0.462308002
# 0.533460826783
# 0.0132815193493
# 误差阈值为1.5
# 平均绝对误差为：0.4623, 
# 均方根误差为：0.5335, 
# 平均绝对百分误差为：0.0133
# 误差检验通过！

# 综上：ARMA+BIC更优


# In[ ]:



