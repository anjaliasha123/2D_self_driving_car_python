# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 16:50:17 2019

@author: JCMat
"""

import numpy as np
import random
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.autograd as autograd
from torch.autograd import Variable


#first step creating neural network for processing the q values

class NeuralNetwork(nn.Module):
    def __init__(self, input_size, nb_action):
        super(NeuralNetwork, self).__init__()
        self.input_size = input_size
        self.nb_action = nb_action
        self.f1 = nn.Linear(input_size, 30)
        self.f2 = nn.Linear(30, nb_action)
        
    #feed forward network
    def forward(self, state):
        x = F.relu(self.f1(state))
        Q_values = self.f2(x)
        return Q_values
    
    
#experience replay to consider previous actions
class ExperienceReplayMemory(object):
    #initialising capacity and creating memory
    def __init__(self, capacity):
        self.c = capacity
        self.memory = []
        
    def push_action(self, event):
        self.memory.append(event)
        if len(self.memory)>self.c:
            del self.memory[0]
    #obtaining a sample of elements from the memory for experience replay        
    def sample(self, batch_size):
        samples = zip(*random.sample(self.memory, batch_size))
        return map(lambda x: Variable(torch.cat(x, 0)), samples)
    
#implementing deep q learning
        
class DeepQNetwork():
    
    def __init__(self, input_size, nb_action, gamma):
        self.gamma = gamma
        self.reward_window = []
        self.model = NeuralNetwork(input_size, nb_action)
        self.memory = ExperienceReplayMemory(100000)
        self.optimizer = optim.Adam(self.model.parameters(), lr = 0.001)
        self.last_state = torch.Tensor(input_size).unsqueeze(0)
        self.last_action = 0
        self.last_reward = 0
        
    def select_action(self, state):
        probs = F.softmax(self.model(Variable(state, volatile = True))*100) # epsilon=100
        action = probs.multinomial()
        return action.data[0,0]
    
    def learn(self, batch_state, batch_next_state, batch_reward, batch_action):
        outputs = self.model(batch_state).gather(1, batch_action.unsqueeze(1)).squeeze(1)
        next_outputs = self.model(batch_next_state).detach().max(1)[0]
        target = self.gamma*next_outputs + batch_reward
        td_loss = F.smooth_l1_loss(outputs, target)
        self.optimizer.zero_grad()
        td_loss.backward(retain_variables = True)
        self.optimizer.step()
        
    def update(self, reward, new_signal):
        new_state = torch.Tensor(new_signal).float().unsqueeze(0)
        self.memory.push_action((self.last_state, new_state, torch.LongTensor([int(self.last_action)]), torch.Tensor([self.last_reward])))
        action = self.select_action(new_state)
        if len(self.memory.memory) > 100:
            batch_state, batch_next_state, batch_action, batch_reward = self.memory.sample(100)
            self.learn(batch_state, batch_next_state, batch_reward, batch_action)
        self.last_action = action
        self.last_state = new_state
        self.last_reward = reward
        self.reward_window.append(reward)
        if len(self.reward_window) > 1000:
            del self.reward_window[0]
        return action
    
    def score(self):
        return sum(self.reward_window)/(len(self.reward_window)+1.)
    
    def save(self):
        torch.save({'state_dict': self.model.state_dict(),
                    'optimizer' : self.optimizer.state_dict(),
                   }, 'new_brain.pth')
    
    def load(self):
        if os.path.isfile('new_brain.pth'):
            print("=> loading checkpoint... ")
            checkpoint = torch.load('new_brain.pth')
            self.model.load_state_dict(checkpoint['state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            print("done !")
        else:
            print("no checkpoint found...")
    
    
    
    
    
    
    
    
    
    
        