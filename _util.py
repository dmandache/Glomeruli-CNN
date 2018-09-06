import os
import random
import math
import numpy as np
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from scipy.misc import imsave
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm


# doesn't work
def confusion_matrix(y_true, y_pred):
    raw_data = {'actual': y_true,
                'preds': y_pred}
    df = pd.DataFrame(raw_data, columns=['actual', 'preds'])
    tab = pd.crosstab(df.actual, df.preds, margins=True)
    print(tab)
    with open("confusion-matrix.txt", "w") as text_file:
        text_file.write(tab.to_string())


def get_output_layer(model, layer_name):
    # get the symbolic outputs of each "key" layer (we gave them unique names).
    layer_dict = dict([(layer.name, layer) for layer in model.layers])
    layer = layer_dict[layer_name]
    return layer


def get_n_samples(n=32, dir=None, target_size=(299,299)):
    samples = []
    files = os.listdir(dir)
    random.seed(9001)

    for i in range(n):
        random_file = random.choice(files)
        path_to_random_file = dir + '/' + random_file
        try:
            img = Image.open(path_to_random_file)
        except IOError:
            i = i-1
            continue
        if target_size is not 'original':
            img_new = Image.Image.resize(img,target_size)
        else: img_new = img
        x = np.asarray(img_new, dtype='float32')
        x /= 255
        samples.append(x)

    samples = np.stack(samples, axis=0)
    #samples = np.expand_dims(samples, axis=3)
    return samples


def get_all_imgs_from_folder(dir, target_size=(299,299)):
    samples = []
    files = os.listdir(dir)

    for f in files:
        path = dir + '/' + f
        try:
            img = Image.open(path)
        except IOError:
            print("Could not open image file ", f)
            continue
        if target_size is not None:
            img_new = Image.Image.resize(img, target_size)
        else:
            img_new = img
        x = np.asarray(img_new, dtype='float32')
        x /= 255
        samples.append(x)

    samples = np.stack(samples, axis=0)
    # samples = np.expand_dims(samples, axis=3)
    return samples



def plot_to_grid(batch, grid_size=None, random=False):

    img_size = batch[0].shape[0]

    nt = len(batch)  # nt = total number of images

    if grid_size is None:
        grid_size = math.ceil(math.sqrt(nt))

    try:
        ch = batch[0].shape[2]
    except:
        ch = 1

    n = grid_size * grid_size  # n = images displayed (based on grid size)

    if n <= nt:
        if random:
            kept_idxs = random.sample(range(nt), n)
        else:
            kept_idxs = range(n)
        kept_patches = [batch[i] for i in kept_idxs]
    else:
        n0 = n - nt
        kept_patches = list(batch)
        for i in range(n0):
            if ch == 1:
                kept_patches.append(np.zeros((img_size, img_size)))
            else:
                kept_patches.append(np.zeros((img_size, img_size, ch)))

    # build a black picture with enough space for
    # our 8 x 8 filters of size 128 x 128, with a 5px margin in between
    margin = 3
    width = grid_size * img_size + (grid_size - 1) * margin
    height = grid_size * img_size + (grid_size - 1) * margin
    if ch == 1:
        stitched_images = np.zeros((width, height))
    else:
        stitched_images = np.zeros((width, height, ch))

    # fill the picture with our saved filters
    for i in range(grid_size):
        for j in range(grid_size):
            img = kept_patches[i * grid_size + j]
            if ch == 1:
                stitched_images[(img_size + margin) * i: (img_size + margin) * i + img_size,
                                (img_size + margin) * j: (img_size + margin) * j + img_size] = img
            else:
                stitched_images[(img_size + margin) * i: (img_size + margin) * i + img_size,
                                (img_size + margin) * j: (img_size + margin) * j + img_size, ] = img
    return stitched_images


def plot_to_grid_with_proba(batch, probabilities, grid_size=None, shuffle=False):

    img_size = batch[0].shape[0]

    nt = len(batch)  # nt = total number of images

    if grid_size is None:
        grid_size = math.ceil(math.sqrt(nt))

    try:
        ch = batch[0].shape[2]
    except:
        ch = 1

    n = grid_size * grid_size  # n = images displayed (based on grid size)

    if n <= nt:
        if shuffle:
            kept_idxs = random.sample(range(nt), n)
        else:
            kept_idxs = range(n)
        kept_patches = [batch[i] for i in kept_idxs]
        kept_probas = [probabilities[i] for i in kept_idxs]
    else:
        n0 = n - nt
        kept_patches = list(batch)
        kept_probas = probabilities
        for i in range(n0):
            if ch == 1:
                kept_patches.append(np.zeros((img_size, img_size)))
            else:
                kept_patches.append(np.zeros((img_size, img_size, ch)))

    # build a black picture with enough space for
    # our 8 x 8 filters of size 128 x 128, with a 5px margin in between
    margin = 3
    width = grid_size * img_size + (grid_size - 1) * margin
    height = grid_size * img_size + (grid_size - 1) * margin
    if ch == 1:
        stitched_images = np.zeros((width, height))
    else:
        stitched_images = np.zeros((width, height, ch))

    # fill the picture with our saved filters
    for i in range(grid_size):
        for j in range(grid_size):
            idx = i * grid_size + j
            img = kept_patches[idx]

            if idx < nt:
                proba = kept_probas[idx]
                proba_text = "{:.3f}%".format(100 - proba * 100)
                img = write_on_image(img,proba_text)

            if ch == 1:
                stitched_images[(img_size + margin) * i: (img_size + margin) * i + img_size,
                                (img_size + margin) * j: (img_size + margin) * j + img_size] = img
            else:
                stitched_images[(img_size + margin) * i: (img_size + margin) * i + img_size,
                                (img_size + margin) * j: (img_size + margin) * j + img_size, ] = img
    return stitched_images


def write_on_image(img, text):
    img_pil = Image.fromarray(np.uint8(img*255))
    draw = ImageDraw.Draw(img_pil)
    # font = ImageFont.truetype(<font-file>, <font-size>)
    #font = ImageFont.truetype("sans-serif.ttf", 12)
    # draw.text((x, y),"Sample Text",(r,g,b))
    draw.text((10, 10), text, (255, 128, 128))
    img_np = np.asarray(img_pil)/255
    return img_np


def apply_jet_colormap(img):
    img /= np.max(img)
    img = Image.fromarray(np.uint8(cm.jet(img) * 255))
    return img


def gaussian_blur(img, kernel=2):
    pil_img = Image.fromarray(np.uint8(img))
    pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=kernel))
    return pil_img


# useless, keep it fpr syntax
def merge_history_dicts(d1, d2, epoch):
    if isinstance(d1, dict):
        d2 = {key: {key_ + epoch: val_ for key_, val_ in val.items()}
                     for key, val in d2.items()}
    d = {key: (d1[key], d2[key]) for key in d2}
    return d


def find_true_pred(y_actual, y_pred, x):
    TP = []
    FP = []
    TN = []
    FN = []
    for i in range(len(y_pred)):
        if y_actual[i]==y_pred[i]==1:
           TP.append(x[i,:,:,:])
    for i in range(len(y_pred)):
        if y_pred[i]==1 and y_actual[i]==0:
           FP.append(x[i,:,:,:])
    for i in range(len(y_pred)):
        if y_actual[i]==y_pred[i]==0:
           TN.append(x[i,:,:,:])
    for i in range(len(y_pred)):
        if y_pred[i]==0 and y_actual[i]==1:
           FN.append(x[i,:,:,:])
    if TP:
        imsave("true_positives.png", TP)
    if FP:
        imsave("false_positives.png", FP)
    if TN:
        imsave("true_negatives.png", TN)
    if FN:
        imsave("false_negatives.png", FN)
    return(TP, FP, TN, FN)