from keras.layers import Input, Dense, Dropout, Conv2D, BatchNormalization
from keras.models import Model, Sequential
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
from keras.models import load_model
import numpy as np
import numpy.linalg as LA
import os
import tensorflow as tf
import scipy.io as sio

Nt=32
Nr=16
SNR=20.0**(20/10.0) # transmit power
# DFT matrix
def DFT_matrix(N):
    m, n = np.meshgrid(np.arange(N), np.arange(N))
    omega = np.exp( - 2 * np.pi * 1j / N )
    D = np.power( omega, m * n )
    return D

def sub_dftmtx(A, N):
    D=A[:,0:N]
    return D

F_DFT=DFT_matrix(Nt)/np.sqrt(Nt)
W_DFT=DFT_matrix(Nr)/np.sqrt(Nr)


Nt_beam=32
F_RF=F_DFT[:,0:Nt_beam]
F=F_RF
F_conj=np.conjugate(F)
F_conjtransp=np.transpose(F_conj)
FFH=np.dot(F,F_conjtransp)
Nr_beam=16
W_RF=W_DFT[:,0:Nr_beam]
W=W_RF
W_conj=np.conjugate(W)
W_conjtransp=np.transpose(W_conj)
WWH=np.dot(W,W_conjtransp)

scale=2
fre=2
time_steps=1

############## training set generation ##################
data_num_train=500
data_num_file=500
H_train=np.zeros((data_num_train,Nr,Nt,2*fre), dtype=float)
H_train_noisy=np.zeros((data_num_train,Nr,Nt,2*fre*time_steps), dtype=float)
filedir = os.listdir('/Users/limingfa/git/CNN4CE/SPR-CNN/2fre4time_data')
n=0
SNRr=5
SNR_factor=5.9
for filename in filedir:
    newname = os.path.join('/Users/limingfa/git/CNN4CE/SPR-CNN/2fre4time_data', filename)
      
    data = sio.loadmat(newname)
    channel = data['ChannelData_fre']
    for i in range(data_num_file):
        for j in range(fre):
            a=channel[:,:,j,i]
            for t in range(time_steps):
                a1=a[:,t*Nr:t*Nr+Nr]
                H=np.transpose(a1)
                H_re=np.real(H)
                H_im = np.imag(H)
                H_train[n * data_num_file + i, :, :, 2 * j] = H_re / scale
                H_train[n * data_num_file + i, :, :, 2 * j + 1] = H_im / scale
                N = np.random.normal(0, 1 / np.sqrt(2), size=(Nr, Nt_beam)) + 1j * np.random.normal(0, 1 / np.sqrt(2), size=(Nr, Nt_beam))
                NFH = np.dot(N, F_conjtransp)
                Y = H + 1.0 / np.sqrt(SNR_factor * SNR) * NFH
                SNRr = SNRr + SNR_factor * SNR * (LA.norm(H)) ** 2 / (LA.norm(NFH)) ** 2
                Y_re = np.real(Y)
                Y_im = np.imag(Y)
                H_train_noisy[n * data_num_file + i, :, :, j * 2 * time_steps + 2 * t] = Y_re / scale
                H_train_noisy[n * data_num_file + i, :, :, j * 2 * time_steps + 2 * t + 1] = Y_im / scale
    n=n+1
print(n)
print(SNRr/(data_num_train*fre*time_steps))
print(H_train.shape,H_train_noisy.shape)
index1=np.where(abs(H_train)>1)
row_num=np.unique(index1[0])
H_train=np.delete(H_train,row_num,axis=0)
H_train_noisy=np.delete(H_train_noisy,row_num,axis=0)
print(len(row_num))
print(H_train.shape,H_train_noisy.shape)

############## testing set generation ##################
data_num_test=500
data_num_file=500
H_test=np.zeros((data_num_test,Nr,Nt,2*fre), dtype=float)
H_test_noisy=np.zeros((data_num_test,Nr,Nt,2*fre*time_steps), dtype=float)
filedir = os.listdir('/Users/limingfa/git/CNN4CE/SPR-CNN/2fre4time_data') # type the path of testing data (Testing data should be different from training data. Here use the same data just for ease of demonstration.)
n=0
SNRr=0
SNR_factor=5.9
for filename in filedir:
    newname = os.path.join('/Users/limingfa/git/CNN4CE/SPR-CNN/2fre4time_data', filename)
    data = sio.loadmat(newname)
    channel = data['ChannelData_fre']
    for i in range(data_num_file):
        for j in range(fre):
            a=channel[:,:,j,i]
            for t in range(time_steps):
                a1=a[:,t*Nr:t*Nr+Nr]
                H=np.transpose(a1)
                H_re=np.real(H)
                H_im = np.imag(H)
                H_test[n * data_num_file + i, :, :, 2 * j] = H_re / scale
                H_test[n * data_num_file + i, :, :, 2 * j + 1] = H_im / scale
                N = np.random.normal(0, 1 / np.sqrt(2), size=(Nr, Nt_beam)) + 1j * np.random.normal(0, 1 / np.sqrt(2), size=(Nr, Nt_beam))
                NFH = np.dot(N, F_conjtransp)
                Y = H + 1.0 / np.sqrt(SNR_factor * SNR) * NFH
                SNRr = SNRr + SNR_factor * SNR * (LA.norm(H)) ** 2 / (LA.norm(NFH)) ** 2
                Y_re = np.real(Y)
                Y_im = np.imag(Y)
                H_test_noisy[n * data_num_file + i, :, :, j * 2 * time_steps + 2 * t] = Y_re / scale
                H_test_noisy[n * data_num_file + i, :, :, j * 2 * time_steps + 2 * t + 1] = Y_im / scale
    n = n + 1
print(n)
print(SNRr/(data_num_test*fre*time_steps))
print(H_test.shape,H_test_noisy.shape)
index3 = np.where(abs(H_test) > 1)
row_num = np.unique(index3[0])
H_test = np.delete(H_test, row_num, axis=0)
H_test_noisy = np.delete(H_test_noisy, row_num, axis=0)
print(len(row_num))
print(H_test.shape, H_test_noisy.shape)
print(((H_test)**2).mean())

K=3
input_dim=(Nr,Nt,2*fre*time_steps)
model = Sequential()
model.add(Conv2D(filters=64, kernel_size=(K,K), padding='Same', activation='relu', input_shape=input_dim))
model.add(BatchNormalization())
model.add(Conv2D(filters=64, kernel_size=(K,K), padding='Same', activation='relu'))
model.add(BatchNormalization())
model.add(Conv2D(filters=64, kernel_size=(K,K), padding='Same', activation='relu'))
model.add(BatchNormalization())
model.add(Conv2D(filters=64, kernel_size=(K,K), padding='Same', activation='relu'))
model.add(BatchNormalization())
model.add(Conv2D(filters=64, kernel_size=(K,K), padding='Same', activation='relu'))
model.add(BatchNormalization())
model.add(Conv2D(filters=64, kernel_size=(K,K), padding='Same', activation='relu'))
model.add(BatchNormalization())
model.add(Conv2D(filters=64, kernel_size=(K,K), padding='Same', activation='relu'))
model.add(BatchNormalization())
model.add(Conv2D(filters=64, kernel_size=(K,K), padding='Same', activation='relu'))
model.add(BatchNormalization())
model.add(Conv2D(filters=64, kernel_size=(K,K), padding='Same', activation='relu'))
model.add(BatchNormalization())
model.add(Conv2D(filters=2*fre, kernel_size=(K,K), padding='Same', activation='tanh'))

# checkpoint
filepath = '2fre4time_SNR20_time1_32_16_200ep.keras'

checkpoint = ModelCheckpoint(filepath, monitor='val_loss', verbose=1, save_best_only=True, mode='min')
callbacks_list = [checkpoint]

adam=Adam(learning_rate=1e-4, beta_1=0.9, beta_2=0.999, epsilon=1e-08)
model.compile(optimizer=adam, loss='mse')
model.fit(H_train_noisy, H_train, epochs=200, batch_size=128, callbacks=callbacks_list, verbose=2, shuffle=True, validation_split=0.1)

# load model
CNN = load_model('2fre4time_SNR20_time1_32_16_200ep.hdf5')

decoded_channel = CNN.predict(H_test_noisy)
nmse2=np.zeros((data_num_test-len(row_num),1), dtype=float)
for n in range(data_num_test-len(row_num)):
    MSE=((H_test[n,:,:,:]-decoded_channel[n,:,:,:])**2).sum()
    norm_real=((H_test[n,:,:,:])**2).sum()
    nmse2[n]=MSE/norm_real
print(nmse2.sum()/(data_num_test-len(row_num))) # calculate NMSE of current training stage