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
        suppliers = self.db.get_all_suppliers()

        # Filter by material
        matching = [s for s in suppliers if material.lower() in s[3].lower()]

        if not matching:
            return None, "No suppliers found for this material."

        # Score each supplier
        scored = []
        for s in suppliers:
            price = s[4]
            orders_completed = s[6]
            lat = s[7]
            lon = s[8]

            # Calculate distance if location available
            if lat and lon:
                distance = self.haversine(buyer_lat, buyer_lon, lat, lon)
            else:
                distance = 9999

            # Score: closer = better, cheaper = better, more orders = better
            distance_score = 1 / (distance + 0.1)
            price_score = 1 / (price + 0.1)
            order_score = orders_completed * 0.1
            total_score = (distance_score * 0.5) + (price_score * 0.3) + (order_score * 0.2)

            scored.append((total_score, distance, s))

        # Sort by score highest first
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, best_distance, best = scored[0]
        reason = (
            f"📍 Distance: {best_distance:.1f} km away\n"
            f"💵 Price: ${best[4]}/unit\n"
            f"📦 Completed orders: {best[6]}"
        )

        return best, reason

    def analyze_price(self, material, offered_price):
        suppliers = self.db.get_all_suppliers()
        matching = [s for s in suppliers if material.lower() in s[3].lower()]

        if not matching:
            return "No price data available for comparison."

        prices = [s[4] for s in matching]
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