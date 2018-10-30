import os
import sys
import argparse
import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
import make_model
import models
import cv2
import LenslessDataset
from normalize import CastTensor
from torchvision import datasets, transforms
import numpy as np

def CreateArgsParser():
    parser =  argparse.ArgumentParser(description='Evaluate Pretrained Model')

    parser.add_argument('--model', default= None, required= True,
                    help='file to load checkpoint from')
    parser.add_argument('--root-dir', required= True,  
                    help='root directory where enclosing image files are located')
    parser.add_argument('--test-csv', required= True, 
                    help='path to the location of the test csv')
    parser.add_argument('--train-csv', required= True, 
                    help='path to the location of the training csv')
    parser.add_argument('--guassian', default= None, type= int,
                    help='Adds gaussian noise with std given by user')
    parser.add_argument('--shift', default= None, type= int, 
                    help='Shifts the image by the int given by user')
    parser.add_argument('--bias', default= None, type= int,
                    help='Adds bias noise to the image by the int given by user')
    return parser

def main():
    args = CreateArgsParser().parse_args()

    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")

    if use_cuda is True:
        cudnn.benchmark = True

    if args.model is not None:
        if os.path.isfile(args.model):
            print("=> loading checkpoint '{}'".format(args.model))
            checkpoint = torch.load(args.model)

            network = make_model.Model(make_model.make_layers(models.feature_layers[checkpoint['f_layers']]), 
                    make_model.make_classifier_layers(models.classifier_layers[checkpoint['c_layers']]), checkpoint= True)

            network.load_state_dict(checkpoint['state_dict'])
            network.eval()
            network = network.to(device)

            batch_size = checkpoint['batch_size']
            resize = checkpoint['resize']
            print("=> loaded model '{}'"
                  .format(args.model))
        else:
            print("=> no checkpoint found at '{}'".format(args.model))
            raise AssertionError("Failed to load Model")

    if torch.cuda.device_count() > 1:
        print("===> Number of GPU's available: %d" % torch.cuda.device_count())
        network = nn.DataParallel(network)

    print("\nBatch Size: %d" % (batch_size))

    if args.shift is not None:
        data_transform = transforms.Compose([
        transforms.Resize((resize, resize)),
        Shift(np.float32([[1, 0, args.shift], [0, 1, 0]])),
        transforms.ToTensor(),
        CastTensor('torch.FloatTensor'),
        transforms.Normalize([40414.038877341736], [35951.78672059086])
        ])
    elif args.guassian is not None:
        data_transform = transforms.Compose([
        transforms.Resize((resize, resize)),
        GuassianNoise(args.gaussian),
        transforms.ToTensor(),
        CastTensor('torch.FloatTensor'),
        transforms.Normalize([40414.038877341736], [35951.78672059086])
        ])
    elif args.bias is not None:
        data_transform = transforms.Compose([
        transforms.Resize((resize, resize)),
        BiasNoise(args.bias),
        transforms.ToTensor(),
        CastTensor('torch.FloatTensor'),
        transforms.Normalize([40414.038877341736], [35951.78672059086])
        ])

    # load the test dataset
    test_dataset = LenslessDataset.LenslessDataset(
    csv_file= args.test_csv,
    root_dir= args.root_dir,
    transform= data_transform
    )

    test_loader = torch.utils.data.DataLoader(
    test_dataset,
    batch_size= batch_size,
    shuffle= True,
    num_workers= 2,
    pin_memory= True
    )

    test_epoch(network, test_loader, device)

def test_epoch(model, test_loader, device):
    test_loss = 0
    accuracy = 0
    correct = 0

    # validate the model over the test set and record no gradient history
    with torch.no_grad():
        for batch_idx, (input, target) in enumerate(test_loader):

            input, target = input.to(device), target.to(device)

            output = model(input)
            # sum up batch loss
            test_loss += F.cross_entropy(output, target, size_average=False).item()
            # get the index of the max log-probability
            pred = output.max(1, keepdim=True)[1]
            correct += pred.eq(target.view_as(pred)).sum().item()
            
            del input, target, output

    test_loss /= len(test_loader.dataset)
    accuracy = 100. * correct / len(test_loader.dataset)
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.1f}%)\n'
          .format(test_loss, correct, len(test_loader.dataset),
                  100. * correct / len(test_loader.dataset)))

'''
Shifts the image by shift. Shift here IS the shifting array.
The shifting matrix has dimensions 2x3 Ex: [[1, 0, s], [0, 1, t]], where s and t are the shifting constants
and the array is an np.float32
'''
class Shift(object):
    def __init__(self, shift):
        self.shift = shift

    def __call__(self, img):
        im = np.array(img, dtype= np.float)
        rows, cols = im.shape
        shifted_img = cv2.wrapAffine(im, self.shift, (cols, rows))

        return shifted_img

# class Defocus(network, batch_size, device, test_csv, root_dir):

'''
Adds bias noise to the input image.
The bias is added when the object is called
'''
class BiasNoise(object):
    def __init__(self, bias_noise):
        self.bias_noise = bias_noise

    def __call__(self, img):
        noisy_img = np.array(img, dtype= np.float) + self.bias_noise
        rows, cols = noisy_img.shape
        noisy_img = noisy_img.reshape((cols, rows, 1))
        # noisy_img_clipped = np.clip(noisy_img, 0, 255)  # we might get out of bounds due to noise

        return noisy_img

'''
Adds Guassian Noise to the image with mean and std.
The bias is added when the object is called
'''
class GuassianNoise(object):
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def __call__(self, img):
        noisy_img = np.array(img, dtype= np.float)
        rows, cols = noisy_img.shape
        noisy_img = img + np.random.normal(mean, std, img.shape)
        noisy_img = noisy_img.reshape((cols, rows, 1))
        # noisy_img_clipped = np.clip(noisy_img, 0, 255)  # we might get out of bounds due to noise

        return noisy_img

    
if __name__ == '__main__':
    main()
