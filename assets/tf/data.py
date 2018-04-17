
import imageio
import matplotlib.pyplot as plt
import os
import glob
import random
import numpy as np
from skimage.transform import resize



#root_dir = r'/home/lie/kaggle/nuclei/input/'
#train_dir = root_dir + r"stage1_train/"
root_dir = r"E:/src/nuclei/data/"
train_dir = root_dir + r"train/"

def image_id_to_filename(id):
    return train_dir + "/" + id + r"/images/" + id + ".png"
def image_id_to_mask_dir(id):
    return train_dir + "/" + id + r"/masks"

def read_image_ids():
    dir = train_dir
    ids = os.listdir(dir)
    return ids

image_ids = read_image_ids()
def get_all_image_ids():
    return image_ids

def read_image_masks(image_id):
    image_file = train_dir + "/" + image_id +"/images/" + image_id + ".png"
    masks_dir = train_dir+"/" + image_id +"/masks/*"
    mask_files = glob.glob(masks_dir)
    masks = np.stack([imageio.imread(mask_file) for mask_file in mask_files], axis=-1)
    return masks


batch_size = 4
def sample_image_ids(batch_size):
    return [random.randint(0, len(image_ids)-1) for _ in range(0,batch_size)]

def load_one_img(id):
    img = imageio.imread(image_id_to_filename(id))[:, :, :3]
    img = resize(img, [512, 512], mode='constant')
    masks = read_image_masks(id)
    masks = resize(masks, [512, 512], mode='constant')
    masks = np.max(masks, axis=-1)
    masks = (masks > 0)*1
    return img,masks

def get_one_batch():
    idxs = sample_image_ids(batch_size)
    data = [load_one_img(image_ids[idx]) for idx in idxs]

    img, mask = list(zip(*data))

    img = np.stack(img)
    mask = np.stack(mask)

    return img, mask

def data_generator():
    for id in image_ids:
        yield load_one_img(id)


if __name__ == "__main__":
    img, mask = get_one_batch()

    print(img.shape)
    print(mask.shape)

    # plt.figure()
    # plt.imshow(img[0])
    # plt.figure()
    # plt.imshow(mask[0])
    # plt.show()
