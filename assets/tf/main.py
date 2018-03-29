import numpy as np
import tensorflow as tf

import imageio

IMAGE_SIZE = 512
graph_location = "logs"
x = tf.placeholder(tf.float32, [None, IMAGE_SIZE, IMAGE_SIZE, 3], name="input_features")
y = tf.placeholder(tf.float32, [None, IMAGE_SIZE, IMAGE_SIZE], name="input_label")

def build_graph(input_layer):
    #512
    x = input_layer
    x = tf.layers.conv2d(inputs=x, filters=64, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)
    d512 = x = tf.layers.conv2d(inputs=x, filters=64, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)

    #256
    x = tf.layers.max_pooling2d(inputs=x, pool_size=[2, 2], strides=2)
    x = tf.layers.conv2d(inputs=x, filters=128, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)
    d256 = x = tf.layers.conv2d(inputs=x, filters=128, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)

    #128
    x = tf.layers.max_pooling2d(inputs=x, pool_size=[2, 2], strides=2)
    x = tf.layers.conv2d(inputs=x, filters=256, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)
    d128 = x = tf.layers.conv2d(inputs=x, filters=256, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)

    #64
    x = tf.layers.max_pooling2d(inputs=x, pool_size=[2, 2], strides=2)
    x = tf.layers.conv2d(inputs=x, filters=512, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)
    d64 = x = tf.layers.conv2d(inputs=x, filters=512, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)

    #32
    x = tf.layers.max_pooling2d(inputs=x, pool_size=[2, 2], strides=2)
    x = tf.layers.conv2d(inputs=x, filters=1024, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)
    d32 = x = tf.layers.conv2d(inputs=x, filters=1024, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)

    #64
    x = tf.layers.conv2d_transpose(inputs=x, filters=512, kernel_size=[2, 2], strides=2, padding="same", activation=tf.nn.relu)
    x = tf.concat([d64, x], axis=-1)
    x = tf.layers.conv2d(inputs=x, filters=512, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)
    x = tf.layers.conv2d(inputs=x, filters=512, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)


    x = tf.layers.conv2d_transpose(inputs=x, filters=256, kernel_size=[2, 2], strides=2, padding="same", activation=tf.nn.relu)
    x = tf.concat([d128, x], axis=-1)
    x = tf.layers.conv2d(inputs=x, filters=256, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)
    x = tf.layers.conv2d(inputs=x, filters=256, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)

    x = tf.layers.conv2d_transpose(inputs=x, filters=128, kernel_size=[2, 2], strides=2, padding="same", activation=tf.nn.relu)
    x = tf.concat([d256, x], axis=-1)
    x = tf.layers.conv2d(inputs=x, filters=128, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)
    x = tf.layers.conv2d(inputs=x, filters=128, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)

    x = tf.layers.conv2d_transpose(inputs=x, filters=64, kernel_size=[2, 2], strides=2, padding="same", activation=tf.nn.relu)
    x = tf.concat([d512, x], axis=-1)
    x = tf.layers.conv2d(inputs=x, filters=64, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)
    x = tf.layers.conv2d(inputs=x, filters=64, kernel_size=[3, 3], strides=1, padding="same", activation=tf.nn.relu)

    logits = tf.layers.conv2d(inputs=x, filters=2, kernel_size=[1, 1], strides=1, padding="same", activation=None)
    #x = tf.sigmoid(x)
    return logits

logits = build_graph(x)

with tf.name_scope('loss'):
    labels = tf.stack([y, 1-y], axis=-1)
    cross_entropy = tf.nn.softmax_cross_entropy_with_logits_v2(labels=labels,
                                                            logits=logits)
loss = tf.reduce_mean(cross_entropy)

train_step = tf.train.AdamOptimizer(1e-4).minimize(loss)

print('Saving graph to: %s' % graph_location)
train_writer = tf.summary.FileWriter(graph_location)
train_writer.add_graph(tf.get_default_graph())

vars = tf.trainable_variables()
print(vars)




import data

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    for i in range(100):
        batch_x, batch_y = data.get_one_batch()
        train_step.run(feed_dict={x: batch_x, y: batch_y})

        ret = sess.run(loss, feed_dict={x: batch_x, y: batch_y})

        print(ret)