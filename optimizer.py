import pandas as pd
import networkx as nx
from geopy.distance import geodesic

MAX_DISTANCE = 50  # Maximum distance in meters for connecting poles

def optimize_poles(input_csv_path, output_csv_path):
    try:
        df = pd.read_csv(input_csv_path, encoding='utf-8', header=0)
        if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
            return False

        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df = df.dropna()

        points = df[['Latitude', 'Longitude']].values.tolist()
        G = nx.Graph()
        for i, pt in enumerate(points):
            G.add_node(i, pos=pt)

        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                dist = geodesic(points[i], points[j]).meters
                if dist <= MAX_DISTANCE:
                    G.add_edge(i, j, weight=dist)

        path = nx.shortest_path(G, source=0, target=len(points)-1, weight='weight')
        optimized_points = [points[i] for i in path]
        pd.DataFrame(optimized_points, columns=['Latitude', 'Longitude']).to_csv(output_csv_path, index=False)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
