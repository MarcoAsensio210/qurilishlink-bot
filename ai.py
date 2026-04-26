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
        # Get all products with their supplier info
        all_products = self.db.get_all_products_with_supplier()

        # Filter by material
        matching = [
            p for p in all_products
            if material.lower() in p[1].lower()
        ]

        if not matching:
            return None, f"No suppliers found for '{material}'."

        # Score each matching product
        scored = []
        for p in matching:
            # p = (product_id, material, price, unit, supplier_id, sup_name, sup_company, sup_contact, lat, lon)
            price = p[2]
            lat = p[8]
            lon = p[9]

            # Calculate distance
            if lat and lon:
                distance = self.haversine(buyer_lat, buyer_lon, lat, lon)
            else:
                distance = 9999

            # Multi-factor scoring
            distance_score = 1 / (distance + 0.1)
            price_score = 1 / (price + 0.1)
            total_score = (distance_score * 0.5) + (price_score * 0.5)

            scored.append((total_score, distance, p))

        # Sort by score highest first
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, best_distance, best = scored[0]

        # best[4] = supplier_id, best[5] = name, best[6] = company, best[7] = contact
        supplier_info = (best[4], best[5], best[6], best[7], best[8], best[9])

        reason = (
            f"📍 Distance: {best_distance:.1f} km away\n"
            f"💵 Price: ${best[2]}/{best[3]}\n"
            f"🏆 Best combined distance + price score"
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