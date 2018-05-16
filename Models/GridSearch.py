import os
import sys
import torch.nn as nn
import argsparse
import make_model
import models
from train import train

def CreateArgsParser():
    parser = argparse.ArgumentParser(description='Lensless Camera Pytorch')

    parser.add_argument('--batch-size', type=int, default=64, metavar='N',
                    help='input batch size for training (default: 64)')
    parser.add_argument('--epochs', type=int, default=10, metavar='N',
                    help='number of epochs to train (default: 20)')
    parser.add_argument('--lr', type=float, default=None, metavar='LR',
                    help='learning rate to start search Options: if None then will do a search ranging from 1 <= .01 <= .001 (default: None)')
    parser.add_argument('--momentum', type=float, default=0.9, metavar='M',
                    help='SGD momentum (default: 0.9)')
    parser.add_argument('--log-interval', type=int, default=10, metavar='N',
                    help='how many batches to wait before logging training status')
    parser.add_argument('--resize', type=int, default=None, 
                    help='dimensions of both height and width to be resized')
    parser.add_argument('--num-processes', type=int, default=2, metavar='N',
                    help='how many training processes to use (default: 2)')
    parser.add_argument('--optimizer', nargs='+', required= True, 
    				help= 'Type of optimizer to use. Select any number or combination. Options: SGD, AdaG, AdaD, Adam, RMS')
    parser.add_argument('--plateau', default= None, 
    				help= 'Measurement to plateau on. Options: loss, accuracy, None (for both) (default: None)')
    parser.add_argument('--root-dir', required= True, 
    				help='root directory where enclosing image files are located')
    parser.add_argument('--train-csv', required= True, 
    				help='path to the location of the training csv')
    parser.add_argument('--test-csv', required= True, 
    				help='path to the location of the test csv')


def main():
	args = CreateArgsParser().parse_args()


if __name__ == '__main__':
	main()