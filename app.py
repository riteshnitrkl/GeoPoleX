import os
import pandas as pd
from flask import Flask, request, jsonify, send_file
from geopy.distance import geodesic
import networkx as nx
from werkzeug.utils import secure_filename
from flask_cors import CORS  # ✅ Import CORS

app = Flask(__name__)
CORS(app)  # ✅ Enables cross-origin requests for frontend access

UPLOAD_FOLDER = os.path.abspath('uploads')  
OUTPUT_FOLDER = os.path.abspath('output')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

MAX_DISTANCE = 50  # meters

def optimize_poles(input_csv, output_csv):
    """Optimize pole placement using shortest-path algorithm."""
    try:
        print(f"🔍 Reading file: {input_csv}")

        df = pd.read_csv(input_csv, encoding='utf-8', header=0)
        print("📌 Raw Data:\n", df.head())

        # ✅ Ensure correct column names
        required_columns = ['Latitude', 'Longitude']
        if not all(col in df.columns for col in required_columns):
            print("❌ Error: CSV does not contain required columns!")
            return False
        
        # ✅ Clean data
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df = df.dropna()
        print("🛠️ Cleaned Data:\n", df.head())

        points = df[['Latitude', 'Longitude']].values.tolist()
        print("📍 Extracted Points:", points[:5])

        # ✅ Build graph with nodes representing coordinates
        G = nx.Graph()
        for i, pt in enumerate(points):
            G.add_node(i, pos=pt)

        # ✅ Connect nodes within MAX_DISTANCE
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                dist = geodesic(points[i], points[j]).meters
                if dist <= MAX_DISTANCE:
                    G.add_edge(i, j, weight=dist)

        print(f"⚡ Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

        # ✅ Find shortest path
        try:
            path = nx.shortest_path(G, source=0, target=len(points)-1, weight='weight')
            optimized_points = [points[i] for i in path]
        except nx.NetworkXNoPath:
            print("❌ No valid path found!")
            optimized_points = []

        optimized_df = pd.DataFrame(optimized_points, columns=['Latitude', 'Longitude'])
        optimized_df.to_csv(output_csv, index=False)
        print(f"✅ Optimized file saved: {output_csv}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


@app.route('/')
def index():
    return "Server is running. Go to your frontend."


@app.route('/upload', methods=['POST'])  # ✅ Fixes 405 Error
def upload_file():
    if 'file' not in request.files:
        print("❌ No file uploaded!")
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        print("❌ No file selected!")
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'optimized_output.csv')

    print(f"📂 Received file: {filename}")

    file.save(input_path)

    # ✅ Confirm file saved properly
    if not os.path.exists(input_path):
        print("❌ File was NOT saved!")
        return jsonify({'status': 'error', 'message': 'File saving failed!'}), 500

    if optimize_poles(input_path, output_path):
        return jsonify({'status': 'success', 'message': 'File processed successfully!', 'download_url': '/download'})
    else:
        return jsonify({'status': 'error', 'message': 'Optimization failed'}), 500


@app.route('/download', methods=['GET'])  # ✅ Fixes method restriction
def download_file():
    output_file_path = os.path.join(app.config['OUTPUT_FOLDER'], 'optimized_output.csv')
    if os.path.exists(output_file_path):
        return send_file(output_file_path, as_attachment=True)
    return jsonify({'status': 'error', 'message': 'File not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)
