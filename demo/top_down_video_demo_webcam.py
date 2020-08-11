import os
from argparse import ArgumentParser

import time

import cv2
from mmdet.apis import inference_detector, init_detector

from mmpose.apis import inference_pose_model, init_pose_model, vis_pose_result

font = cv2.FONT_HERSHEY_SIMPLEX
cv2.namedWindow('Image',cv2.WINDOW_NORMAL)
def main():
    """Visualize the demo images.

    Using mmdet to detect the human.
    """
    parser = ArgumentParser()
    parser.add_argument('det_config', help='Config file for detection')
    parser.add_argument('det_checkpoint', help='Checkpoint file for detection')
    parser.add_argument('pose_config', help='Config file for pose')
    parser.add_argument('pose_checkpoint', help='Checkpoint file for pose')
    parser.add_argument('--video-path', type=str, help='Video path')
    parser.add_argument(
        '--show',
        action='store_true',
        default=False,
        help='whether to show visualizations.')
    parser.add_argument(
        '--out-video-root',
        default='',
        help='Root of the output video file. '
        'Default not saving the visualization video.')
    parser.add_argument(
        '--device', default='cuda:0', help='Device used for inference')
    parser.add_argument(
        '--bbox-thr',
        type=float,
        default=0.3,
        help='Bounding box score threshold')
    parser.add_argument(
        '--kpt-thr', type=float, default=0.3, help='Keypoint score threshold')

    args = parser.parse_args()

    skeleton = [[16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12],
                [7, 13], [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3],
                [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]]

    assert args.show or (args.out_video_root != '')
    assert 'cuda' in args.device
    assert args.det_config is not None
    assert args.det_checkpoint is not None

    det_model = init_detector(
        args.det_config, args.det_checkpoint, device=args.device)
    # build the pose model from a config file and a checkpoint file
    pose_model = init_pose_model(
        args.pose_config, args.pose_checkpoint, device=args.device)

    cap = cv2.VideoCapture(0)
	
    #cap.set(cv2.CAP_PROP_FRAME_WIDTH,320);
    #cap.set(cv2.CAP_PROP_FRAME_HEIGHT,240);

    while (cap.isOpened()):
        flag, img = cap.read()
	# Start time
        startTime = time.time()

        if not flag:
            break
        # test a single image, the resulting box is (x1, y1, x2, y2)
        det_results = inference_detector(det_model, img)
        # keep the person class bounding boxes.
        person_bboxes = det_results[0].copy()

        # test a single image, with a list of bboxes.
        pose_results = inference_pose_model(
            pose_model,
            img,
            person_bboxes,
            bbox_thr=args.bbox_thr,
            format='xyxy')

        # show the results
        vis_img = vis_pose_result(
            pose_model,
            img,
            pose_results,
            skeleton=skeleton,
            kpt_score_thr=args.kpt_thr,
            show=False)
        # Time elapsed
        endTime = time.time()

        # Time elapsed
        seconds = endTime - startTime
        fps = str("{:.2f}".format(1/seconds)) + " fps"
        if args.show:
            cv2.putText(vis_img, fps, (10,10), font, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imshow('Image', vis_img)
            cv2.resizeWindow('image', 600,600)



        #if save_out_video:
        #    videoWriter.write(vis_img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    #if save_out_video:
    #    videoWriter.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()

