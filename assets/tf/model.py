

import tensorflow as tf

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

    logits = tf.layers.conv2d(inputs=x, filters=1, kernel_size=[1, 1], strides=1, padding="same", activation=None)

    logits = tf.squeeze(logits)
    #x = tf.sigmoid(x)
    return logits
