import json
import os
from collections import OrderedDict

import numpy as np
from scipy.io import loadmat, savemat

from ...registry import DATASETS
from .topdown_base_dataset import TopDownBaseDataset


@DATASETS.register_module()
class TopDownMpiiDataset(TopDownBaseDataset):
    """MPII Dataset for top-down pose estimation.

    The dataset loads raw features and apply specified transforms
    to return a dict containing the image tensors and other information.

    Args:
        ann_file (str): Path to the annotation file.
        img_prefix (str): Path to a directory where images are held.
            Default: None.
        data_cfg (dict): config
        pipeline (list[dict | callable]): A sequence of data transforms.
        test_mode (bool): Store True when building test or
            validation dataset. Default: False.
    """

    def __init__(self,
                 ann_file,
                 img_prefix,
                 data_cfg,
                 pipeline,
                 test_mode=False):
        super().__init__(
            ann_file, img_prefix, data_cfg, pipeline, test_mode=test_mode)

        self.ann_file = ann_file
        self.ann_info['flip_pairs'] = [[0, 5], [1, 4], [2, 3], [10, 15],
                                       [11, 14], [12, 13]]
        self.ann_info['upper_body_ids'] = (7, 8, 9, 10, 11, 12, 13, 14, 15)
        self.ann_info['lower_body_ids'] = (0, 1, 2, 3, 4, 5, 6)

        self.ann_info['use_different_joints_weight'] = False
        self.ann_info['joints_weight'] = np.ones(
            (self.ann_info['num_joints'], 1))

        self.db = self._get_db()

    def _get_db(self):
        # create train/val split
        with open(self.ann_file) as anno_file:
            anno = json.load(anno_file)

        gt_db = []
        for a in anno:
            image_name = a['image']

            center = np.array(a['center'], dtype=np.float)
            scale = np.array([a['scale'], a['scale']], dtype=np.float)

            # Adjust center/scale slightly to avoid cropping limbs
            if center[0] != -1:
                center[1] = center[1] + 15 * scale[1]
                scale = scale * 1.25

            # MPII uses matlab format, index is 1-based,
            # we should first convert to 0-based index
            center = center - 1

            joints_3d = np.zeros((self.ann_info['num_joints'], 3),
                                 dtype=np.float)
            joints_3d_visible = np.zeros((self.ann_info['num_joints'], 3),
                                         dtype=np.float)
            if not self.test_mode:
                joints = np.array(a['joints'])
                joints[:, 0:2] = joints[:, 0:2] - 1
                joints_vis = np.array(a['joints_vis'])
                assert len(joints) == self.ann_info['num_joints'], \
                    f'joint num diff: {len(joints)}' + \
                    f' vs {self.ann_info["num_joints"]}'

                joints_3d[:, 0:2] = joints[:, 0:2]
                joints_3d_visible[:, 0] = joints_vis[:]
                joints_3d_visible[:, 1] = joints_vis[:]

            gt_db.append({
                'image_file':
                os.path.join(self.img_prefix, image_name),
                'center':
                center,
                'scale':
                scale,
                'rotation':
                0,
                'joints_3d':
                joints_3d,
                'joints_3d_visible':
                joints_3d_visible,
                'dataset':
                'mpii',
                'bbox_score':
                1
            })

        return gt_db

    def evaluate(self, outputs, res_folder, metrics='PCKh', **kwargs):
        """Evaluate PCKh for MPII dataset. Adapted from
        https://github.com/leoxiaobin/deep-high-resolution- net.pytorch
        Original licence: Copyright (c) Microsoft, under the MIT License.

        Note:
            num_keypoints: K

        Args:
            outputs(list(preds, boxes, image_path)):Output results.
                preds(np.ndarray[1,K,3]): The first two dimensions are
                    coordinates, score is the third dimension of the array.
                boxes(np.ndarray[1,6]): [center[0], center[1], scale[0]
                    , scale[1],area, score]
                image_path(list[str]): For example, ['0', '0',
                    '0', '0', '0', '1', '1', '6', '3', '.', 'j', 'p', 'g']
            res_folder(str): Path of directory to save the results.
            metrics(str): Metrics to be performed.
                Defaults: 'PCKh'.

        Returns:
            PCKh for each joint
        """

        # only PCKh is supported.
        assert metrics == 'PCKh'

        _preds = []
        for i in range(len(outputs)):
            kpts, _, _ = outputs[i]
            _preds.append(kpts[0])

        preds = np.stack(_preds)

        # convert 0-based index to 1-based index
        preds = preds[:, :, 0:2] + 1.0

        if res_folder:
            pred_file = os.path.join(res_folder, 'pred.mat')
            savemat(pred_file, mdict={'preds': preds})

        SC_BIAS = 0.6
        threshold = 0.5

        gt_file = os.path.join(self.ann_file[:-11], 'mpii_gt_valid.mat')
        gt_dict = loadmat(gt_file)
        dataset_joints = gt_dict['dataset_joints']
        jnt_missing = gt_dict['jnt_missing']
        pos_gt_src = gt_dict['pos_gt_src']
        headboxes_src = gt_dict['headboxes_src']

        pos_pred_src = np.transpose(preds, [1, 2, 0])

        head = np.where(dataset_joints == 'head')[1][0]
        lsho = np.where(dataset_joints == 'lsho')[1][0]
        lelb = np.where(dataset_joints == 'lelb')[1][0]
        lwri = np.where(dataset_joints == 'lwri')[1][0]
        lhip = np.where(dataset_joints == 'lhip')[1][0]
        lkne = np.where(dataset_joints == 'lkne')[1][0]
        lank = np.where(dataset_joints == 'lank')[1][0]

        rsho = np.where(dataset_joints == 'rsho')[1][0]
        relb = np.where(dataset_joints == 'relb')[1][0]
        rwri = np.where(dataset_joints == 'rwri')[1][0]
        rkne = np.where(dataset_joints == 'rkne')[1][0]
        rank = np.where(dataset_joints == 'rank')[1][0]
        rhip = np.where(dataset_joints == 'rhip')[1][0]

        jnt_visible = 1 - jnt_missing
        uv_error = pos_pred_src - pos_gt_src
        uv_err = np.linalg.norm(uv_error, axis=1)
        headsizes = headboxes_src[1, :, :] - headboxes_src[0, :, :]
        headsizes = np.linalg.norm(headsizes, axis=0)
        headsizes *= SC_BIAS
        scale = np.multiply(headsizes, np.ones((len(uv_err), 1)))
        scaled_uv_err = np.divide(uv_err, scale)
        scaled_uv_err = np.multiply(scaled_uv_err, jnt_visible)
        jnt_count = np.sum(jnt_visible, axis=1)
        less_than_threshold = np.multiply((scaled_uv_err <= threshold),
                                          jnt_visible)
        PCKh = np.divide(100. * np.sum(less_than_threshold, axis=1), jnt_count)

        # save
        rng = np.arange(0, 0.5 + 0.01, 0.01)
        pckAll = np.zeros((len(rng), 16))

        for r in range(len(rng)):
            threshold = rng[r]
            less_than_threshold = np.multiply(scaled_uv_err <= threshold,
                                              jnt_visible)
            pckAll[r, :] = np.divide(
                100. * np.sum(less_than_threshold, axis=1), jnt_count)

        PCKh = np.ma.array(PCKh, mask=False)
        PCKh.mask[6:8] = True

        jnt_count = np.ma.array(jnt_count, mask=False)
        jnt_count.mask[6:8] = True
        jnt_ratio = jnt_count / np.sum(jnt_count).astype(np.float64)

        name_value = [('Head', PCKh[head]),
                      ('Shoulder', 0.5 * (PCKh[lsho] + PCKh[rsho])),
                      ('Elbow', 0.5 * (PCKh[lelb] + PCKh[relb])),
                      ('Wrist', 0.5 * (PCKh[lwri] + PCKh[rwri])),
                      ('Hip', 0.5 * (PCKh[lhip] + PCKh[rhip])),
                      ('Knee', 0.5 * (PCKh[lkne] + PCKh[rkne])),
                      ('Ankle', 0.5 * (PCKh[lank] + PCKh[rank])),
                      ('Mean', np.sum(PCKh * jnt_ratio)),
                      ('Mean@0.1', np.sum(pckAll[11, :] * jnt_ratio))]
        name_value = OrderedDict(name_value)

        return name_value
