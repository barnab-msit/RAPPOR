import pandas as pd
from rappor import ProcessDataAndParameters, mapBloomFilter, GetBloomBits
import numpy as np
from sklearn.linear_model import Lasso, LinearRegression



field = 'word'
candidates = pd.read_csv('corpus1000.csv')

print('------')
client = candidates.sample(frac=0.8)

client.to_csv('client.csv')
nbits = 32
icohort = 2
nhashes = 4
f = 0.1
allunique = []
[matrix,cohorts] = ProcessDataAndParameters(client, icohort, f, nbits, nhashes, allunique)
#print(allunique)
matrix = np.array(matrix)
#print(cohorts[9499])
nreports = matrix.shape[0]
print('reports number:', nreports)
Y = np.zeros((nbits,icohort))
C = np.zeros((nbits,icohort))
nreportspercohort=np.zeros(icohort)

for i in range(0,nreports):
    nreportspercohort[cohorts[i]-1]=nreportspercohort[cohorts[i]-1]+1

print(nreportspercohort)

for cohort in range(1,icohort+1):
   matrix1=[]
   for i in range(0,nreports):
       if(cohort==cohorts[i]):
           matrix1.append(matrix[i,:])
   matrix1=np.array(matrix1)
   print(matrix1.shape)

   for bits in range(0,nbits):
       cval = np.sum(matrix1[:,bits])
       C[bits][cohort-1] = cval
       
print(C)
#print(C[0][0])
#print(nreportspercohort[0])
for k in range(0,nbits):
   for cohort in range(1,icohort+1):

     val = (C[k][cohort-1] - 0.5 * nreportspercohort[cohort-1] * f) / (1 - f)

     if val < 0:
        val = 0
     Y[k][cohort-1] = val

print(Y)

X = np.zeros((nbits*icohort,candidates.shape[0]), int)
i=1

for cand in candidates[field]:
    col=[]
    for cohort in range(1,icohort+1):
        vec_cand = mapBloomFilter(cand, cohort, nhashes, nbits)
        col.extend(vec_cand)
    num = int(np.sum(col))
    if num != icohort * nhashes:
        print(cand)
        print('wrong')
    X[:,i-1] = col
    i=i+1
print(np.sum(X, axis=0))
u, ind = np.unique(X, return_index=True, axis=1)
print(X.shape)
print(len(ind))
Y = Y.reshape(nbits*icohort,1)
sparse_lasso = Lasso(alpha=1, fit_intercept=False,max_iter=5000)
sparse_lasso.fit(X, Y)
#print('---candidates---')
#print(candidates)
print('---client---')
print('---')
words=candidates[field]
coefs = sparse_lasso.coef_
for i in range(0,coefs.shape[0]):
    if(coefs[i]>0):
      print(words.iloc[i])
      print(coefs[i])

print('strings selected by lasso: ')
pos_client_selec = candidates[field][coefs>0]
#check here
neg_client_selec=  candidates[field][coefs<0]
client_selec = pd.concat([pos_client_selec, neg_client_selec])
print(client_selec.shape)

cnt = .0
i = 1
for val in client_selec:

   inflag = val in set(client[field])
   cnt += inflag
 #  print(i)
   if inflag:
       true_freq = client[client[field] == val]['trueFrequency'].values[0]
    #   print(val, ': ***true positive***', true_freq)
   else:
     #  print(val, ': false positive')
       u=1
   i += 1
print('precison', cnt/len(client_selec))
print(cnt, len(client))
acc = cnt/len(client)
print('recall', acc)
# print(X.shape)
#check here
X_lasso = X[:, coefs!=0]
print(X_lasso.shape, Y.shape)
#check here
reg=Lasso(alpha=0, fit_intercept=False,max_iter=5000,positive=True)
reg.fit(X_lasso, Y)
#check here
print(reg.coef_)


