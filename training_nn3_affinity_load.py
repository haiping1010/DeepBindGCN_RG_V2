import numpy as np
import pandas as pd
import sys, os
from random import shuffle
import torch
import torch.nn as nn
from models.gat import GATNet
from models.gat_gcn import GAT_GCN
from models.gcn import GCNNet
from models.ginconv import GINConvNet
#from  read_smi_protein import *
from torch_geometric.data import InMemoryDataset, DataLoader
from torch_geometric import data as DATA
from utils import *

# training function at each epoch
def train(model, device, train_loader, optimizer, epoch, TRAIN_BATCH_SIZE):
    print('Training on {} samples...'.format(len(train_loader.dataset)))
    model.train()
    for batch_idx, data in enumerate(train_loader):
        data = data.to(device)
        optimizer.zero_grad()
        output = model(data,TRAIN_BATCH_SIZE,device)
        #output = model(data)
        loss = loss_fn(output, data.y.view(-1, 1).float().to(device))
        loss.backward()
        optimizer.step()
        if batch_idx % LOG_INTERVAL == 0:
            print('Train epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(epoch,
                                                                           batch_idx * len(data.x),
                                                                           len(train_loader.dataset),
                                                                           100. * batch_idx / len(train_loader),
                                                                           loss.item()))

def predicting(model, device, loader,TRAIN_BATCH_SIZE):
    model.eval()
    total_preds = torch.Tensor()
    total_labels = torch.Tensor()
    print('Make prediction for {} samples...'.format(len(loader.dataset)))
    with torch.no_grad():
        for data in loader:
            data = data.to(device)
            output = model(data,TRAIN_BATCH_SIZE,device)
            total_preds = torch.cat((total_preds, output.cpu()), 0)
            total_labels = torch.cat((total_labels, data.y.view(-1, 1).cpu()), 0)
    return total_labels.numpy().flatten(),total_preds.numpy().flatten()


#modeling = [GINConvNet, GATNet, GAT_GCN, GCNNet][int(sys.argv[2])]
#model_st = modeling.__name__
modeling = GAT_GCN
model_st = modeling.__name__

import sys
sys.setrecursionlimit(100000)

#cuda_name = "cuda:0"
cuda_name = "cuda"
print (str(len(sys.argv))+'xxxx')
if len(sys.argv)>1:
    cuda_name = ["cuda:0","cuda:1"][int(sys.argv[1])]
print('cuda_name:', cuda_name)
#cuda_name = "cuda:0"
TRAIN_BATCH_SIZE = 500   
LR = 0.0005
LOG_INTERVAL = 20
NUM_EPOCHS = 2000

print('Learning rate: ', LR)
print('Epochs: ', NUM_EPOCHS)

import glob
from torch.utils.data.dataset import Dataset, ConcatDataset


from torch.utils.data import random_split
np.random.seed(0)
torch.manual_seed(0)

import torch
from torch.utils.data import Subset
from sklearn.model_selection import train_test_split

from sklearn import metrics

def acc(true, pred):

    return np.sum(true == pred) * 1.0 / len(true)

def aucJ(true_labels, predictions):

    fpr, tpr, thresholds = metrics.roc_curve(true_labels, predictions, pos_label=1)
    auc = metrics.auc(fpr,tpr)

    return auc


def train_val_dataset(dataset, val_split=0.25):
    train_idx, val_idx = train_test_split(list(range(len(dataset))), test_size=val_split)
    datasets = {}
    datasets['train'] = Subset(dataset, train_idx)
    datasets['val'] = Subset(dataset, val_idx)
    return datasets

dataset_pos=TestbedDataset2(root='data1', dataset='L_P_train_1')

for name in range(2,4):
    print (name)
    train_data = TestbedDataset2(root='data1', dataset='L_P_train_'+str(name))
    dataset_pos=dataset_pos + train_data
print (dataset_pos.__len__())



print (torch.cuda.get_device_name(0))
print (torch.cuda.is_available())
# Main program: iterate over different datasets
for datasetxxxx in 'L':
        test_loader = DataLoader(dataset_pos, batch_size=TRAIN_BATCH_SIZE, shuffle=True)       
        #print('Training on {} samples...'.format(len(train_loader.dataset)))
        #for data in train_loader:
        #    #x, edge_index, batch = data.x, data.edge_index, data.batch
        #    print(data.x)
        ##for batch_idx, data in enumerate(train_loader):
        #     print  (data)
        #     x, edge_index, batch = data.x, data.edge_index, data.batch
        ##     print (x, edge_index, batch)
        # get protein input
        #target = data.target
        # training the model
        device = torch.device(cuda_name if torch.cuda.is_available() else "cpu")
        #device = torch.device("cpu")
        #device=torch.device("cuda")
        model = modeling().to(device)
        #model.train()
        loss_fn = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=LR)
        best_mse = 1000
        best_ci = 0
        best_epoch = -1
        
        ###train(model, device, train_loader, optimizer, 1, TRAIN_BATCH_SIZE)
        for epoch in range(1100,2100,100):
            #print (epoch)
            #model_file_name = 'full_model_out2000.model'
            model_file_name = 'full_model_out'+str(epoch)+'.model'
            model.eval()
            model = torch.load(model_file_name)
            #G,P,N = predicting(model, device, test_loader,TRAIN_BATCH_SIZE)

            G,P = predicting(model, device, test_loader,TRAIN_BATCH_SIZE)
            
            print ("epoch"+str(epoch), rmse(G,P),mse(G,P),pearson(G,P),spearman(G,P),ci(G,P))
            #print('epoch:',str(epoch+1))
            #print ('rmse:', rmse(G,P))
            #print ('mse:',mse(G,P) )
            #print (G)
            #print (P)
            #print ('pearson',pearson(G,P))
            #print ('spearman',spearman(G,P))
            #print ('ci',ci(G,P))
'''
            G,P = predicting(model, device, test_loader)
            ret = [rmse(G,P),mse(G,P),pearson(G,P),spearman(G,P),ci(G,P)]
            if ret[1]<best_mse:
                torch.save(model.state_dict(), model_file_name)
                with open(result_file_name,'w') as f:
                    f.write(','.join(map(str,ret)))
                best_epoch = epoch+1
                best_mse = ret[1]
                best_ci = ret[-1]
                print('rmse improved at epoch ', best_epoch, '; best_mse,best_ci:', best_mse,best_ci,model_st,dataset)
            else:
                print(ret[1],'No improvement since epoch ', best_epoch, '; best_mse,best_ci:', best_mse,best_ci,model_st,dataset)
'''



