# Getting Started

This page provides basic tutorials about the usage of MMPose.
For installation instructions, please see [install.md](install.md).

## Prepare datasets

It is recommended to symlink the dataset root to `$MMPOSE/data`.
If your folder structure is different, you may need to change the corresponding paths in config files.

**For COCO data**, please download from [COCO download](http://cocodataset.org/#download), 2017 Train/Val is needed for COCO keypoints training and validation. [HRNet-Human-Pose-Estimation](https://github.com/HRNet/HRNet-Human-Pose-Estimation) provides person detection result of COCO val2017 to reproduce our multi-person pose estimation results. Please download from [OneDrive](https://1drv.ms/f/s!AhIXJn_J-blWzzDXoz5BeFl8sWM-)
Download and extract them under $MMPOSE/data, and make them look like this:

```
mmpose
├── mmpose
├── docs
├── tests
├── tools
├── configs
`── data
    │── coco
        │-- annotations
        │   │-- person_keypoints_train2017.json
        │   |-- person_keypoints_val2017.json
        |-- person_detection_results
        |   |-- COCO_val2017_detections_AP_H_56_person.json
        │-- train2017
        │   │-- 000000000009.jpg
        │   │-- 000000000025.jpg
        │   │-- 000000000030.jpg
        │   │-- ...
        `-- val2017
            │-- 000000000139.jpg
            │-- 000000000285.jpg
            │-- 000000000632.jpg
            │-- ...

```

**For MPII data**, please download from [MPII Human Pose Dataset](http://human-pose.mpi-inf.mpg.de/).
We have converted the original annotation files into json format, please download them from [mpii_annotations](https://openmmlab.oss-cn-hangzhou.aliyuncs.com/mmpose/datasets/mpii_annotations.tar).
Extract them under {MMPose}/data, and make them look like this:

```
mmpose
├── mmpose
├── docs
├── tests
├── tools
├── configs
`── data
    │── mpii
        |── annotations
        |   |── mpii_gt_valid.mat
        |   |── mpii_test.json
        |   |── mpii_train.json
        |   |── mpii_trainval.json
        |   `── mpii_valid.json
        `── images
            |── 000001163.jpg
            |── 000003072.jpg

```


**For MPII-TRB data**, please download from [MPII Human Pose Dataset](http://human-pose.mpi-inf.mpg.de/).
Please download the annotation files from [mpii_trb_annotations](https://openmmlab.oss-cn-hangzhou.aliyuncs.com/mmpose/datasets/mpii_trb_annotations.tar).
Extract them under {MMPose}/data, and make them look like this:

```
mmpose
├── mmpose
├── docs
├── tests
├── tools
├── configs
`── data
    │── mpii
        |── annotations
        |   |── mpii_trb_train.json
        |   |── mpii_trb_val.json
        `── images
            |── 000001163.jpg
            |── 000003072.jpg

```

For using custom datasets, please refer to [Tutorial 2: Adding New Dataset](tutorials/new_dataset.md)

## Prepare Pretrained Models
Download imagenet pretrained models from our [model zoo](model_zoo.md)

```
mmpose
`-- models
    `-- pytorch
         `-- imagenet
            |-- hrnet_w32-36af842e.pth
            |-- hrnet_w48-8ef0771d.pth
            |-- resnet50-19c8e357.pth
            |-- resnet101-5d3b4d8f.pth
            |-- resnet152-b121ed2d.pth
            |-- ...


```
## Inference with pretrained models

We provide testing scripts to evaluate a whole dataset (COCO, etc.),
and provide some high-level apis for easier integration to other projects.

### Test a dataset

- [x] single GPU
- [x] single node multiple GPUs
- [x] multiple node

You can use the following commands to test a dataset.

```shell
# single-gpu testing
python tools/test.py ${CONFIG_FILE} ${CHECKPOINT_FILE} [--out ${RESULT_FILE}] [--eval ${EVAL_METRIC}] \
    [--proc_per_gpu ${NUM_PROC_PER_GPU}] [--gpu_collect] [--tmpdir ${TMPDIR}] [--average_clips ${AVG_TYPE}] \
    [--launcher ${JOB_LAUNCHER}] [--local_rank ${LOCAL_RANK}]

python tools/test.py ${CONFIG_FILE} ${CHECKPOINT_FILE} ${GPU_NUM} [--out ${RESULT_FILE}] [--eval ${EVAL_METRIC}] \
    [--proc_per_gpu ${NUM_PROC_PER_GPU}] [--gpu_collect] [--tmpdir ${TMPDIR}] [--average_clips ${AVG_TYPE}] \
    [--launcher ${JOB_LAUNCHER}] [--local_rank ${LOCAL_RANK}]
```

Optional arguments:
- `RESULT_FILE`: Filename of the output results. If not specified, the results will not be saved to a file.
- `EVAL_METRIC`: Items to be evaluated on the results. Allowed values depend on the dataset.
- `NUM_PROC_PER_GPU`: Number of processes per GPU. If not specified, only one process will be assigned for a single gpu.
- `--gpu_collect`: If specified, recognition results will be collected using gpu communication. Otherwise, it will save the results on different gpus to `TMPDIR` and collect them by the rank 0 worker.
- `TMPDIR`: Temporary directory used for collecting results from multiple workers, available when `--gpu_collect` is not specified.
- `AVG_TYPE`: Items to average the test clips. If set to `prob`, it will apply softmax before averaging the clip scores. Otherwise, it will directly average the clip scores.
- `JOB_LAUNCHER`: Items for distributed job initialization launcher. Allowed choices are `none`, `pytorch`, `slurm`, `mpi`. Especially, if set to none, it will test in a non-distributed mode.
- `LOCAL_RANK`: ID for local rank. If not specified, it will be set to 0.

Examples:

Assume that you have already downloaded the checkpoints to the directory `checkpoints/`.

1. Test ResNet50 on COCO (without saving the test results) and evaluate the mAP.

    ```shell
    ./tools/dist_test.sh configs/top_down/resnet/coco/res50_coco_256x192.py \
        checkpoints/SOME_CHECKPOINT.pth 1 \
        --eval mAP
    ```

2. Test ResNet50 on COCO  with 8 GPUS, and evaluate the mAP.

    ```shell
    ./tools/dist_test.sh configs/top_down/resnet/coco/res50_coco_256x192.py \
        checkpoints/SOME_CHECKPOINT.pth 8 \
        --eval mAP
    ```

2. Test ResNet50 on COCO in slurm environment and evaluate the mAP.

    ```shell
    ./tools/slurm_test.sh slurm_partition test_job \
        configs/top_down/resnet/coco/res50_coco_256x192.py \
        checkpoints/SOME_CHECKPOINT.pth \
        --eval mAP
    ```



### Top-down Image demo

#### Using gt human bounding boxes as input

We provide a demo script to test a single image, given gt json file.

```shell
python demo/top_down_img_demo.py \
    ${MMPOSE_CONFIG_FILE} ${MMPOSE_CHECKPOINT_FILE} \
    --img-root ${IMG_ROOT} --json-file ${JSON_FILE} \
    --out-img-root ${OUTPUT_DIR} \
    [--show --device ${GPU_ID}] \
    [--kpt-thr ${KPT_SCORE_THR}]
```

Examples:

```shell
python demo/top_down_img_demo.py \
    configs/top_down/hrnet/coco/hrnet_w48_coco_256x192.py \
    hrnet_w48_coco_256x192/epoch_210.pth \
    --img-root tests/data/coco/ --json-file tests/data/coco/test_coco.json \
    --out-img-root vis_results
```

#### Using mmdet for human bounding box detection

Assume that you have already installed [mmdet](https://github.com/open-mmlab/mmdetection).

We provide a demo script to run mmdet for human detection, and mmpose for pose estimation.

```shell
python demo/top_down_img_demo_with_mmdet.py \
    ${MMDET_CONFIG_FILE} ${MMDET_CHECKPOINT_FILE} \
    ${MMPOSE_CONFIG_FILE} ${MMPOSE_CHECKPOINT_FILE} \
    --img-root ${IMG_ROOT} --img ${IMG_FILE} \
    --out-img-root ${OUTPUT_DIR} \
    [--show --device ${GPU_ID}] \
    [--bbox-thr ${BBOX_SCORE_THR} --kpt-thr ${KPT_SCORE_THR}]
```

Examples:

```shell
python demo/top_down_img_demo_with_mmdet.py mmdetection/configs/faster_rcnn/faster_rcnn_r50_fpn_1x_coco.py \
    mmdetection/checkpoints/faster_rcnn_r50_fpn_1x_coco_20200130-047c8118.pth \
    configs/top_down/hrnet/coco/hrnet_w48_coco_256x192.py \
    hrnet_w48_coco_256x192/epoch_210.pth \
    --img-root tests/data/coco/ \
    --img 000000196141.jpg \
    --out-img-root vis_results
```

### Top-down Video demo

We also provide a video demo to illustrate the results.

Assume that you have already installed [mmdet](https://github.com/open-mmlab/mmdetection).

```shell
python demo/top_down_video_demo_with_mmdet.py \
    ${MMDET_CONFIG_FILE} ${MMDET_CHECKPOINT_FILE} \
    ${MMPOSE_CONFIG_FILE} ${MMPOSE_CHECKPOINT_FILE} \
    --video-path ${VIDEO_FILE} \
    --output-video-root ${OUTPUT_VIDEO_ROOT} \
    [--show --device ${GPU_ID}] \
    [--bbox-thr ${BBOX_SCORE_THR} --kpt-thr ${KPT_SCORE_THR}]
```

Examples:

```shell
python demo/top_down_video_demo_with_mmdet.py mmdetection/configs/faster_rcnn/faster_rcnn_r50_fpn_1x_coco.py \
    mmdetection/checkpoints/faster_rcnn_r50_fpn_1x_coco_20200130-047c8118.pth \
    configs/top_down/hrnet/coco/hrnet_w48_coco_256x192.py \
    hrnet_w48_coco_256x192/epoch_210.pth \
    --video_path demo/demo_video.mp4 \
    --output-video-root vis_results
```

## Train a model

MMPose implements distributed training and non-distributed training,
which uses `MMDistributedDataParallel` and `MMDataParallel` respectively.

All outputs (log files and checkpoints) will be saved to the working directory,
which is specified by `work_dir` in the config file.

By default we evaluate the model on the validation set after each epoch, you can change the evaluation interval by modifying the interval argument in the training config
```python
evaluation = dict(interval=5)  # This evaluate the model per 5 epoch.
```

According to the [Linear Scaling Rule](https://arxiv.org/abs/1706.02677), you need to set the learning rate proportional to the batch size if you use different GPUs or videos per GPU, e.g., lr=0.01 for 4 GPUs * 2 video/gpu and lr=0.08 for 16 GPUs * 4 video/gpu.

### Train with a single GPU

```shell
python tools/train.py ${CONFIG_FILE} [optional arguments]
```

If you want to specify the working directory in the command, you can add an argument `--work_dir ${YOUR_WORK_DIR}`.

### Train with multiple GPUs

```shell
./tools/dist_train.sh ${CONFIG_FILE} ${GPU_NUM} [optional arguments]
```

Optional arguments are:

- `--validate` (**strongly recommended**): Perform evaluation at every k (default value is 5 epochs during the training.
- `--work-dir ${WORK_DIR}`: Override the working directory specified in the config file.
- `--resume-from ${CHECKPOINT_FILE}`: Resume from a previous checkpoint file.
- `--gpus ${GPU_NUM}`: Number of gpus to use, which is only applicable to non-distributed training.
- `--seed ${SEED}`: Seed id for random state in python, numpy and pytorch to generate random numbers.
- `--deterministic`: If specified, it will set deterministic options for CUDNN backend.
- `JOB_LAUNCHER`: Items for distributed job initialization launcher. Allowed choices are `none`, `pytorch`, `slurm`, `mpi`. Especially, if set to none, it will test in a non-distributed mode.
- `LOCAL_RANK`: ID for local rank. If not specified, it will be set to 0.
- `--autoscale-lr`: If specified, it will automatically scale lr with the number of gpus by [Linear Scaling Rule](https://arxiv.org/abs/1706.02677).

Difference between `resume-from` and `load-from`:
`resume-from` loads both the model weights and optimizer status, and the epoch is also inherited from the specified checkpoint. It is usually used for resuming the training process that is interrupted accidentally.
`load-from` only loads the model weights and the training epoch starts from 0. It is usually used for finetuning.

Here is an example of using 8 GPUs to load ResNet50 checkpoint.

```shell
./tools/dist_train.sh configs/top_down/resnet/coco/res50_coco_256x192.py 8 --resume_from work_dirs/res50_coco_256x192/latest.pth
```

### Train with multiple machines

If you can run MMPose on a cluster managed with [slurm](https://slurm.schedmd.com/), you can use the script `slurm_train.sh`. (This script also supports single machine training.)

```shell
./tools/slurm_train.sh ${PARTITION} ${JOB_NAME} ${CONFIG_FILE} ${WORK_DIR} [${GPUS}]
```

Here is an example of using 16 GPUs to train ResNet50 on the dev partition in a slurm cluster.
(Use `GPUS_PER_NODE=8` to specify a single slurm cluster node with 8 GPUs, `CPUS_PER_TASK=2` to use 2 cpus per task.
Assume that `Test` is a valid ${PARTITION} name.)

```shell
GPUS_PER_NODE=8 CPUS_PER_TASK=2 ./tools/slurm_train.sh Test res50 configs/top_down/resnet/coco/res50_coco_256x192.py work_dirs/res50_coco_256x192 16
```

You can check [slurm_train.sh](../tools/slurm_train.sh) for full arguments and environment variables.

If you have just multiple machines connected with ethernet, you can refer to
pytorch [launch utility](https://pytorch.org/docs/stable/distributed_deprecated.html#launch-utility).
Usually it is slow if you do not have high speed networking like infiniband.

### Launch multiple jobs on a single machine

If you launch multiple jobs on a single machine, e.g., 2 jobs of 4-GPU training on a machine with 8 GPUs,
you need to specify different ports (29500 by default) for each job to avoid communication conflict.

If you use `dist_train.sh` to launch training jobs, you can set the port in commands.

```shell
CUDA_VISIBLE_DEVICES=0,1,2,3 PORT=29500 ./tools/dist_train.sh ${CONFIG_FILE} 4
CUDA_VISIBLE_DEVICES=4,5,6,7 PORT=29501 ./tools/dist_train.sh ${CONFIG_FILE} 4
```

If you use launch training jobs with slurm, you need to modify the config files (usually the 6th line from the bottom in config files) to set different communication ports.

In `config1.py`,
```python
dist_params = dict(backend='nccl', port=29500)
```

In `config2.py`,
```python
dist_params = dict(backend='nccl', port=29501)
```

Then you can launch two jobs with `config1.py` ang `config2.py`.

```shell
CUDA_VISIBLE_DEVICES=0,1,2,3 ./tools/slurm_train.sh ${PARTITION} ${JOB_NAME} config1.py ${WORK_DIR} 4
CUDA_VISIBLE_DEVICES=4,5,6,7 ./tools/slurm_train.sh ${PARTITION} ${JOB_NAME} config2.py ${WORK_DIR} 4
```

## Benchmark
You can get average inference speed using the following script. Note that it does not include the IO time and the pre-processing time.
```shell
python tools/benchmark_inference.py ${MMPOSE_CONFIG_FILE}
```

## Tutorials

Currently, we provide some tutorials for users to [finetune model](tutorials/finetune.md),
[add new dataset](tutorials/new_dataset.md), [add new modules](tutorials/new_modules.md).
