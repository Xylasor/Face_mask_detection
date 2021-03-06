# -*- coding: utf-8 -*-
"""EIASR_transfer.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MLDenqeX8i5zqYBomdf0-d62oSQhwzIc
"""

# Commented out IPython magic to ensure Python compatibility.
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, random_split
from torch.utils.data.sampler import SubsetRandomSampler
from torchvision import datasets, transforms, models
from torchvision.utils import make_grid

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# %matplotlib inline

import time

from google.colab import drive
from PIL import Image

drive.mount('/content/drive/')

display(Image.open('/content/drive/MyDrive/dataset/with_mask/0_0_0 copy 10.jpg'))

display(Image.open('/content/drive/MyDrive/dataset/without_mask/1.jpg'))

test_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((200,200)),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])
train_transform = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(20),
    transforms.ToTensor(),
    transforms.Resize((200,200)),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

train_data = datasets.ImageFolder('/content/drive/MyDrive/dataset',transform=train_transform)
test_data = datasets.ImageFolder('/content/drive/MyDrive/dataset',transform=test_transform)

np.random.seed(10)
class_names = train_data.classes
num_train = len(train_data)
indices = list(range(num_train))
split = int(np.floor(0.2 * num_train))
np.random.shuffle(indices)
train_idx, test_idx = indices[split:], indices[:split]

#balanced sampling (against the classes) + taking only the train_idx
train_sampler = SubsetRandomSampler(train_idx) 
test_sampler = SubsetRandomSampler(test_idx)

batch_size = 10 #only to display images, trained with batch = 100
workers = 0

train_loader = torch.utils.data.DataLoader(
    train_data, batch_size=batch_size, sampler=train_sampler, num_workers=workers)
test_loader = torch.utils.data.DataLoader(
    test_data, batch_size=batch_size, sampler=test_sampler, num_workers=workers)

for images,labels in train_loader: 
    break

print('Class:', [class_names[i] for i in labels])

im = make_grid(images, nrow=5)
# denormalization of images so they can be shown
inv_normalize = transforms.Normalize(
    mean=[-0.485/0.229, -0.456/0.224, -0.406/0.225],
    std=[1/0.229, 1/0.224, 1/0.225]
)
im_inv = inv_normalize(im)
plt.figure(figsize=(12,4))
# imshow wymaga podania wymiar??w w innej kolejno??ci
plt.imshow(np.transpose(im_inv.numpy(), (1, 2, 0)));

class ConvolutionalNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        
        self.conv1 = nn.Conv2d(3, 6, 3, 1)
        self.conv2 = nn.Conv2d(6, 12, 3, 1)
        #(((200-2)/2) - 2)/2 = 48.5; zaokr??glone w d????
        self.fc1 = nn.Linear(48*48*12, 200)
        self.fc2 = nn.Linear(200, 80)
        self.fc3 = nn.Linear(80, 2)

    def forward(self, X):
        X = F.relu(self.conv1(X)) # rectified linear unit - activation function
        X = F.max_pool2d(X, 2, 2)
        X = F.relu(self.conv2(X))
        X = F.max_pool2d(X, 2, 2)
        X = X.view(-1, 48*48*12)
        X = F.relu(self.fc1(X))
        X = F.relu(self.fc2(X))
        X = self.fc3(X)
        return F.log_softmax(X, dim=1) # converting logits to odds

CNNmodel = ConvolutionalNetwork()
CNNmodel.parameters

def train_model(CNNmodel, criterion, optimizer, epochs):
    start_time = time.time()

    train_losses = []
    test_losses = []
    train_correct = []
    test_correct = []

    for i in range(epochs):
        trn_corr = 0
        tst_corr = 0

        for b,(X_train,y_train) in enumerate(train_loader):

            b+=1

            # predykcja
            y_pred = CNNmodel(X_train)
            # strata
            loss = criterion(y_pred, y_train)
            
            # przewidywana klasa
            predicted = torch.max(y_pred,1)[1]
            # liczba poprawnych predykcji
            batch_corr = (predicted == y_train).sum()
            trn_corr += batch_corr

            # zerowanie gradientu
            optimizer.zero_grad()
            # propagacja wsteczna
            loss.backward()
            # uaktualnienie parametr??w
            optimizer.step()
            
#             if b%10 == 0:
            print(f'Epoka: {i}, seria: {b}, strata: {loss}, dok??adno????: {trn_corr.item()/b:7.3f}%')

        train_losses.append(loss)
        train_correct.append(trn_corr)

        # testowanie po ka??dej iteracji
        with torch.no_grad():
            for b, (X_test, y_test) in enumerate(test_loader):

                y_val = CNNmodel(X_test)

                predicted = torch.max(y_val,1)[1]
                tst_corr += (predicted == y_test).sum()

        loss = criterion(y_val, y_test)
        test_losses.append(loss)
        test_correct.append(tst_corr)

    total_time = (time.time() - start_time)/60
    
    print(f'Czas uczenia: {total_time} minut.')
    
    return CNNmodel, train_losses, test_losses, train_correct, test_correct

criterion = nn.CrossEntropyLoss()
CNNmodel = ConvolutionalNetwork()
optimizer = torch.optim.Adam(CNNmodel.parameters(), lr=0.001)

batch_size = 100

train_loader = torch.utils.data.DataLoader(
    train_data, batch_size=batch_size, sampler=train_sampler, num_workers=workers)
test_loader = torch.utils.data.DataLoader(
    test_data, batch_size=batch_size, sampler=test_sampler, num_workers=workers)

result = train_model(CNNmodel, criterion, optimizer, 5)

CNNmodel,train_losses, test_losses, train_correct, test_correct = result

model = ConvolutionalNetwork()
model.load_state_dict(torch.load('/content/drive/MyDrive/siec_od_0_pierwsza.pt'))

batch_size = 100

train_loader = torch.utils.data.DataLoader(
    train_data, batch_size=batch_size, sampler=train_sampler, num_workers=workers)
test_loader = torch.utils.data.DataLoader(
    test_data, batch_size=batch_size, sampler=test_sampler, num_workers=workers)

# RESNET 18
res18_mod = models.resnet18(pretrained = True)
print(res18_mod)

# Freezing parameters
for param in res18_mod.parameters():
    param.requires_grad = False

fc_features_num = res18_mod.fc.in_features
res18_mod.fc = nn.Linear(fc_features_num, 2)

optimizer = torch.optim.SGD(res18_mod.parameters(), lr=0.001, momentum=0.9)
criterion = nn.CrossEntropyLoss()
result_18 = train_model(res18_mod, criterion, optimizer, 10)

res18_mod,train_losses, test_losses, train_correct, test_correct = result_18

torch.save(res18_mod.state_dict(), '/content/drive/MyDrive/transfer_res18.pt')

torch.save(res18_mod, '/content/drive/MyDrive/model_transfer_res18.pt')

plt.plot([x/(len(train_idx)/100) for x in np.array(train_correct)], label='training')
plt.plot([x/(len(test_idx)/100) for x in np.array(test_correct)], label='testing')
plt.title('Accuracy at the end of each epoch')
plt.legend()

plt.plot([x/(len(train_idx)/100) for x in np.array(train_losses)], label='training')
plt.plot([x/(len(test_idx)/100) for x in np.array(test_losses)], label='testing')
plt.title('Loss at the end of each epoch')
plt.legend()



the_model = torch.load('/content/drive/MyDrive/model_transfer_res18.pt')





