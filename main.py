@app.route('/symbols', methods=['GET'])
def symbols():
    try:
        endpoint = "/api/v1/contracts/active"
        url = API_BASE_URL + endpoint
        headers = kucoin_headers("GET", endpoint)
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        return jsonify({"error": str(e)})



