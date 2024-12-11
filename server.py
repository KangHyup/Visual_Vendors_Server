from flask import Flask, request, jsonify, send_file, Response
import os
import time
import threading
from flask_cors import CORS
from Yolo_Parsing_model import get_arguments, main  # Importing necessary functions

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global variables for progress tracking
progress_data = {"status": "idle", "current_frame": 0, "total_frames": 0}

def run_yolo_parsing(args):
    """
    Run YOLO parsing and update progress.
    """
    global progress_data
    progress_data["status"] = "processing"
    progress_data["current_frame"] = 0
    progress_data["total_frames"] = args.frame_count

    try:
        for frame_number in main(args):  # Assuming `main` yields frame numbers
            progress_data["current_frame"] = frame_number
            time.sleep(0.1)  # Simulating frame processing time

        progress_data["status"] = "completed"
    except Exception as e:
        progress_data["status"] = "error"
        progress_data["error"] = str(e)

@app.route('/process-video', methods=['POST'])
def process_video():
    """
    Process video with YOLO and human parsing based on client parameters.
    """
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

    output_path = os.path.join(OUTPUT_FOLDER, f'processed_{video_file.filename}')

    args = get_arguments()
    args.parts = parts
    args.rate = rate
    args.weights = weights
    args.input_video = input_path
    args.output_video = output_path

    progress_data = {"status": "processing", "current_frame": 0, "total_frames": 0}

    # 진행률 업데이트 콜백 함수
    def update_progress(data):
        progress_data.update(data)

    # YOLO 파싱 실행
    thread = threading.Thread(target=main, args=(args, update_progress))
    thread.start()

    return jsonify({'message': 'Video processing started.', 'output': output_path})

@app.route('/progress', methods=['GET'])
def progress():
    """
    Stream progress updates to the client.
    """
    def generate():
        while True:
            yield f"data: {jsonify(progress_data)}\n\n"
            time.sleep(1)

    return Response(generate(), mimetype="text/event-stream")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
