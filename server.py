from flask import Flask, request, jsonify, send_file
import os
from Yolo_Parsing_model import get_arguments, main  # Importing necessary functions

app = Flask(__name__)

UPLOAD_FOLDER = './uploads'
OUTPUT_FOLDER = './outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/process-video', methods=['POST'])
def process_video():
    """
    Process video with YOLO and human parsing based on client parameters.
    """
    # Check for required parameters
    if 'file' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    if not request.form.get('parts') or not request.form.get('rate'):
        return jsonify({'error': 'Missing required parameters (parts or rate)'}), 400

    # Save uploaded video
    video_file = request.files['file']
    input_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
    video_file.save(input_path)

    # Get parameters from request
    parts = request.form.get('parts').split(',')  # Expected as 'Head,Torso,Upper_Legs'
    rate = int(request.form.get('rate'))          # Expected as an integer
    weights = request.form.get('weights', './default_weights.pth')  # Path to model weights

    # Define output video path
    output_path = os.path.join(OUTPUT_FOLDER, f'processed_{video_file.filename}')

    # Prepare arguments for YOLO parsing
    args = get_arguments()
    args.parts = parts
    args.rate = rate
    args.weights = weights
    args.input_video = input_path
    args.output_video = output_path

    try:
        # Call the YOLO parsing process
        main(args)  # Assuming main() accepts args as a parameter
        return send_file(output_path, mimetype='video/mp4')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
