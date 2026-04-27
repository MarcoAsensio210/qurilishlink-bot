import math


class AIRecommender:
    def __init__(self, database):
        self.db = database

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) *
             math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def recommend_supplier(self, material, buyer_lat, buyer_lon):
        # Get all products with stock > 0 and their supplier info
        all_products = self.db.get_all_products_with_supplier()

        # Filter by material
        matching = [
            p for p in all_products
            if material.lower() in p[1].lower()
        ]

        if not matching:
            return None, f"No suppliers found for '{material}' with available stock."

        # Score each matching product
        # p = (product_id, material, price, unit, stock, supplier_id, sup_name, sup_company, sup_contact, lat, lon)
        scored = []
        for p in matching:
            price = p[2]
            stock = p[4]
            lat = p[9]
            lon = p[10]

            # Calculate distance
            if lat and lon:
                distance = self.haversine(buyer_lat, buyer_lon, lat, lon)
            else:
                distance = 9999

            # Multi-factor scoring
            distance_score = 1 / (distance + 0.1)
            price_score = 1 / (price + 0.1)
            stock_score = min(stock / 1000, 1.0)  # bonus for high stock

            total_score = (distance_score * 0.5) + (price_score * 0.3) + (stock_score * 0.2)

            scored.append((total_score, distance, p))

        # Sort by score highest first
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, best_distance, best = scored[0]

        # best[5]=supplier_id, best[6]=name, best[7]=company, best[8]=contact, best[9]=lat, best[10]=lon
        supplier_info = (best[5], best[6], best[7], best[8], best[9], best[10])

        reason = (
            f"📍 Distance: {best_distance:.1f} km away\n"
            f"💵 Price: ${best[2]}/{best[3]}\n"
            f"📦 Available stock: {best[4]} {best[3]}\n"
            f"🏆 Best combined distance + price + stock score"
        )

        return supplier_info, reason

    def analyze_price(self, material, offered_price):
        all_products = self.db.get_all_products_with_supplier()
        matching = [p for p in all_products if material.lower() in p[1].lower()]

        if not matching:
            return "No price data available for comparison."

        prices = [p[2] for p in matching]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)

        if offered_price < avg_price:
            assessment = "✅ Below market average — great deal!"
        elif offered_price == avg_price:
            assessment = "➡️ Exactly at market average."
        else:
            assessment = "⚠️ Above market average — consider negotiating."

        return (
            f"📊 *Price Analysis for {material}:*\n"
            f"   Your price: ${offered_price}\n"
            f"   Market average: ${avg_price:.2f}\n"
            f"   Lowest available: ${min_price}\n"
            f"   Highest available: ${max_price}\n\n"
            f"   {assessment}"
        )