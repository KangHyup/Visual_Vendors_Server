from flask import Flask, request, jsonify, Response, send_file, send_from_directory
import os
import time
import threading
import json
from flask_cors import CORS
import cv2
from Yolo_Parsing_model import get_arguments, main

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 진행 상황 관리용 글로벌 변수
progress_data = {"status": "idle", "current_frame": 0, "total_frames": 0, "output_file": None}

def run_yolo_parsing(args):
    global progress_data
    progress_data["status"] = "processing"
    progress_data["current_frame"] = 0
    progress_data["total_frames"] = args.frame_count

    try:
        for frame_number in main(args):
            progress_data["current_frame"] = frame_number
            time.sleep(0.1)  # 처리 시뮬레이션

        # 실제 처리 완료 시점에서 완료 상태 설정
        progress_data["status"] = "completed"
        app.logger.info(f"모자이크화 완료!. Output file: {progress_data['output_file']}")
    except Exception as e:
        progress_data["status"] = "error"
        progress_data["error"] = str(e)

@app.route('/process-video', methods=['POST'])
def process_video():
    global progress_data

    if 'file' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    if not request.form.get('parts') or not request.form.get('rate'):
        return jsonify({'error': 'Missing required parameters (parts or rate)'}), 400

    video_file = request.files['file']
    input_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
    video_file.save(input_path)

    parts = request.form.get('parts').split(',')
    rate = int(request.form.get('rate'))
    weights = request.form.get('weights', os.path.join(BASE_DIR, 'exp-schp-201908270938-pascal-person-part.pth'))

    if not os.path.exists(weights):
        return jsonify({'error': f"Weight file not found: {weights}"}), 400

    output_filename = f'processed_{video_file.filename}'
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    args = get_arguments()
    args.parts = parts
    args.rate = rate
    args.weights = weights
    args.input_video = input_path
    args.output_video = output_path

    progress_data = {
        "status": "processing",
        "current_frame": 0,
        "total_frames": 0,
        "output_file": output_filename
    }

    # 프레임 수 할당
    cap = cv2.VideoCapture(args.input_video)
    args.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    # 쓰레드 시작
    thread = threading.Thread(target=run_yolo_parsing, args=(args,))
    thread.start()

    # 여기서 completed로 바꾸는 코드 제거
    # 처리 완료는 run_yolo_parsing 함수 내에서만 변경

    return jsonify({'message': 'Video processing started.', 'output': output_path})

@app.route('/progress', methods=['GET'])
def progress():
    def generate():
        while True:
            yield f"data: {json.dumps(progress_data)}\n\n"
            time.sleep(1)
    return Response(generate(), mimetype="text/event-stream")


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        # 첫 번째 인자: 디렉토리, 두 번째 인자: 파일명
        return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
