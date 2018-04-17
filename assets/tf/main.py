
import tensorflow as tf

import matplotlib.pyplot as plt

import model
import data


IMAGE_SIZE = 512
graph_location = "logs"

#
# x = tf.placeholder(tf.float32, [None, IMAGE_SIZE, IMAGE_SIZE, 3], name="input_features")
# y = tf.placeholder(tf.float32, [None, IMAGE_SIZE, IMAGE_SIZE], name="input_label")


dataset = tf.data.Dataset.from_generator(data.get_all_image_ids,
                                 tf.string,
                                 tf.TensorShape([]))

#dataset = tf.data.DataSet.list_files(data.train_dir + "/*")
def read_image(image_id):
    img = tf.read_file(data.train_dir + image_id + "/images/" + image_id + ".png")
    img = tf.image.decode_image(img, channels=3)
    
    img = tf.expand_dims(img, 0)
    img = tf.image.resize_area(img, [512, 512])
    img = tf.squeeze(img)
    return img

def read_masks(image_id):

    masks_dir = data.train_dir+"/" + image_id +"/masks/*"
    mask_files = tf.matching_files(masks_dir)

    masks = tf.map_fn(tf.read_file, mask_files)


    masks = tf.map_fn(lambda x: tf.image.decode_png(x, channels=1, dtype=tf.uint8), masks, dtype=tf.uint8)


    masks = tf.image.resize_area(masks, [512, 512])

    masks = tf.reduce_max(masks, axis=0)
    masks = (masks > 0)
    masks = tf.cast(masks, tf.uint8)
    masks = tf.squeeze(masks)
    return masks

def read_one_image(image_id):
    return read_image(image_id), read_masks(image_id)

dataset = dataset.map(read_one_image, num_parallel_calls=4)
dataset = dataset.batch(4)
dataset = dataset.prefetch(8)
dataset = dataset.repeat(100)

x, y = dataset.make_one_shot_iterator().get_next()

logits = model.build_graph(x)
prob=tf.nn.sigmoid(logits)

cross_entropy = tf.losses.sigmoid_cross_entropy(multi_class_labels=y,
                                                logits=logits,
                                                weights = 1)
loss = tf.reduce_mean(cross_entropy)

train_step = tf.train.AdamOptimizer(1e-4).minimize(loss)



print('Saving graph to: %s' % graph_location)
train_writer = tf.summary.FileWriter(graph_location)
train_writer.add_graph(tf.get_default_graph())

vars = tf.trainable_variables()
print(vars)

sess = tf.Session()
sess.run(tf.global_variables_initializer())

# for i in range(300):
#     ret,_ = sess.run([loss,train_step])
#     print(i, ret)

