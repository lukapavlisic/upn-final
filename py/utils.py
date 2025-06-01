import requests

def get_image_url(car_name):
    """
    Vrne URL slike (small) za avtomobil glede na ime znamke + model.
    """
    try:
        url = "https://api.auto-data.net/media/schema.json"
        response = requests.get(url)
        if response.status_code != 200:
            return None

        data = response.json()
        brands = data.get("brands", {}).get("brand", [])
        car_name = car_name.lower()

        for brand in brands:
            brand_name = brand.get("name", "").lower()
            models = brand.get("models", {}).get("model", [])
            for model in models:
                model_name = model.get("name", "").lower()
                full_name = f"{brand_name} {model_name}"
                if car_name in full_name:
                    generations = model.get("generations", {}).get("generation", [])
                    for gen in generations:
                        images = gen.get("images", {}).get("image", [])
                        if images:
                            return images[0].get("small")  # ali "big"
        return None
    except Exception as e:
        print("Napaka pri pridobivanju slike:", e)
        return None
