import time

import numpy as np
import tensorflow as tf

import awesome_gans.image_utils as iu
import awesome_gans.segan.segan_model as segan
from awesome_gans.datasets import MNISTDataSet

results = {'output': './gen_img/', 'checkpoint': './model/checkpoint', 'model': './model/SEGAN-model.ckpt'}

train_step = {
    'global_step': 150001,
    'logging_interval': 1500,
}


def main():
    start_time = time.time()  # Clocking start

    # UrbanSound8K Dataset load
    mnist = MNISTDataSet().data

    # GPU configure
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True

    with tf.Session(config=config) as s:
        # CoGAN Model
        model = segan.SEGAN(s)

        # Initializing
        s.run(tf.global_variables_initializer())

        sample_x, _ = mnist.test.next_batch(model.sample_num)
        sample_y = np.zeros(shape=[model.sample_num, model.n_classes])
        for i in range(10):
            sample_y[10 * i : 10 * (i + 1), i] = 1

        for step in range(train_step['global_step']):
            batch_x, batch_y = mnist.train.next_batch(model.batch_size)
            batch_x = np.reshape(batch_x, model.image_shape)
            batch_z = np.random.uniform(-1.0, 1.0, [model.batch_size, model.z_dim]).astype(np.float32)

            # Update D network
            _, d_loss = s.run(
                [model.d_op, model.d_loss],
                feed_dict={
                    model.x_1: batch_x,
                    model.x_2: batch_x,
                    # model.y: batch_y,
                    model.z: batch_z,
                },
            )

            # Update G network
            _, g_loss = s.run(
                [model.g_op, model.g_loss],
                feed_dict={
                    model.x_1: batch_x,
                    model.x_2: batch_x,
                    # model.y: batch_y,
                    model.z: batch_z,
                },
            )

            if step % train_step['logging_interval'] == 0:
                batch_x, batch_y = mnist.train.next_batch(model.batch_size)
                batch_x = np.reshape(batch_x, model.image_shape)
                batch_z = np.random.uniform(-1.0, 1.0, [model.batch_size, model.z_dim]).astype(np.float32)

                d_loss, g_loss, summary = s.run(
                    [model.d_loss, model.g_loss, model.merged],
                    feed_dict={
                        model.x_1: batch_x,
                        model.x_2: batch_x,
                        # model.y: batch_y,
                        model.z: batch_z,
                    },
                )

                # Print loss
                print("[+] Step %08d => " % step, " D loss : {:.8f}".format(d_loss), " G loss : {:.8f}".format(g_loss))

                sample_z = np.random.uniform(-1.0, 1.0, [model.sample_num, model.z_dim]).astype(np.float32)

                # Training G model with sample image and noise
                samples_1 = s.run(
                    model.g_sample_1,
                    feed_dict={
                        # model.y: sample_y,
                        model.z: sample_z,
                    },
                )

                samples_2 = s.run(
                    model.g_sample_2,
                    feed_dict={
                        # model.y: sample_y,
                        model.z: sample_z,
                    },
                )

                samples_1 = np.reshape(samples_1, [-1] + model.image_shape[1:])
                samples_2 = np.reshape(samples_2, [-1] + model.image_shape[1:])

                # Summary saver
                model.writer.add_summary(summary, global_step=step)

                # Export image generated by model G
                sample_image_height = model.sample_size
                sample_image_width = model.sample_size

                sample_dir_1 = results['output'] + 'train_1_{:08d}.png'.format(step)
                sample_dir_2 = results['output'] + 'train_2_{:08d}.png'.format(step)

                # Generated image save
                iu.save_images(samples_1, size=[sample_image_height, sample_image_width], image_path=sample_dir_1)
                iu.save_images(samples_2, size=[sample_image_height, sample_image_width], image_path=sample_dir_2)

                # Model save
                model.saver.save(s, results['model'], global_step=step)

    end_time = time.time() - start_time  # Clocking end

    # Elapsed time
    print("[+] Elapsed time {:.8f}s".format(end_time))

    # Close tf.Session
    s.close()


if __name__ == '__main__':
    main()
