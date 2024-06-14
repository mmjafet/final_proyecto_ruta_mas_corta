from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)

# Coordenadas de las ciudades
coord = {
    'Aguascalientes': [21.87641043660486, -102.26438663286967],
    'BajaCalifornia': [32.5027, -117.00371],
    'BajaCaliforniaSur': [24.14437, -110.3005],
    'Campeche': [19.8301, -90.53491],
    'Chiapas': [16.75, -93.1167],
    'Chihuahua': [28.6353, -106.0889],
    'CDMX': [19.432713075976878, -99.13318344772986],
    'Coahuila': [25.4260, -101.0053],
    'Colima': [19.2452, -103.725],
    'Durango': [24.0277, -104.6532],
    'Guanajuato': [21.0190, -101.2574],
    'Guerrero': [17.5506, -99.5024],
    'Hidalgo': [20.1011, -98.7624],
    'Jalisco': [20.6767, -103.3475],
    'Mexico': [19.285, -99.5496],
    'Michoacan': [19.701400113725654, -101.20829680213464],
    'Morelos': [18.6813, -99.1013],
    'Nayarit': [21.5085, -104.895],
    'NuevoLeon': [25.6714, -100.309],
    'Oaxaca': [17.0732, -96.7266],
    'Puebla': [19.0414, -98.2063],
    'Queretaro': [20.5972, -100.387],
    'QuintanaRoo': [21.1631, -86.8023],
    'SanLuisPotosi': [22.1565, -100.9855],
    'Sinaloa': [24.8091, -107.394],
    'Sonora': [29.0729, -110.9559],
    'Tabasco': [17.9892, -92.9475],
    'Tamaulipas': [25.4348, -99.134],
    'Tlaxcala': [19.3181, -98.2375],
    'Veracruz': [19.1738, -96.1342],
    'Yucatan': [20.967, -89.6237],
    'Zacatecas': [22.7709, -102.5833]
}

# Calcular la distancia euclidiana entre dos puntos
def calcular_distancia(coord1, coord2):
    return ((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2) ** 0.5

# Implementar el algoritmo de Dijkstra
def dijkstra(grafo, origen, destino):
    distancias = {nodo: float('inf') for nodo in grafo}
    distancias[origen] = 0
    predecesores = {nodo: None for nodo in grafo}
    nodos_no_visitados = set(grafo)

    while nodos_no_visitados:
        # Seleccionar el nodo no visitado con la distancia mínima
        nodo_actual = min(nodos_no_visitados, key=lambda nodo: distancias[nodo])

        if distancias[nodo_actual] == float('inf'):
            break  # Todos los nodos alcanzables han sido visitados

        # Para cada vecino del nodo actual
        for vecino, peso in grafo[nodo_actual].items():
            nueva_distancia = distancias[nodo_actual] + peso
            if nueva_distancia < distancias[vecino]:
                distancias[vecino] = nueva_distancia
                predecesores[vecino] = nodo_actual

        nodos_no_visitados.remove(nodo_actual)

    # Reconstruir el camino desde el destino al origen
    camino = []
    paso_actual = destino
    while paso_actual is not None:
        camino.insert(0, paso_actual)
        paso_actual = predecesores[paso_actual]

    if distancias[destino] == float('inf'):
        return "No hay camino disponible", []
    
    return camino

# Crear el grafo como un diccionario
grafo = {ciudad: {} for ciudad in coord}

for ciudad1 in coord:
    for ciudad2 in coord:
        if ciudad1 != ciudad2:
            distancia = calcular_distancia(coord[ciudad1], coord[ciudad2])
            grafo[ciudad1][ciudad2] = distancia

# Función para encontrar nodos intermedios por latitud y longitud similares
def encontrar_nodos_intermedios(coord, origen, destino, umbral_lat, umbral_lon):
    nodos_intermedios = []
    lat_origen, lon_origen = coord[origen]
    lat_destino, lon_destino = coord[destino]
    
    for ciudad, (lat, lon) in coord.items():
        if ciudad != origen and ciudad != destino:
            # Verificar si la latitud y longitud están dentro de los umbrales
            if (min(lat_origen, lat_destino) - umbral_lat <= lat <= max(lat_origen, lat_destino) + umbral_lat and
                min(lon_origen, lon_destino) - umbral_lon <= lon <= max(lon_origen, lon_destino) + umbral_lon):
                nodos_intermedios.append(ciudad)
    
    return nodos_intermedios

@app.route('/')
def index():
    return render_template('index.html', ciudades=coord.keys())

@app.route('/get_routes', methods=['POST'])
def get_routes():
    data = request.get_json()
    origen = data['start']
    destino = data['end']
    umbral_lat = 0.0005  # Tolerancia para la latitud
    umbral_lon = 0.0005 # Tolerancia para la longitud

    if origen not in coord or destino not in coord:
        return jsonify({'error': 'Origen o destino no válidos.'}), 400

    # Encontrar los nodos intermedios
    nodos_intermedios = encontrar_nodos_intermedios(coord, origen, destino, umbral_lat, umbral_lon)

    # Ordenar los nodos intermedios para la búsqueda de camino
    nodos_intermedios.sort(key=lambda ciudad: calcular_distancia(coord[origen], coord[ciudad]))

    # Construir el camino pasando por nodos intermedios
    camino_completo = [origen]

    nodo_actual = origen
    for nodo_intermedio in nodos_intermedios:
        segmento = dijkstra(grafo, nodo_actual, nodo_intermedio)
        camino_completo.extend(segmento[1:])  # Agregar el segmento sin el primer nodo (ya está en camino_completo)
        nodo_actual = nodo_intermedio

    # Añadir el segmento final al destino
    segmento_final = dijkstra(grafo, nodo_actual, destino)
    camino_completo.extend(segmento_final[1:])

    # Convertir la ruta en coordenadas
    coordenadas_ruta = [coord[ciudad] for ciudad in camino_completo]

    # Retornar el camino y las coordenadas para la visualización en el mapa
    return jsonify({
        'camino': " -> ".join(camino_completo),
        'coordenadas_ruta': coordenadas_ruta,
        'nodos_intermedios_encontrados': nodos_intermedios
    })

if __name__ == '__main__':
    app.run(debug=True)
