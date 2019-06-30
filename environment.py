import gym
from alpha_vantage import foreignexchange, techindicators,cryptocurrencies
import numpy as np
from gym.utils import seeding
from gym import spaces
import agent
import utils
from matplotlib import pyplot as plt

#Check Out what gym.Env should be returning



'''FOCUS ON ONLY ONE TRADE DECISIONS'''

'''
Primary Rules for trading:

1. Only trading ONE Ticker
2. Only one position can be opened at any single point in time
3. Can only hold long and no short

--> All these parameters can be changed later when I have more experience in machine learning
'''

class tradingEnvironment(gym.Env):

    #The __init__ method is only called once in the firstRun with trainData and initial to Invest
    def __init__(self,trainData,cashInHand,uPnL):

        self.n_Assets=1 #This has to be the number of currencies I am trading with

        '''Generally might not need to use environments but check when you run it'''

        self.fig = plt.figure()
        self.x = list()
        self.y = list()
        self.r=list()
        fig, self.ax1 = plt.subplots()
        self.ax2 = self.ax1.twinx()

        env = gym.make('Copy-v0')
        env.reset()

        self.trainData=trainData
        self.currentStep=0
        self.maxStep=100

        self.currency_Price=None


        #self.step(actionsReceived.action)

        self.initValue=cashInHand
        self.initPnL=uPnL

        self.unrealizedPnl=self.initPnL

        self.tradesInfo=np.zeros((10**5,5)) #Array with ID|Ticker Symbol|BOUGHT PRICE|SOLD PRICE|VOLUME in the future this can have quantity as well collumns

        '''
        Actions: Buy, Sell, Hold
        States: Long, Neutral
        '''

        self.openPositions=0


        '''------------Fix the Code Below----------'''

        states=['Neutral','Long']
        actions=['Buy','Sell','Hold']

        self.observation_space=spaces.Discrete(len(states))
        self.action_space=spaces.Discrete(len(actions))

        self._seed()


    def _step(self, action):
        '''Fix the reward and the updateInfotable methods'''
        self.updatePositions(action)
        self.currency_Price=self.trainData[self.currentStep]

        self.y.append(self.currency_Price)
        self.x.append(self.currentStep)
        self.ax1.plot(self.x, self.y,'-g')




        observation=self.observeCurrentState()
        self.updateInfoTable(action)
        reward=self.updatePnl()

        self.r.append(reward)
        self.ax2.plot(self.x,self.r,'r')
        plt.draw()

        info={'unrealized PnL':self.unrealizedPnl}
        if self.currentStep==self.maxStep:
            done = True
        else:
            done=False
            self.currentStep+=1

        self.agent.replay(observation, reward, done, info)

        return observation,reward,done,info

    def _reset(self):
        '''------When you reset you need to reset all the other variables such as initial pnl etc------'''
        self.openPositions=0
        self.currentStep=0
        self.updateInfoTable('Delete')
        return self.observeCurrentState()

    def _seed(self, seed=None):
        seeds=seeding.np_random(seed)
        return [seeds]

    def _render(self):
        return None

    def updateInfoTable(self,action):

        if action=='Delete':
            self.tradesInfo=np.zeros((10**5,5))
        else:
            if action==2:
                return
            elif action==0:
                self.tradesInfo[self.currentStep, 2] = self.currency_Price
            elif action==1:
                self.tradesInfo[self.currentStep, 3] = self.currency_Price

            self.tradesInfo[self.currentStep, 0] = self.currentStep + 1
            self.tradesInfo[self.currentStep, 4] = 100
            '''Lets assume volume is constant at 100 for now'''
        return

    def updatePositions(self,action):
            if (action==0):
                self.openPositions+=1
            elif (action==1):
                self.openPositions+=-1

    def rememberAgent(self,agent):
        self.agent=agent


    def updatePnl(self):

        ids=self.tradesInfo[:,0]
        a=len(np.nonzero(ids))-1
        Volume=self.tradesInfo[a,4]

        if self.openPositions==0:
            return 0
        elif self.openPositions==1:
            BoughtPrice = self.tradesInfo[a, 2]
            SoldPrice = self.tradesInfo[a-1, 3]
            updatedPnl=Volume*(SoldPrice-BoughtPrice)
            return updatedPnl


    def observeCurrentState(self):
        '''States  Neutral(0) or Long(1) thus return ALL actions for that state'''
        Q=self.agent.Q
        return Q[:,self.openPositions], self.openPositions


