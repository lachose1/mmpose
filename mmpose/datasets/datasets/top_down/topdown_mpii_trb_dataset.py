import copy as cp
import os
import os.path as osp
from collections import OrderedDict, defaultdict

import json_tricks as json
import numpy as np

from mmpose.datasets.builder import DATASETS
from .topdown_base_dataset import TopDownBaseDataset


@DATASETS.register_module()
class TopDownMpiiTrbDataset(TopDownBaseDataset):
    """MPII-TRB Dataset dataset for top-down pose estimation.

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

        # flip_pairs in MPII-TRB
        self.ann_info['flip_pairs'] = [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9],
                                       [10, 11], [14, 15]]
        for i in range(6):
            self.ann_info['flip_pairs'].append([16 + i, 22 + i])
            self.ann_info['flip_pairs'].append([28 + i, 34 + i])

        self.ann_info['upper_body_ids'] = [0, 1, 2, 3, 4, 5, 12, 13]
        self.ann_info['lower_body_ids'] = [6, 7, 8, 9, 10, 11]
        self.ann_info['upper_body_ids'].extend(list(range(14, 28)))
        self.ann_info['lower_body_ids'].extend(list(range(28, 40)))

        self.ann_info['use_different_joints_weight'] = False
        self.ann_info['joints_weight'] =  \
            np.ones(40, dtype=np.float32).reshape(
                (self.ann_info['num_joints'], 1))

        self.db = self._get_db(ann_file)
        self.image_set = set([x['image_file'] for x in self.db])
        self.num_images = len(self.image_set)

        print('=> num_images: {}'.format(self.num_images))
        print('=> load {} samples'.format(len(self.db)))

    def _get_db(self, ann_file):
        """Load dataset."""
        with open(ann_file, 'r') as f:
            data = json.load(f)
        tmpl = dict(
            image_file=None,
            center=None,
            scale=None,
            rotation=0,
            joints_3d=None,
            joints_3d_visible=None,
            dataset='mpii_trb')

        imid2info = {
            int(osp.splitext(x['file_name'])[0]): x
            for x in data['images']
        }

        num_joints = self.ann_info['num_joints']
        gt_db = []

        for anno in data['annotations']:
            newitem = cp.deepcopy(tmpl)
            image_id = anno['image_id']
            newitem['image_file'] = os.path.join(
                self.img_prefix, imid2info[image_id]['file_name'])

            if max(anno['keypoints']) == 0:
                continue

            joints_3d = np.zeros((num_joints, 3), dtype=np.float)
            joints_3d_visible = np.zeros((num_joints, 3), dtype=np.float)

            for ipt in range(num_joints):
                joints_3d[ipt, 0] = anno['keypoints'][ipt * 3 + 0]
                joints_3d[ipt, 1] = anno['keypoints'][ipt * 3 + 1]
                joints_3d[ipt, 2] = 0
                t_vis = anno['keypoints'][ipt * 3 + 2]
                if t_vis > 1:
                    t_vis = 1
                joints_3d_visible[ipt, 0] = t_vis
                joints_3d_visible[ipt, 1] = t_vis
                joints_3d_visible[ipt, 2] = 0

            center = np.array(anno['center'], dtype=np.float32)
            scale = self.ann_info['image_size'] / anno['scale'] / 200.0
            newitem['center'] = center
            newitem['scale'] = scale
            newitem['joints_3d'] = joints_3d
            newitem['joints_3d_visible'] = joints_3d_visible
            if 'headbox' in anno:
                newitem['headbox'] = anno['headbox']
            gt_db.append(newitem)

        return gt_db

    def evaluate_kernal(self, pred, joints_3d, joints_3d_visible, headbox):
        """Evaluate one example."""
        num_joints = self.ann_info['num_joints']
        headbox = np.array(headbox)
        threshold = np.linalg.norm(headbox[:2] - headbox[2:]) * 0.3
        hit = np.zeros(num_joints, dtype=np.float32)
        exist = np.zeros(num_joints, dtype=np.float32)

        for i in range(num_joints):
            pred_pt = pred[i]
            gt_pt = joints_3d[i]
            vis = joints_3d_visible[i][0]
            if vis:
                exist[i] = 1
            else:
                continue
            distance = np.linalg.norm(pred_pt[:2] - gt_pt[:2])
            if distance < threshold:
                hit[i] = 1
        return hit, exist

    def evaluate(self, outputs, res_folder, metrics='PCKh', **kwargs):
        """Evaluate PCKh for MPII-TRB dataset.

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
        """Evaluate MPII-TRB keypoint results."""
        res_file = os.path.join(res_folder, 'result_keypoints.json')

        kpts = defaultdict(list)
        for preds, boxes, image_path in outputs:
            str_image_path = ''.join(image_path)
            image_id = int(osp.basename(osp.splitext(str_image_path)[0]))

            kpts[image_id].append({
                'keypoints':
                list(preds[0].astype(np.float32)),
                'center':
                list(boxes[0][0:2].astype(np.float32)),
                'scale':
                list(boxes[0][2:4].astype(np.float32)),
                'area':
                boxes[0][4],
                'score':
                boxes[0][5],
                'image_id':
                image_id,
            })

        self._write_keypoint_results(kpts, res_file)
        info_str = self._report_metric(res_file)
        name_value = OrderedDict(info_str)

        return name_value

    def _write_keypoint_results(self, keypoints, res_file):
        """Write results into a json file."""

        with open(res_file, 'w') as f:
            json.dump(keypoints, f, sort_keys=True, indent=4)

    def _report_metric(self, res_file):
        """Keypoint evaluation.

        Report Mean Acc of skeleton, contour and all joints.
        """
        num_joints = self.ann_info['num_joints']
        hit = np.zeros(num_joints)
        exist = np.zeros(num_joints)

        with open(res_file, 'r') as fin:
            preds = json.load(fin)

        assert len(preds) == len(
            self.db), f'LEN(PREDS)={len(preds)}, LEN(DB)={len(self.db)}'
        for pred, item in zip(preds, self.db):
            h, e = self.evaluate_kernal(pred['keypoints'], item['joints_3d'],
                                        item['joints_3d_visible'],
                                        item['headbox'])
            hit += h
            exist += e
        skeleton = np.sum(hit[:14]) / np.sum(exist[:14])
        contour = np.sum(hit[14:]) / np.sum(exist[14:])
        p_all = np.sum(hit) / np.sum(exist)

        info_str = []
        info_str.append(('kp_acc', skeleton))
        info_str.append(('cp_acc', contour))
        info_str.append(('p_acc', p_all))
        return info_str
