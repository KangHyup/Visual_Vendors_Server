import torch
import torchvision.transforms as transforms
from utils.transforms import transform_logits
import numpy as np
import cv2
from utils.transforms import get_affine_transform
import argparse
from ultralytics import YOLO
from tqdm import tqdm
import networks
import warnings

# FutureWarning 제거
warnings.filterwarnings("ignore", category=FutureWarning)


def get_arguments():
    """Parse all the arguments provided from the CLI."""
    parser = argparse.ArgumentParser(description="Yolo + Human Parsing in video")
    parser.add_argument("--parts", type=str, nargs='+', default=[], choices=['Head', 'Torso', 'Upper_Arms', 'Lower_Arms', 'Upper_Legs', 'Lower_Legs'])
    parser.add_argument("--weights", type=str, default='', help="Pre-trained model weights")
    parser.add_argument("--rate", type=int, default=5, help="Set the degree of mosaic.")
    parser.add_argument("--input-video", type=str, default='', help="Path of input video.")
    parser.add_argument("--output-video", type=str, default='', help="Path of output video.")
    return parser.parse_args()


def initialize_model(weights, device):
    """Initialize the human parsing model with weights."""
    num_classes = 7
    model = networks.init_model('resnet101', num_classes=num_classes, pretrained=None)
    state_dict = torch.load(weights, map_location=device)['state_dict']

    # Update state dict
    from collections import OrderedDict
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = k[7:]  # Remove `module.`
        new_state_dict[name] = v
    model.load_state_dict(new_state_dict)
    model.to(device)
    model.eval()
    return model


def human_parsing(frame, model, rate, parts, device, input_size=(512, 512)):
    """Perform human parsing on the given frame."""
    label = ['Background', 'Head', 'Torso', 'Upper_Arms', 'Lower_Arms', 'Upper_Legs', 'Lower_Legs']

    # Preprocess the frame
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.406, 0.456, 0.485], std=[0.225, 0.224, 0.229])
    ])
    frame_tensor = transform(frame).unsqueeze(0).to(device)

    # Run model inference
    with torch.no_grad():
        output = model(frame_tensor)
        selected_output = output[0][-1]  # Adjust as per your model's structure

        # Upsample to input size
        upsample = torch.nn.Upsample(size=input_size, mode='bilinear', align_corners=True)
        upsample_output = upsample(selected_output).squeeze().permute(1, 2, 0).cpu().numpy()

    # Create parsing result
    parsing_result = np.argmax(upsample_output, axis=2)

    # Adjust parsing result size to match original frame
    parsing_result = cv2.resize(parsing_result, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)

    # Blur processing
    rate = max(rate, 1)
    h, w, _ = frame.shape
    small_frame = cv2.resize(frame, (w // rate, h // rate), interpolation=cv2.INTER_AREA)
    blur_frame = cv2.resize(small_frame, (w, h), interpolation=cv2.INTER_NEAREST)

    for i in range(h):
        for j in range(w):
            if parsing_result[i, j] in [label.index(part) for part in parts]:
                continue
            blur_frame[i, j] = frame[i, j]

    return blur_frame


def main(args=None, progress_callback=None):
    if args is None:  # args가 명시적으로 전달되지 않으면 CLI로부터 가져오기
        args = get_arguments()
    cap = cv2.VideoCapture(args.input_video)

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Set up video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output_video, fourcc, fps, (width, height))

    # Initialize models
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    yolo_model = YOLO('yolov8n.pt')  # Adjust path if needed
    yolo_model.to(device)
    parsing_model = initialize_model(args.weights, device)

    # Process video frames
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for frame_index in tqdm(range(frame_count), desc="Processing frames"):
        ret, frame = cap.read()
        if not ret:
            break

        # Detect humans using YOLO
        results = yolo_model(frame)
        nms_human = sum(results[0].boxes.cls == 0)

        if nms_human > 0:
            for bbox in results[0].boxes:
                if bbox.cls.item() == 0:
                    start_point = (int(bbox.xyxy[0][0].item()), int(bbox.xyxy[0][1].item()))
                    end_point = (int(bbox.xyxy[0][2].item()), int(bbox.xyxy[0][3].item()))

                    # Perform human parsing and blur
                    cropped_frame = frame[start_point[1]:end_point[1], start_point[0]:end_point[0]]
                    if cropped_frame.size > 0:
                        blur_frame = human_parsing(cropped_frame, parsing_model, args.rate, args.parts, device)
                        frame[start_point[1]:end_point[1], start_point[0]:end_point[0]] = blur_frame

        out.write(frame)

        # Update progress
        if progress_callback:
            progress_callback({"current_frame": frame_index + 1, "total_frames": frame_count})

    cap.release()
    out.release()

if __name__ == '__main__':
    main()
