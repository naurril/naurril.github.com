
import tensorflow as tf


import model
import data


IMAGE_SIZE = 512
graph_location = "logs"
x = tf.placeholder(tf.float32, [None, IMAGE_SIZE, IMAGE_SIZE, 3], name="input_features")
y = tf.placeholder(tf.float32, [None, IMAGE_SIZE, IMAGE_SIZE], name="input_label")

logits = model.build_graph(x)
prob=tf.nn.sigmoid(logits)

cross_entropy = tf.losses.sigmoid_cross_entropy(multi_class_labels=y,
                                                logits=logits,
                                                weights = 1)
loss = tf.reduce_mean(cross_entropy)
tf.summary.scalar('loss', loss)

train_step = tf.train.AdamOptimizer(1e-4).minimize(loss)



merged = tf.summary.merge_all()

print('Saving graph to: %s' % graph_location)
train_writer = tf.summary.FileWriter(graph_location)
train_writer.add_graph(tf.get_default_graph())

vars = tf.trainable_variables()
print(vars)

sess = tf.Session()
sess.run(tf.global_variables_initializer())

for i in range(100,200):
    batch_x, batch_y = data.get_one_batch()
    ret, summary, _ = sess.run([loss, merged, train_step], feed_dict={x: batch_x, y: batch_y})
    train_writer.add_summary(summary, i)
    print(i, ret)